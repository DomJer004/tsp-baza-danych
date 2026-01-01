import streamlit as st
import pandas as pd
import datetime
import re
import os
import time
import calendar

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="TSP Baza Danych", 
    layout="wide", 
    page_icon="⚽"
)

# ==========================================
# [NOWOŚĆ] GLOBALNE STYLE CSS (DARK MODE FIX)
# ==========================================
def apply_custom_css():
    st.markdown("""
        <style>
        /* 1. Kafelki w Kalendarzu */
        .cal-card {
            background-color: var(--secondary-background-color); /* Szary w light, Ciemny w dark */
            border: 1px solid var(--text-color);
            border-radius: 8px;
            padding: 5px;
            text-align: center;
            margin-bottom: 5px;
            color: var(--text-color);
            opacity: 0.9;
        }
        
        /* 2. Dzień dzisiejszy */
        .cal-card.today {
            border: 2px solid #28a745; /* Zielona ramka */
            background-color: rgba(40, 167, 69, 0.15); /* Półprzezroczysta zieleń - działa na czarnym i białym */
        }

        /* 3. Baner Dnia Meczowego */
        .match-banner {
            background-color: rgba(40, 167, 69, 0.2); /* Półprzezroczyste tło */
            border: 2px solid #28a745;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
            color: var(--text-color); /* Tekst dopasowuje się do trybu */
        }
        
        /* 4. Poprawa widoczności metryk */
        [data-testid="stMetricValue"] {
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_css() # <--- Uruchomienie stylów

# --- 2. ZARZĄDZANIE SESJĄ (State) ---
if 'uploader_key' not in st.session_state:
    st.session_state['uploader_key'] = 0

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- 3. LOGOWANIE ---
USERS = {
    "Djero": "TSP1995", 
    "KKowalski": "Tsp2025", 
    "PPorebski": "TSP2025", 
    "MCzerniak": "TSP2025", 
    "SJaszczurowski": "TSP2025", 
    "guest": "123456789",
    "Gabrielba": "TSP2026"
}

def login():
    st.title("🔒 Panel Logowania TSP")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Użytkownik")
        p = st.text_input("Hasło", type="password")
        if st.button("Zaloguj", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state['logged_in'] = True
                st.session_state['username'] = u
                st.rerun()
            else: st.error("Błąd logowania")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.rerun()

if not st.session_state['logged_in']:
    login()
    st.stop()

# --- GŁÓWNA APLIKACJA ---
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except: 
    HAS_PLOTLY = False

# --- MAPOWANIE KRAJÓW (BEZ ZMIAN) ---
COUNTRY_TO_ISO = {
    'polska': 'pl', 'hiszpania': 'es', 'słowacja': 'sk', 'łotwa': 'lv', 
    'chorwacja': 'hr', 'kamerun': 'cm', 'zimbabwe': 'zw', 'finlandia': 'fi', 
    'gruzja': 'ge', 'słowenia': 'si', 'ukraina': 'ua', 'holandia': 'nl', 
    'czechy': 'cz', 'białoruś': 'by', 'serbia': 'rs', 'litwa': 'lt', 
    'turcja': 'tr', 'bośnia i hercegowina': 'ba', 'japonia': 'jp', 
    'senegal': 'sn', 'bułgaria': 'bg', 'izrael': 'il', 'nigeria': 'ng', 
    'grecja': 'gr', 'francja': 'fr', 'niemcy': 'de', 'argentyna': 'ar', 
    'usa': 'us', 'stany zjednoczone': 'us', 'kolumbia': 'co', 'włochy': 'it', 
    'belgia': 'be', 'szwecja': 'se', 'portugalia': 'pt', 'węgry': 'hu', 
    'austria': 'at', 'brazylia': 'br', 'szkocja': 'gb-sct', 'anglia': 'gb-eng',
    'walia': 'gb-wls', 'irlandia': 'ie', 'irlandia północna': 'gb-nir',
    'rosja': 'ru', 'dania': 'dk', 'norwegia': 'no', 'szwajcaria': 'ch',
    'rumunia': 'ro', 'cypr': 'cy', 'macedonia': 'mk', 'czarnogóra': 'me',
    'ghana': 'gh', 'estonia': 'ee', 'haiti': 'ht', 'kanada': 'ca', 
    'wybrzeże kości słoniowej': 'ci', 'maroko': 'ma', 'tunezja': 'tn',
    'algieria': 'dz', 'egipt': 'eg', 'islandia': 'is', 'korea południowa': 'kr',
    'australia': 'au', 'urugwaj': 'uy', 'chile': 'cl', 'paragwaj': 'py',
    'kongo': 'cg', 'dr konga': 'cd', 'mali': 'ml', 'burkina faso': 'bf',
    'liberia': 'lr'
}

# --- FUNKCJE POMOCNICZE ---
def render_player_profile(player_name):
    """Funkcja wyświetlająca pełny profil zawodnika - izoluje logikę widoku."""
    
    # 1. Ładowanie danych (zakładamy, że df_uv, df_long itp. są dostępne globalnie lub wczytujemy je tu)
    # Dla bezpieczeństwa pobieramy je z cache wewnątrz funkcji
    df_uv = load_data("pilkarze.csv")
    df_long = load_data("pilkarze.csv")
    df_strzelcy = load_data("strzelcy.csv")
    df_mecze = load_data("mecze.csv")
    
    if df_uv is None or df_long is None:
        st.error("Brak danych podstawowych.")
        return

    # Przygotowanie danych unikalnych (tak jak w głównej pętli)
    if 'SUMA' in df_uv.columns:
        if isinstance(df_uv['SUMA'], pd.DataFrame): df_uv['SUMA'] = df_uv['SUMA'].iloc[:, 0]
        df_uv['SUMA'] = pd.to_numeric(df_uv['SUMA'], errors='coerce').fillna(0).astype(int)
        df_uv_sorted = df_uv.sort_values('SUMA', ascending=False).drop_duplicates(subset=['imię i nazwisko'])
    else:
        df_uv_sorted = df_uv.drop_duplicates(subset=['imię i nazwisko'])
        
    df_uv_sorted = prepare_flags(df_uv_sorted)

    # Sprawdzenie czy zawodnik istnieje
    if player_name not in df_uv_sorted['imię i nazwisko'].values:
        st.warning("Nie znaleziono danych zawodnika.")
        return

    # --- POCZĄTEK WIDOKU PROFILU ---
    
    # A. NAGŁÓWEK I DANE OSOBOWE
    row = df_uv_sorted[df_uv_sorted['imię i nazwisko'] == player_name].iloc[0]
    
    col_b = next((c for c in row.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
    age_info, is_bday = "-", False
    if col_b: 
        a, is_bday = get_age_and_birthday(row[col_b])
        if a: age_info = f"{a} lat"
    
    if is_bday: st.balloons(); st.success(f"🎉🎂 {player_name} kończy dzisiaj {age_info}! 🎂🎉")
    
    c_p1, c_p2 = st.columns([1, 3])
    with c_p1: 
        if 'Flaga' in row and pd.notna(row['Flaga']) and str(row['Flaga']) != 'nan' and str(row['Flaga']).strip() != '':
            st.image(row['Flaga'], width=100) 
        else: 
            st.markdown("## 👤")

    with c_p2:
        st.markdown(f"## {player_name}")
        st.markdown(f"**Kraj:** {row.get('Narodowość', '-')} | **Poz:** {row.get('pozycja', '-')} | **Wiek:** {age_info}")
    
    st.markdown("---")
    
    # B. STATYSTYKI SEZONOWE
    p_stats = df_long[df_long['imię i nazwisko'] == player_name].copy()
    if 'sezon' in p_stats.columns: p_stats = p_stats.sort_values('sezon')
    
    gole_l = []
    if df_strzelcy is not None:
        gm = df_strzelcy.set_index(['imię i nazwisko', 'sezon'])['gole'].to_dict()
        for _, r in p_stats.iterrows(): 
            gole_l.append(gm.get((player_name, r.get('sezon', '-')), 0))
    else: 
        gole_l = [0]*len(p_stats)
    p_stats['Gole'] = gole_l

    # Wykres (zostawiamy, jeśli chcesz mieć wykres słupkowy, jeśli nie - też możesz usunąć)
    if 'sezon' in p_stats.columns:
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            # Jeśli dane są puste, wykres się nie wyświetli lub będzie pusty, co jest ok
            if not p_stats.empty and p_stats['liczba'].sum() > 0:
                fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['liczba'], name='Mecze', marker_color='#3498db'))
                fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['Gole'], name='Gole', marker_color='#2ecc71'))
                fig.update_layout(title=f"Statystyki: {player_name}", barmode='group', height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{player_name}")
        except: pass
    
    # C. LISTA GOLI (Wersja oparta na wystepy.csv)
    # Ładujemy dane szczegółowe (jeśli cache zadziała, to będzie bardzo szybkie)
    df_det_goals = load_details("wystepy.csv")

    if df_det_goals is not None and 'Gole' in df_det_goals.columns:
        # 1. Upewniamy się, że gole są liczbami
        df_det_goals['Gole'] = pd.to_numeric(df_det_goals['Gole'], errors='coerce').fillna(0).astype(int)

        # 2. Filtrujemy: Ten zawodnik ORAZ liczba goli > 0
        goals_df = df_det_goals[
            (df_det_goals['Zawodnik_Clean'] == player_name) & 
            (df_det_goals['Gole'] > 0)
        ].copy()

        if not goals_df.empty:
            # 3. Sortowanie chronologiczne (od najnowszych)
            if 'Data_Sort' in goals_df.columns:
                goals_df = goals_df.sort_values('Data_Sort', ascending=False)

            # 4. Przygotowanie tabeli do wyświetlenia
            # Wybieramy tylko potrzebne kolumny. 
            # Uwaga: w wystepy.csv kolumna z rywalem to zazwyczaj 'Przeciwnik', a data to 'Data_Sort' (obiekt)
            cols_needed = ['Sezon', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Gole']
            
            # Sprawdzamy, czy te kolumny istnieją w pliku
            cols_final = [c for c in cols_needed if c in goals_df.columns]
            
            df_display = goals_df[cols_final].copy()
            
            # Zmieniamy nazwę 'Data_Sort' na 'Data' dla estetyki (jeśli istnieje)
            if 'Data_Sort' in df_display.columns:
                df_display.rename(columns={'Data_Sort': 'Data'}, inplace=True)

            st.markdown("**Mecze z bramkami:**")
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                key=f"goals_tab_wystepy_{player_name}",
                column_config={
                    "Data": st.column_config.DatetimeColumn(
                        "Data",
                        format="DD.MM.YYYY"  # Np. 10 marca 2023
                    ),
                    "Gole": st.column_config.NumberColumn(
                        "Gole",
                        format="%d ⚽"
                    ),
                    "Przeciwnik": st.column_config.TextColumn("Rywal")
                }
            )

    # D. SZCZEGÓŁOWA HISTORIA (z pliku wystepy.csv)
    st.markdown("---")
    st.subheader("📜 Szczegółowa historia meczowa")
    
    df_det = load_details("wystepy.csv") 
    
    if df_det is not None:
        # Filtrujemy
        if 'Zawodnik_Clean' in df_det.columns:
            player_history = df_det[df_det['Zawodnik_Clean'] == player_name].copy()
        else:
            player_history = pd.DataFrame() # Fallback

        if not player_history.empty:
            if 'Data_Sort' in player_history.columns:
                player_history = player_history.sort_values('Data_Sort', ascending=False)
            
            # --- 1. SPRAWDZAMY POZYCJĘ ---
            pos_str = str(row.get('pozycja', '')).lower().strip()
            is_goalkeeper = (pos_str == 'bramkarz')

            # --- 2. OBLICZENIA DLA BRAMKARZA (DLA KAŻDEGO WIERSZA) ---
            if is_goalkeeper:
                # Definiujemy funkcję pomocniczą do analizy pojedynczego meczu
                def analyze_gk_row(r):
                    conceded = 0
                    clean_sheet_icon = "" 
                    
                    # Parsowanie wyniku (np. "2:1")
                    w_str = str(r.get('Wynik', ''))
                    w_clean = w_str.split('(')[0].strip() # Usuwamy (k), (wo)
                    parts = re.split(r'[:\-]', w_clean)
                    
                    if len(parts) >= 2:
                        try:
                            # Zakładamy format TSP : Rywal (druga liczba to stracone)
                            conceded = int(parts[1].strip())
                        except: pass
                    
                    # Sprawdzanie Czystego Konta (Min >= 46 i Wpuszczone == 0)
                    mins = pd.to_numeric(r.get('Minuty'), errors='coerce')
                    if pd.isna(mins): mins = 0
                    
                    if mins >= 46 and conceded == 0:
                        clean_sheet_icon = "🧱"
                    elif mins > 0:
                        clean_sheet_icon = "➖" # Grał, ale wpuścił
                    else:
                        clean_sheet_icon = "" # Nie grał
                        
                    return pd.Series([conceded, clean_sheet_icon])

                # Aplikujemy funkcję do DataFrame, tworząc nowe kolumny
                player_history[['Wpuszczone', 'Czyste konto']] = player_history.apply(analyze_gk_row, axis=1)

            # --- 3. DEFINIOWANIE KOLUMN DO WYŚWIETLENIA ---
            # Baza kolumn wspólnych
            cols_base = ['Sezon', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Rola', 'Status', 'Minuty']
            cols_end = ['Żółte', 'Czerwone']

            if is_goalkeeper:
                # DLA BRAMKARZA: Wstawiamy 'Wpuszczone' i 'Czyste konto' zamiast 'Gole'
                target_cols = cols_base + ['Wpuszczone', 'Czyste konto'] + cols_end
            else:
                # DLA GRACZA Z POLA: Standardowo 'Gole'
                target_cols = cols_base + ['Gole'] + cols_end

            # Filtrujemy, żeby upewnić się, że kolumny istnieją
            cols_show = [c for c in target_cols if c in player_history.columns]

            # --- 4. RENDEROWANIE TABELI ---
            st.dataframe(
                player_history[cols_show].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
                key=f"hist_det_{player_name}", 
                column_config={
                    "Data_Sort": st.column_config.DatetimeColumn("Data", format="D MMMM YYYY, HH:mm"),
                    "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                    "Wpuszczone": st.column_config.NumberColumn("Wpuszczone", format="%d ❌"),
                    "Czyste konto": st.column_config.TextColumn("Czyste konto", help="Min. 46 min i 0 strat"),
                    "Minuty": st.column_config.NumberColumn("Minuty", format="%d'"),
                    "Żółte": st.column_config.NumberColumn("Żółte", format="%d 🟨")
                }
            )
            
            # --- 5. LICZNIKI POD TABELĄ ---
            if is_goalkeeper:
                c_d1, c_d2, c_d3, c_d4 = st.columns(4)
            else:
                c_d1, c_d2, c_d3 = st.columns(3)
            
            c_d1.metric("Łącznie minut", int(player_history['Minuty'].fillna(0).sum()))
            
            if 'Status' in player_history.columns:
                starter_cnt = len(player_history[player_history['Status'].isin(['Cały mecz', 'Zszedł', 'Czerwona kartka', 'Grał'])])
                sub_cnt = len(player_history[player_history['Status'] == 'Wszedł'])
                c_d2.metric("Pierwszy skład", starter_cnt)
                c_d3.metric("Z ławki", sub_cnt)
                
            # Licznik Czystych Kont (Sumujemy "Ptaszki" z kolumny, którą przed chwilą obliczyliśmy)
            if is_goalkeeper and 'Czyste konto' in player_history.columns:
                clean_sheets_total = len(player_history[player_history['Czyste konto'] == "🧱"])
                c_d4.metric("🧤 Czyste konta", clean_sheets_total)

        else:
            st.info("Brak szczegółowych danych historycznych.")
    else:
        st.warning("Nie wczytano pliku wystepy.csv")
    
def render_coach_profile(coach_name):
    """Generuje pełny profil trenera ze statystykami i historią."""
    
    # 1. Ładowanie danych
    df_t = load_data("trenerzy.csv")
    df_m = load_data("mecze.csv")
    
    if df_t is None: 
        st.error("Brak pliku trenerzy.csv")
        return
    
    # 2. Znalezienie trenera
    coach_row = df_t[df_t['imię i nazwisko'] == coach_name]
    if coach_row.empty:
        st.warning(f"Nie znaleziono trenera: {coach_name}")
        return
    
    coach_row = coach_row.iloc[0]

    # 3. Przetwarzanie dat (Początek - Koniec)
    def smart_date(s):
        if pd.isna(s) or str(s).strip() == '-': return pd.NaT
        # Próba parsowania
        for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%Y/%m/%d']:
            try: return pd.to_datetime(s, format=fmt)
            except: continue
        return pd.to_datetime(s, errors='coerce')

    start_date = smart_date(coach_row.get('początek'))
    end_date = smart_date(coach_row.get('koniec'))
    
    # Jeśli brak daty końcowej, zakładamy, że pracuje do dzisiaj (lub do teraz)
    is_active = False
    if pd.isna(end_date): 
        end_date = pd.Timestamp.today()
        is_active = True
    
    # 4. Pobieranie meczów dla trenera (filtrowanie po datach)
    coach_matches = pd.DataFrame()
    if df_m is not None:
        col_d = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
        if col_d:
            df_m['dt_temp'] = pd.to_datetime(df_m[col_d], dayfirst=True, errors='coerce')
            if pd.notna(start_date):
                # Filtrujemy mecze w zakresie dat
                coach_matches = df_m[
                    (df_m['dt_temp'] >= start_date) & 
                    (df_m['dt_temp'] <= end_date)
                ].sort_values('dt_temp', ascending=False)

    # --- WIDOK PROFILU ---

    # A. Nagłówek
    st.markdown(f"## 👔 {coach_name}")
    nat = coach_row.get('Narodowość', '-')
    flag_url = get_flag_url(nat)
    
    c1, c2 = st.columns([1, 4])
    with c1:
        if flag_url: st.image(flag_url, width=100)
        else: st.markdown("### 🏳️")
        
    with c2:
        # Wiek
        age_info = ""
        col_b = next((c for c in coach_row.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
        if col_b:
            age, is_bday = get_age_and_birthday(coach_row[col_b])
            if is_bday: 
                st.balloons()
                st.success(f"🎉🎂 Wszystkiego najlepszego Trenerze! ({age} lat)")
            if age: age_info = f"| **Wiek:** {age} lat"
        
        st.markdown(f"**Narodowość:** {nat} {age_info}")
        
        # Daty pracy
        s_txt = start_date.strftime('%d.%m.%Y') if pd.notna(start_date) else "?"
        e_txt = "obecnie" if is_active else (end_date.strftime('%d.%m.%Y') if pd.notna(coach_row.get('koniec')) else "?")
        st.info(f"📅 **Kadencja:** {s_txt} — {e_txt}")

    st.divider()

    # B. Statystyki i Wykresy
    if not coach_matches.empty:
        wins = 0; draws = 0; losses = 0; gf = 0; ga = 0
        
        # Obliczanie bilansu
        for _, m in coach_matches.iterrows():
            res = parse_result(m.get('wynik'))
            if res:
                gf += res[0]; ga += res[1]
                if res[0] > res[1]: wins += 1
                elif res[0] == res[1]: draws += 1
                else: losses += 1
        
        total = wins + draws + losses
        
        if total > 0:
            pts = (wins * 3) + draws
            ppg = pts / total
            
            # Kafelki ze statystykami
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Mecze", total)
            k2.metric("Z - R - P", f"{wins} - {draws} - {losses}")
            k3.metric("Średnia pkt", f"{ppg:.2f}")
            k4.metric("Bramki", f"{gf}:{ga}")
            
            # Wykres kołowy (jeśli jest Plotly)
            if HAS_PLOTLY:
                labels = ['Zwycięstwa', 'Remisy', 'Porażki']
                values = [wins, draws, losses]
                colors = ['#2ecc71', '#95a5a6', '#e74c3c'] # Zielony, Szary, Czerwony
                
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker_colors=colors)])
                fig.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0), title_text="Bilans Meczy")
                st.plotly_chart(fig, use_container_width=True)

            # C. Lista Meczów
            st.subheader("📜 Historia Meczów")
            
            display_df = coach_matches.copy()
            if 'dt_temp' in display_df.columns:
                display_df['Data'] = display_df['dt_temp']
            
            cols_needed = ['Data', 'rywal', 'wynik', 'rozgrywki', 'dom']
            final_cols = [c for c in cols_needed if c in display_df.columns]
            
            st.dataframe(
                display_df[final_cols].style.map(color_results_logic, subset=['wynik'] if 'wynik' in display_df.columns else None),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Data": st.column_config.DatetimeColumn("Data", format="DD.MM.YYYY"),
                    "dom": st.column_config.TextColumn("Gdzie?", width="small")
                }
            )
    else:
        st.info("Brak zarejestrowanych meczów w bazie dla tego trenera w podanym okresie.")
@st.cache_data
def load_details(filename="wystepy.csv"):
    if not os.path.exists(filename): 
        return None
    try:
        df = pd.read_csv(filename, sep=';')
        
        # Słownik polskich miesięcy
        PL_MONTHS = {
            'stycznia': '01', 'lutego': '02', 'marca': '03', 'kwietnia': '04',
            'maja': '05', 'czerwca': '06', 'lipca': '07', 'sierpnia': '08',
            'września': '09', 'października': '10', 'listopada': '11', 'grudnia': '12'
        }
        
        def parse_pl_date(date_str):
            if not isinstance(date_str, str): return pd.NaT
            s = date_str.lower().strip()
            
            # Zamiana miesiąca słownego na liczbę
            for pl, num in PL_MONTHS.items():
                if pl in s:
                    s = s.replace(pl, num) # "9 marca 2020 18:00" -> "9 03 2020 18:00"
                    break
            
            # Próba konwersji (ignorujemy godzinę jeśli przeszkadza, ale pandas zwykle radzi sobie)
            try:
                return pd.to_datetime(s, dayfirst=True)
            except:
                return pd.NaT

        if 'Data' in df.columns:
            # Tworzymy ukrytą kolumnę sortowania
            df['Data_Sort'] = df['Data'].apply(parse_pl_date)
            # Sortujemy OD RAZU tutaj
            df = df.sort_values('Data_Sort', ascending=False)
        
        # Reszta bez zmian
        if 'Zawodnik' in df.columns:
            df['Zawodnik_Clean'] = df['Zawodnik'].astype(str).apply(
                lambda x: re.sub(r'^\s*\(\d+\)\s*', '', x).strip()
            )
        
        if 'Data' in df.columns and 'Przeciwnik' in df.columns:
            df['Mecz_Label'] = df['Data'] + " | " + df['Gospodarz'] + " - " + df['Gość'] + " (" + df['Wynik'] + ")"
            
        return df
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None
def get_flag_url(name):
    if not isinstance(name, str): return None
    first = name.split('/')[0].strip().lower()
    code = COUNTRY_TO_ISO.get(first)
    if not code:
        for k, v in COUNTRY_TO_ISO.items():
            if k == first: code = v; break
    return f"https://flagcdn.com/w40/{code}.png" if code else None

@st.cache_data
def load_data(filename):
    try:
        df = pd.read_csv(filename)
        
        # --- AUTOMATYCZNA NAPRAWA FREKWENCJI ---
        # Usuwa spacje (np. "1 200" -> 1200) i zamienia na liczby
        if 'frekwencja' in df.columns:
            df['frekwencja'] = (
                df['frekwencja']
                .astype(str)
                .str.replace(r'\s+', '', regex=True) # Usuwa wszystkie spacje
                .str.replace(',', '') 
                .str.replace('nan', '')
            )
            # Konwersja na liczby całkowite (Int64 obsługuje puste pola)
            df['frekwencja'] = pd.to_numeric(df['frekwencja'], errors='coerce').astype('Int64')

        return df
    except FileNotFoundError:
        return None
    
    df = df.fillna("-")
    
    # Normalizacja nazw kolumn (małe litery, usuwanie spacji)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # --- LOGIKA NAPRAWCZA DLA MECZE.CSV ---
    if 'mecze.csv' in filename:
        # 1. Zmiana nazwy frekwencja -> widzów
        if 'frekwencja' in df.columns:
            df.rename(columns={'frekwencja': 'widzów'}, inplace=True)
        
        # 2. AUTOMATYCZNE WYKRYWANIE DOM/WYJAZD (Poprawione)
        place_col = next((c for c in df.columns if c in ['miejsce rozgrywania', 'miejsce', 'stadion', 'miasto']), None)
        
        if place_col:
            def is_bielsko_logic(val):
                s = str(val).lower()
                # Zmieniona logika: uwzględnia Rekord i BKS w Bielsku
                keywords = ['bielsko', 'rychlińskiego', 'startowa', 'rekord', 'bks']
                return '1' if any(k in s for k in keywords) else '0'
            
            df['dom'] = df[place_col].apply(is_bielsko_logic)
        else:
            synonyms = ['dom', 'gospodarz', 'u siebie', 'gdzie']
            if not any(col in df.columns for col in synonyms):
                df['dom'] = "-"

    # Usuwanie zduplikowanych kolumn
    df = df.loc[:, ~df.columns.duplicated()]

    cols_drop = [c for c in df.columns if 'lp' in c]
    if cols_drop: df = df.drop(columns=cols_drop)

    if 'kolejka' in df.columns:
        def format_kolejka(x):
            s = str(x).strip()
            if s.replace('.','',1).isdigit():
                try: return f"{int(float(s)):02d}"
                except: return s
            return s
        df['kolejka'] = df['kolejka'].apply(format_kolejka)
        
    if '1999/20' in df.columns:
        df.rename(columns={'1999/20': '1999/00'}, inplace=True)

    season_cols = [c for c in df.columns if re.match(r'^\d{4}/\d{2}$', c)]
    for col in season_cols:
        if df[col].dtype == object and not df[col].astype(str).str.contains('/').any(): pass 
        else: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # --- KONWERSJA LICZB (Poprawiona dla frekwencji) ---
    int_candidates = [
        'wiek', 'suma', 'liczba', 'mecze', 'gole', 'punkty', 'minuty', 'numer', 
        'asysty', 'żółte kartki', 'czerwone kartki', 'gole samobójcze', 
        'asysta 2. stopnia', 'sprokurowany karny', 'wywalczony karny', 
        'karny', 'niestrzelony karny', 'główka', 'lewa', 'prawa', 
        'czyste konta', 'obronione karne', 'kanadyjka', 'widzów'
    ]
    for col in df.columns:
        if col in int_candidates:
            try:
                # Najpierw czyszczenie stringów (usuwanie spacji, kropek tysięcznych)
                if df[col].dtype == object:
                    # Zamień '2 000' -> '2000', '1.500' -> '1500' (uwaga na kropki)
                    # Usuwamy wszystko co nie jest cyfrą, minusem
                    temp = df[col].astype(str).str.replace(r'[^\d\-]', '', regex=True)
                    # Zamiana pustych na 0
                    temp = temp.replace('', '0').replace('-', '0')
                    df[col] = pd.to_numeric(temp, errors='coerce').fillna(0).astype(int)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            except: pass
            
    return df

def prepare_flags(df, col='narodowość'):
    target_col = col
    if target_col not in df.columns:
        poss = [c for c in df.columns if c in ['kraj', 'narodowosc', 'narodowość']]
        if poss: target_col = poss[0]
    
    if target_col in df.columns:
        df['flaga'] = df[target_col].apply(get_flag_url)
        df = df.rename(columns={target_col: 'Narodowość', 'flaga': 'Flaga'})
        cols = list(df.columns)
        if 'Narodowość' in cols and 'Flaga' in cols:
            cols.remove('Flaga'); cols.insert(cols.index('Narodowość') + 1, 'Flaga')
            df = df[cols]
    return df

def parse_result(val):
    if not isinstance(val, str): return None
    
    clean_val = val.lower().replace(" ", "")
    
    # 1. SZUKANIE KARNYCH (Priorytet najwyższy)
    pen_match = re.search(r'\(?k\.?(\d+)[:\-](\d+)\)?', clean_val)
    if pen_match:
        return int(pen_match.group(1)), int(pen_match.group(2))

    # 2. CZYSZCZENIE "pd." (Po dogrywce)
    clean_val = clean_val.replace("pd.", "").replace("dogr.", "")
    clean_val = re.sub(r'\(.*?\)', '', clean_val)

    # 3. SZUKANIE STANDARDOWEGO WYNIKU
    score_match = re.search(r'(\d+)[:\-](\d+)', clean_val)
    if score_match:
        return int(score_match.group(1)), int(score_match.group(2))
        
    return None

def color_results_logic(val):
    if not isinstance(val, str): return ''
    res = parse_result(val)
    style = ''
    if res:
        t, o = res
        if t > o: style = 'color: #28a745; font-weight: bold;'
        elif t < o: style = 'color: #dc3545; font-weight: bold;'
        else: style = 'color: #fd7e14; font-weight: bold;'
    
    if any(x in val.lower() for x in ['pd', 'k.', 'wo']):
        style += ' font-style: italic; background-color: #f0f0f040;'
    return style

def parse_scorers(scorers_str):
    if not isinstance(scorers_str, str) or pd.isna(scorers_str) or scorers_str == '-': return {}
    parts = scorers_str.split(',')
    stats = {}
    current_scorer = None
    for part in parts:
        part = part.strip()
        if not part: continue
        is_own = bool(re.search(r'\(s\)|s\.|sam\.', part.lower()))
        clean_check = re.sub(r'\(k\)|k\.|\(s\)|s\.|sam\.', '', part.lower())
        has_letters = bool(re.search(r'[a-z]{2,}', clean_check))
        
        if has_letters:
            name = re.sub(r'\d+', '', part)
            name = re.sub(r'\(k\)|k\.|\(s\)|s\.|sam\.', '', name, flags=re.IGNORECASE)
            name = name.replace('(', '').replace(')', '').replace('.', '').strip()
            if name:
                current_scorer = name
                target = 'Bramka samobójcza' if is_own else current_scorer
                stats[target] = stats.get(target, 0) + 1
        else:
            if current_scorer:
                target = 'Bramka samobójcza' if is_own else current_scorer
                stats[target] = stats.get(target, 0) + 1
    return stats

def get_age_and_birthday(birth_date_val):
    if pd.isna(birth_date_val) or str(birth_date_val) in ['-', '', 'nan']: return None, False
    formats = ['%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d']
    dt = None
    for f in formats:
        try: dt = pd.to_datetime(birth_date_val, format=f); break
        except: continue
    if dt is None:
        try: dt = pd.to_datetime(birth_date_val)
        except: return None, False
    today = datetime.date.today()
    born = dt.date()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    is_birthday = (today.month == born.month) and (today.day == born.day)
    return age, is_birthday

def admin_save_csv(filename, new_data_dict):
    try:
        df = pd.read_csv(filename)
        new_row = pd.DataFrame([new_data_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(filename, index=False)
        st.cache_data.clear() 
        return True
    except Exception as e:
        st.error(f"Błąd zapisu: {e}"); return False

def get_match_icon(val):
    if pd.isna(val): return "🚌"
    s = str(val).lower().strip()
    if s in ['1', 'true', 'tak', 'dom', 'gospodarz', 'd', 'u siebie']: return "🏠"
    return "🚌"

# --- MENU ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Moduł:", ["Aktualny Sezon (25/26)", "Kalendarz", "Centrum Zawodników", "Centrum Meczowe", "Trenerzy"])
st.sidebar.divider()

# --- PANEL ADMINA (Djero) ---
if st.session_state.get('username') == 'Djero':
    st.sidebar.markdown("### 🛠️ Panel Admina (Djero)")
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    with st.sidebar.expander("📝 EDYTOR DANYCH"):
        st.info("💡 Kliknij w pusty wiersz na dole tabeli, aby dodać nowy rekord.")
        selected_file = st.selectbox("Wybierz plik do edycji:", all_files)
        
        if selected_file:
            try:
                try: df_editor = pd.read_csv(selected_file, encoding='utf-8')
                except: df_editor = pd.read_csv(selected_file, encoding='windows-1250')
                
                # --- AUTO-NAPRAWA DLA MECZE.CSV ---
                is_changed = False
                if selected_file == "mecze.csv":
                    for col in df_editor.columns:
                        if col.lower().strip() == 'frekwencja':
                            df_editor.rename(columns={col: 'Widzów'}, inplace=True)
                            is_changed = True
                            break
                    
                    synonyms_dom = ['dom', 'gospodarz', 'u siebie', 'gdzie']
                    cols_lower = [c.lower().strip() for c in df_editor.columns]
                    if not any(x in cols_lower for x in synonyms_dom):
                        df_editor['Dom'] = "-" 
                        is_changed = True

                edited_df = st.data_editor(
                    df_editor, 
                    num_rows="dynamic", 
                    key=f"editor_{selected_file}_{st.session_state['uploader_key']}", 
                    height=400
                )
                
                save_label = "💾 Zapisz zmiany"
                if is_changed: save_label += " (Auto-korekta kolumn)"
                
                if st.button(save_label, use_container_width=True):
                    try:
                        edited_df.to_csv(selected_file, index=False)
                        st.success(f"✅ Zapisano {selected_file}!")
                        st.cache_data.clear()
                        st.session_state['uploader_key'] += 1
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"Błąd zapisu: {e}")

            except Exception as e: st.error(f"Błąd pliku: {e}")

    with st.sidebar.expander("➕ SZYBKIE DODAWANIE"):
        tab_p, tab_m = st.tabs(["Piłkarz", "Mecz"])
        with tab_p:
            with st.form("add_player_form"):
                a_imie = st.text_input("Imię i Nazwisko")
                a_kraj = st.text_input("Kraj", value="Polska")
                a_poz = st.selectbox("Pozycja", ["Bramkarz", "Obrońca", "Pomocnik", "Napastnik"])
                a_data = st.date_input("Data urodzenia", min_value=datetime.date(1970,1,1))
                if st.form_submit_button("Zapisz Piłkarza"):
                    if a_imie and os.path.exists("pilkarze.csv"):
                        admin_save_csv("pilkarze.csv", {"imię i nazwisko": a_imie, "kraj": a_kraj, "pozycja": a_poz, "data urodzenia": str(a_data), "SUMA": 0})
                        st.success(f"Dodano: {a_imie}"); time.sleep(1); st.rerun()
        with tab_m:
            with st.form("add_result_form"):
                a_sezon = st.text_input("Sezon", value="2025/26")
                a_rywal = st.text_input("Rywal")
                a_wynik = st.text_input("Wynik (np. 2:1)")
                a_data_m = st.date_input("Data meczu")
                a_dom = st.selectbox("Gdzie?", ["Dom", "Wyjazd"])
                dom_val = "1" if a_dom == "Dom" else "0"
                if st.form_submit_button("Zapisz Mecz"):
                    if os.path.exists("mecze.csv"):
                        admin_save_csv("mecze.csv", {"sezon": a_sezon, "rywal": a_rywal, "wynik": a_wynik, "data meczu": str(a_data_m), "Dom": dom_val, "Widzów": 0})
                        st.success("Dodano mecz!"); time.sleep(1); st.rerun()
    st.sidebar.divider()
    # [NOWOŚĆ] SYMULACJA DATY
    with st.sidebar.expander("🕒 SYMULACJA CZASU"):
        st.info("Zmień datę, aby sprawdzić 'Dzień Meczowy' w Kalendarzu.")
        use_sim = st.checkbox("Włącz symulację daty", value=False)
        if use_sim:
            sim_date = st.date_input("Ustaw 'Dzisiaj' na:", value=datetime.date.today())
            st.session_state['simulated_today'] = sim_date
        else:
            st.session_state['simulated_today'] = None
if st.sidebar.button("Wyloguj"): logout()

# --- LOGIKA MODUŁÓW ---

if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Kadra 2025/2026")
    df = load_data("25_26.csv")
    if df is not None:
        df['is_youth'] = False
        if 'status' in df.columns:
            df['is_youth'] = df['status'].astype(str).str.contains(r'\(M\)', case=False, regex=True)
            df.loc[df['is_youth'], 'imię i nazwisko'] = "Ⓜ️ " + df.loc[df['is_youth'], 'imię i nazwisko']
        if 'gole' in df.columns and 'asysty' in df.columns: df['kanadyjka'] = df['gole'] + df['asysty']

        total_players = len(df); avg_age = f"{df['wiek'].mean():.1f}" if 'wiek' in df.columns else "-"; youth_count = df['is_youth'].sum()
        foreigners = 0; nat_col_raw = 'narodowość' if 'narodowość' in df.columns else ('kraj' if 'kraj' in df.columns else None)
        if nat_col_raw: foreigners = df[~df[nat_col_raw].str.contains('Polska', case=False, na=False)].shape[0]

        top_scorer = "-"
        if 'gole' in df.columns:
            max_g = df['gole'].max()
            if max_g > 0: best = df[df['gole'] == max_g].iloc[0]; top_scorer = f"{best['imię i nazwisko'].replace('Ⓜ️ ', '')} ({max_g})"

        df = prepare_flags(df)
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Liczba Zawodników", total_players)
        k2.metric("Średnia Wieku", avg_age)
        k3.metric("Obcokrajowcy", foreigners)
        k4.metric("Młodzieżowcy", youth_count)
        k5.metric("Najlepszy Strzelec", top_scorer)
        st.divider()

        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1: search_q = st.text_input("🔍 Szukaj:", placeholder="Nazwisko...")
        with c2: view_mode = st.selectbox("Widok:", ["Tabela Szczegółowa", "Podział na Formacje"])
        with c3: sort_by = st.selectbox("Sortuj:", ["Nr", "Wiek", "Mecze", "Gole", "Kanadyjka"], index=0)
        with c4: show_only_youth = st.checkbox("Młodzieżowcy", value=False)

        df_view = df.copy()
        if show_only_youth: df_view = df_view[df_view['is_youth']]
        if search_q: df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]
        
        sort_map = {'Nr': 'numer', 'Wiek': 'wiek', 'Mecze': 'mecze', 'Gole': 'gole', 'Kanadyjka': 'kanadyjka'}
        col_sort = sort_map.get(sort_by)
        if col_sort and col_sort in df_view.columns:
            ascending = True if col_sort in ['numer', 'wiek'] else False
            df_view = df_view.sort_values(col_sort, ascending=ascending)

        col_config = {
            "Flaga": st.column_config.ImageColumn("Kraj", width="small"),
            "mecze": st.column_config.ProgressColumn("Mecze", format="%d", min_value=0, max_value=int(df['mecze'].max()) if 'mecze' in df.columns else 35),
            "gole": st.column_config.ProgressColumn("Gole", format="%d ⚽", min_value=0, max_value=int(df['gole'].max()) if 'gole' in df.columns else 20),
            "asysty": st.column_config.ProgressColumn("Asysty", format="%d 🅰️", min_value=0, max_value=int(df['asysty'].max()) if 'asysty' in df.columns else 15),
            "kanadyjka": st.column_config.NumberColumn("Kanadyjka", format="%d 🍁"),
        }
        
        pref = ['numer', 'imię i nazwisko', 'Flaga', 'pozycja', 'wiek', 'mecze', 'minuty', 'gole', 'asysty', 'kanadyjka']
        final = [c for c in pref if c in df_view.columns]
        rest = [c for c in df_view.columns if c not in final and c not in ['narodowość', 'flaga', 'is_youth', 'status']]
        final.extend(rest)

        if view_mode == "Tabela Szczegółowa":
            df_view.index = range(1, len(df_view)+1)
            st.dataframe(df_view[final], use_container_width=True, column_config=col_config, height=(len(df_view)+1)*35+3)
        else:
            if 'pozycja' in df_view.columns:
                formacje = sorted(df_view['pozycja'].astype(str).unique())
                def get_priority(pos):
                    p = str(pos).lower()
                    if 'bramkarz' in p: return 0
                    if 'obroń' in p or 'obron' in p: return 1
                    if 'pomoc' in p: return 2
                    if 'napast' in p: return 3
                    return 10
                formacje.sort(key=get_priority)
                for f in formacje:
                    sub = df_view[df_view['pozycja'] == f]
                    if not sub.empty:
                        with st.expander(f"🟢 {f} ({len(sub)})", expanded=True):
                            sub.index = range(1, len(sub)+1)
                            st.dataframe(sub[[c for c in final if c in sub.columns]], use_container_width=True, hide_index=True, column_config=col_config)
            else: st.dataframe(df_view[final], use_container_width=True, column_config=col_config)
    else: st.error("⚠️ Brak pliku '25_26.csv'.")

# =========================================================
# MODUŁ: KALENDARZ (ZINTEGROWANY Z PROFILAMI TRENERÓW)
# =========================================================
elif opcja == "Kalendarz":
    # --- A. ZARZĄDZANIE STANEM WIDOKU (ROUTER) ---
    if 'cal_view_mode' not in st.session_state: st.session_state['cal_view_mode'] = 'list'
    if 'cal_selected_item' not in st.session_state: st.session_state['cal_selected_item'] = None

    # 1. WIDOK PROFILU ZAWODNIKA
    if st.session_state['cal_view_mode'] == 'profile':
        if st.button("⬅️ Wróć do Kalendarza"):
            st.session_state['cal_view_mode'] = 'list'
            st.rerun()
        st.divider()
        render_player_profile(st.session_state['cal_selected_item'])

    # 2. WIDOK PROFILU TRENERA (NOWOŚĆ - Wywołanie funkcji z Kroku 1)
    elif st.session_state['cal_view_mode'] == 'coach_profile':
        if st.button("⬅️ Wróć do Kalendarza"):
            st.session_state['cal_view_mode'] = 'list'
            st.rerun()
        st.divider()
        render_coach_profile(st.session_state['cal_selected_item'])

    # 3. WIDOK SZCZEGÓŁÓW MECZU
    elif st.session_state['cal_view_mode'] == 'match':
        if st.button("⬅️ Wróć do Kalendarza"):
            st.session_state['cal_view_mode'] = 'list'
            st.rerun()
        st.divider()
        
        m_data = st.session_state['cal_selected_item']
        st.markdown(f"## ⚽ Raport Meczowy: {m_data.get('Rywal', 'Rywal')}")
        st.markdown(f"📅 **Data:** {m_data.get('Data_Txt', '-')}")
        
        wynik_str = str(m_data.get('Wynik', '-'))
        if '🔜' in wynik_str:
            st.info(f"Mecz nadchodzący. {wynik_str}")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Wynik", wynik_str)
            if 'Widzów' in m_data: c2.metric("Widzów", m_data['Widzów'])
            c3.metric("Miejsce", "Dom" if str(m_data.get('Dom')) in ['1','True'] else "Wyjazd")

        if 'Strzelcy' in m_data and pd.notna(m_data['Strzelcy']) and m_data['Strzelcy'] != '-':
            st.markdown("### 🥅 Strzelcy")
            st.write(m_data['Strzelcy'])
            
        df_det = load_details("wystepy.csv")
        if df_det is not None and 'Data' in m_data:
            match_date = pd.to_datetime(m_data['Data_Obj']).date()
            if 'Data_Sort' in df_det.columns:
                squad = df_det[df_det['Data_Sort'].dt.date == match_date]
                if not squad.empty:
                    st.markdown("### 👥 Skład TSP")
                    st.dataframe(
                        squad[['Zawodnik_Clean', 'Status', 'Minuty', 'Gole']].sort_values('Minuty', ascending=False),
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.caption("Brak szczegółowego składu w bazie występów.")

    # 4. GŁÓWNY WIDOK KALENDARZA (Siatka i Tydzień)
    else:
        st.header("📅 Kalendarz Klubowy")
        
        # Symulacja daty
        if st.session_state.get('simulated_today'):
            today = st.session_state['simulated_today']
            st.warning(f"⚠️ TRYB SYMULACJI: {today.strftime('%d.%m.%Y')}")
        else:
            today = datetime.date.today()
        
        # Ładowanie danych
        df_m = load_data("mecze.csv")
        df_p = load_data("pilkarze.csv")
        df_curr = load_data("25_26.csv")
        df_t = load_data("trenerzy.csv")
        
        # --- ALERT DNIA MECZOWEGO ---
        match_today_alert = None
        if df_m is not None:
            col_date_m = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
            if col_date_m:
                df_m['dt_obj'] = pd.to_datetime(df_m[col_date_m], dayfirst=True, errors='coerce')
                # Sprawdzenie dokładnej daty (Dzień + Miesiąc + ROK)
                matches_today = df_m[df_m['dt_obj'].dt.date == today]
                if not matches_today.empty:
                    row_t = matches_today.iloc[0]
                    rival = row_t.get('rywal', 'Rywal')
                    place = "🏠 u siebie" if str(row_t.get('dom', '0')) in ['1', 'True', 'dom'] else "🚌 wyjazd"
                    match_today_alert = f"{rival} ({place})"

        if match_today_alert:
            st.markdown(f"""
            <div style="background-color: #d4edda; border: 2px solid #28a745; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h2 style="color: #155724; margin:0;">🔥 DZIEŃ MECZOWY! 🔥</h2>
                <h3 style="color: #155724; margin:5px 0;">TSP vs {match_today_alert.split('(')[0]}</h3>
                <p style="margin:0; font-weight:bold;">{match_today_alert.split('(')[1].replace(')', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            st.toast(f"⚽ Dziś mecz: {match_today_alert}!", icon="🏟️")

        # --- BUDOWANIE MAPY ZDARZEŃ ---
        events_map = {} 
        current_squad_names = [str(x).lower().strip() for x in df_curr['imię i nazwisko'].unique()] if df_curr is not None else []

        # A. Urodziny Piłkarzy
        if df_p is not None:
            df_p['id_name'] = df_p['imię i nazwisko'].astype(str).str.lower().str.strip()
            df_unique = df_p.drop_duplicates(subset=['id_name'], keep='first')
            col_b = next((c for c in df_unique.columns if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
            if col_b:
                for _, row in df_unique.iterrows():
                    try:
                        bdate = pd.to_datetime(row[col_b], errors='coerce')
                        if pd.isna(bdate): continue
                        key = (bdate.month, bdate.day)
                        name = row['imię i nazwisko']
                        is_curr = row['id_name'] in current_squad_names
                        prefix = "🟢🎂" if is_curr else "🎂"
                        age = today.year - bdate.year
                        events_map.setdefault(key, []).append({'type': 'birthday', 'label': f"{prefix} {name} ({age})", 'name': name, 'sort': 1 if is_curr else 2})
                    except: pass
        
        # B. Urodziny Trenerów
        if df_t is not None:
            col_bt = next((c for c in df_t.columns if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
            if col_bt:
                for _, row in df_t.iterrows():
                    try:
                        bdate = pd.to_datetime(row[col_bt], errors='coerce')
                        if pd.isna(bdate): continue
                        key = (bdate.month, bdate.day)
                        name = row.get('imię i nazwisko', 'Trener')
                        age = today.year - bdate.year
                        # Typ: 'coach_birthday'
                        events_map.setdefault(key, []).append({'type': 'coach_birthday', 'label': f"👔🎂 {name} ({age})", 'name': name, 'sort': 2})
                    except: pass

        # C. Mecze
        if df_m is not None and 'dt_obj' in df_m.columns:
            for _, row in df_m.dropna(subset=['dt_obj']).iterrows():
                d = row['dt_obj']; d_date = d.date(); key = (d.month, d.day)
                
                raw_score = str(row.get('wynik', ''))
                if raw_score.lower() == 'nan': raw_score = ''
                
                # Ustalanie statusu meczu
                if d_date > today: icon = "🔜"; info = "Coming Soon"; sort_prio = 0 
                elif d_date == today: icon = "🔥"; info = raw_score if raw_score else "DZIŚ"; sort_prio = 0
                else: icon = "⚽"; info = raw_score; sort_prio = 3

                rywal = row.get('rywal', 'Rywal')
                match_details = {'Rywal': rywal, 'Data_Txt': d.strftime('%d.%m.%Y'), 'Data_Obj': d, 'Wynik': f"{info}", 'Strzelcy': row.get('strzelcy', '-'), 'Widzów': row.get('widzów', '-'), 'Dom': row.get('dom', '0')}
                
                events_map.setdefault(key, []).append({'type': 'match', 'label': f"{icon} {rywal} {info}", 'match_data': match_details, 'sort': sort_prio, 'year': d.year})

        # --- WIDOK 1: TYGODNIOWY ---
        st.subheader("Ten tydzień")
        start_of_week = today - datetime.timedelta(days=today.weekday())
        cols = st.columns(7)
        days_pl = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]
        
        for i, col in enumerate(cols):
            curr_day = start_of_week + datetime.timedelta(days=i)
            is_today = (curr_day == today)
            lookup_key = (curr_day.month, curr_day.day)
            
            # Pobieranie i filtrowanie
            raw_events = events_map.get(lookup_key, [])
            day_events = []
            for ev in raw_events:
                # Mecze pokazujemy tylko z TEGO ROKU
                if ev['type'] == 'match':
                    if ev.get('year') == curr_day.year: day_events.append(ev)
                else:
                    # Urodziny zawsze
                    day_events.append(ev)
            day_events.sort(key=lambda x: (x.get('sort', 5)))
            
            with col:
                bg = "#d4edda" if is_today else "#e9ecef"; border = "#28a745" if is_today else "#dee2e6"
                st.markdown(f"<div style='background-color: {bg}; border: 2px solid {border}; border-radius: 5px; text-align: center; padding: 5px; margin-bottom: 5px;'><small>{days_pl[i]}</small><br><strong>{curr_day.strftime('%d.%m')}</strong></div>", unsafe_allow_html=True)
                
                if not day_events: st.markdown("<div style='text-align: center; opacity: 0.3; font-size: 10px;'>Brak</div>", unsafe_allow_html=True)
                
                for idx, ev in enumerate(day_events):
                    btn_key = f"ev_w_{i}_{idx}_{ev['label']}"
                    
                    # Logika Przycisków
                    if ev['type'] == 'birthday':
                        if st.button(ev['label'], key=btn_key, use_container_width=True):
                            st.session_state['cal_selected_item'] = ev['name']
                            st.session_state['cal_view_mode'] = 'profile'
                            st.rerun()
                    
                    elif ev['type'] == 'coach_birthday':
                        # PRZYCISK TRENERA -> PROFIL TRENERA
                        if st.button(ev['label'], key=btn_key, use_container_width=True):
                            st.session_state['cal_selected_item'] = ev['name']
                            st.session_state['cal_view_mode'] = 'coach_profile'
                            st.rerun()
                    
                    elif ev['type'] == 'match':
                        b_type = "primary" if "🔜" in ev['label'] or "🔥" in ev['label'] else "secondary"
                        if st.button(ev['label'], key=btn_key, type=b_type, use_container_width=True):
                            st.session_state['cal_selected_item'] = ev['match_data']
                            st.session_state['cal_view_mode'] = 'match'
                            st.rerun()

        st.divider()

        # --- WIDOK 2: MIESIĘCZNY ---
        with st.expander("📅 Pełny Kalendarz (Widok Miesięczny)", expanded=False):
            c_m1, c_m2 = st.columns(2)
            sel_year = c_m1.number_input("Rok", value=today.year, min_value=1990, max_value=2030)
            pl_months = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
            sel_month_name = c_m2.selectbox("Miesiąc", pl_months, index=today.month-1)
            sel_month = pl_months.index(sel_month_name) + 1
            
            cols_h = st.columns(7)
            for i, d in enumerate(days_pl): cols_h[i].markdown(f"**{d}**")
            
            cal_data = calendar.monthcalendar(sel_year, sel_month)
            for week in cal_data:
                cols_w = st.columns(7)
                for i, day_num in enumerate(week):
                    with cols_w[i]:
                        if day_num == 0: st.write(" ")
                        else:
                            is_today_cell = (day_num == today.day and sel_month == today.month and sel_year == today.year)
                            bg = "#d4edda" if is_today_cell else "#f8f9fa"; border = "2px solid #28a745" if is_today_cell else "1px solid #dee2e6"
                            st.markdown(f"<div style='background-color: {bg}; border: {border}; border-radius: 5px; text-align: center; padding: 2px; margin-bottom: 2px;'><strong>{day_num}</strong></div>", unsafe_allow_html=True)
                            
                            raw_events = events_map.get((sel_month, day_num), [])
                            valid_events = []
                            for ev in raw_events:
                                # Filtrowanie meczów po wybranym roku
                                if ev['type'] == 'match':
                                    if ev.get('year') == sel_year: valid_events.append(ev)
                                else: valid_events.append(ev)
                            valid_events.sort(key=lambda x: (x.get('sort', 5)))

                            for idx, ev in enumerate(valid_events):
                                btn_key = f"ev_month_{sel_year}_{sel_month}_{day_num}_{idx}_{ev['label']}"
                                
                                if ev['type'] == 'birthday':
                                    if st.button(ev['label'], key=btn_key, use_container_width=True):
                                        st.session_state['cal_selected_item'] = ev['name']
                                        st.session_state['cal_view_mode'] = 'profile'
                                        st.rerun()
                                elif ev['type'] == 'coach_birthday':
                                    if st.button(ev['label'], key=btn_key, use_container_width=True):
                                        st.session_state['cal_selected_item'] = ev['name']
                                        st.session_state['cal_view_mode'] = 'coach_profile'
                                        st.rerun()
                                elif ev['type'] == 'match':
                                    b_type = "primary" if "🔜" in ev['label'] or "🔥" in ev['label'] else "secondary"
                                    if st.button(ev['label'], key=btn_key, type=b_type, use_container_width=True):
                                        st.session_state['cal_selected_item'] = ev['match_data']
                                        st.session_state['cal_view_mode'] = 'match'
                                        st.rerun()

    st.caption("Legenda: 🔥 Dzień Meczowy | 🔜 Nadchodzące | 🟢 Kadra | 👔 Trenerzy | ⚽ Mecze (Wybrany Rok)")
elif opcja == "Centrum Zawodników":
    st.header("🏃 Centrum Zawodników TSP")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Baza Zawodników", "Strzelcy", "Klub 100", "Transfery", "Młoda Ekstraklasa"])

    with tab1:
        st.subheader("Baza Zawodników")
        
        df_long = load_data("pilkarze.csv")
        
        # 1. Ładowanie i sumowanie minut z nowego pliku (wystepy.csv)
        df_det = load_details("wystepy.csv")
        minutes_dict = {}
        
        if df_det is not None:
            minutes_dict = df_det.groupby('Zawodnik_Clean')['Minuty'].sum().to_dict()
        
        if df_long is not None:
            # 2. Ustalanie kolumny z meczami (suma)
            col_s = 'SUMA'
            if 'SUMA' not in df_long.columns:
                if 'mecze' in df_long.columns: col_s = 'mecze'
                elif 'liczba' in df_long.columns: col_s = 'liczba'
            
            # Jeśli kolumna istnieje, czyścimy ją
            if col_s in df_long.columns:
                if isinstance(df_long[col_s], pd.DataFrame): df_long[col_s] = df_long[col_s].iloc[:, 0]
                df_long[col_s] = pd.to_numeric(df_long[col_s], errors='coerce').fillna(0).astype(int)
            else:
                df_long[col_s] = 0 

            # 3. PRZYPISANIE MINUT DO GŁÓWNEJ BAZY
            df_long['Minuty'] = df_long['imię i nazwisko'].map(minutes_dict).fillna(0).astype(int)

            # 4. SORTOWANIE WSTĘPNE I USUWANIE DUPLIKATÓW
            df_uv = df_long.sort_values([col_s, 'Minuty'], ascending=[False, False]).drop_duplicates(subset=['imię i nazwisko'])

            # 5. FILTRY I SORTOWANIE (Bez paginacji)
            c1, c2, c3 = st.columns([2, 1, 1])
            
            with c1: 
                search = st.text_input("Szukaj zawodnika:", key="search_box")
            with c2: 
                # Sortowanie całej tabeli
                sort_option = st.selectbox(
                    "Sortuj wg:", 
                    ["Mecze (Najwięcej)", "Mecze (Najmniej)", "Minuty (Najwięcej)", "Nazwisko (A-Z)"],
                    index=0
                )
            with c3: 
                st.write("") 
                st.write("") 
                obcy = st.checkbox("Tylko obcokrajowcy")
            
            # Aplikowanie filtrów
            if search: 
                df_uv = df_uv[df_uv['imię i nazwisko'].astype(str).str.contains(search, case=False)]
            
            if obcy and 'narodowość' in df_uv.columns: 
                df_uv = df_uv[~df_uv['narodowość'].str.contains("Polska", na=False)]
            
            # Aplikowanie sortowania
            if sort_option == "Mecze (Najwięcej)":
                df_uv = df_uv.sort_values([col_s, 'Minuty'], ascending=[False, False])
            elif sort_option == "Mecze (Najmniej)":
                df_uv = df_uv.sort_values([col_s, 'Minuty'], ascending=[True, True])
            elif sort_option == "Minuty (Najwięcej)":
                df_uv = df_uv.sort_values(['Minuty', col_s], ascending=[False, False])
            elif sort_option == "Nazwisko (A-Z)":
                df_uv = df_uv.sort_values('imię i nazwisko', ascending=True)

            df_uv = prepare_flags(df_uv)
            
            # Licznik wyników
            st.caption(f"Znaleziono: {len(df_uv)} zawodników")

            # --- WYŚWIETLANIE CAŁEJ TABELI ---
            cols_base = ['imię i nazwisko', 'Flaga', 'Narodowość', 'pozycja', col_s, 'Minuty']
            cols_final = [c for c in cols_base if c in df_uv.columns]
            
            st.dataframe(
                df_uv[cols_final], 
                use_container_width=True, 
                hide_index=True, 
                height=500, # Ustalona wysokość z wewnętrznym scrollem (wygodne przy dużej liście)
                column_config={
                    "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                    col_s: st.column_config.NumberColumn("Mecze", format="%d 👕"), 
                    "Minuty": st.column_config.NumberColumn("Minuty", format="%d ⏱️") 
                }
            )
            
            st.divider()
            
            # 7. PROFIL ZAWODNIKA
            st.subheader("📈 Profil i Analiza")
            
            lista_zawodnikow = [""] + df_uv['imię i nazwisko'].tolist()
            wyb = st.selectbox("Wybierz zawodnika:", lista_zawodnikow)
            
            if wyb:
                render_player_profile(wyb)

    with tab2:
        st.subheader("⚽ Klasyfikacja Strzelców")
        df = load_data("strzelcy.csv")
        if df is not None:
            c1, c2 = st.columns(2)
            search_s = c1.text_input("Szukaj:", key="ss")
            sezs = c2.multiselect("Sezon:", sorted(df['sezon'].unique(), reverse=True))
            df_v = df.copy()
            if sezs: df_v = df_v[df_v['sezon'].isin(sezs)]
            if search_s: df_v = df_v[df_v['imię i nazwisko'].astype(str).str.contains(search_s, case=False)]
            grp = df_v.groupby(['imię i nazwisko', 'kraj'], as_index=False)['gole'].sum().sort_values('gole', ascending=False)
            grp = prepare_flags(grp, 'kraj')
            st.dataframe(grp[['imię i nazwisko', 'Flaga', 'Narodowość', 'gole']], use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

    with tab3:
        st.subheader("Klub 100")
        df = load_data("pilkarze.csv")
        
        if df is not None:
            # 1. Ustalamy nazwę kolumny z meczami (zazwyczaj 'suma')
            col_s = 'SUMA'
            if 'SUMA' not in df.columns:
                if 'mecze' in df.columns: col_s = 'mecze'
                elif 'liczba' in df.columns: col_s = 'liczba'
            
            if col_s in df.columns:
                # 2. Czyszczenie danych (konwersja na liczby)
                if isinstance(df[col_s], pd.DataFrame): df[col_s] = df[col_s].iloc[:, 0]
                df[col_s] = pd.to_numeric(df[col_s], errors='coerce').fillna(0).astype(int)
                
                # 3. KLUCZOWE: Najpierw sortujemy (najwięcej meczów na górze), potem usuwamy duplikaty
                # Dzięki temu dla każdego nazwiska zostaje tylko rekord z największą liczbą meczów
                k100 = df.sort_values(col_s, ascending=False).drop_duplicates(subset=['imię i nazwisko'], keep='first')
                
                # 4. Filtrujemy tylko tych, co mają 100 lub więcej meczów
                k100 = k100[k100[col_s] >= 100]
                
                # 5. Dodajemy flagi i wyświetlamy
                k100 = prepare_flags(k100)
                
                # Wybieramy tylko potrzebne kolumny do wyświetlenia
                cols_show = ['imię i nazwisko', 'Flaga', 'Narodowość', col_s]
                # Zabezpieczenie na wypadek braku którejś kolumny (np. Narodowość)
                cols_show = [c for c in cols_show if c in k100.columns]
                
                st.dataframe(
                    k100[cols_show], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                        col_s: st.column_config.NumberColumn("Liczba Meczów", format="%d 👕")
                    }
                )
            else:
                st.warning("W pliku pilkarze.csv brakuje kolumny 'SUMA' (lub 'mecze'/'liczba').")
        else:
            st.error("Nie znaleziono pliku pilkarze.csv")

    with tab4:
        st.subheader("Transfery")
        df = load_data("transfery.csv")
        if df is not None:
            df = prepare_flags(df)
            st.dataframe(df.drop(columns=['kwota pln', 'val'], errors='ignore'), use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

    with tab5:
        st.subheader("Młoda Ekstraklasa")
        df = load_data("me.csv")
        if df is not None:
            df = prepare_flags(df)
            st.dataframe(df, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

# =========================================================
# MODUŁ 6: CENTRUM MECZOWE (NAPRAWIONE)
# =========================================================
elif opcja == "Centrum Meczowe":
    st.header("⚽ Centrum Meczowe")
    
    df_m = load_data("mecze.csv")
    
    if df_m is not None:
        # --- 1. GLOBALNE PRZETWARZANIE DANYCH ---
        # To musi być tutaj, aby każda zakładka widziała te kolumny
        
        # A. Normalizacja wyniku (dla statystyk np. 1-0)
        def standardize_score(s):
            if pd.isna(s): return None
            s = str(s).strip()
            # Usuwamy przypisy w nawiasach jeśli są
            if '(' in s: s = s.split('(')[0].strip()
            return s
        
        if 'wynik' in df_m.columns:
            df_m['wynik_std'] = df_m['wynik'].apply(standardize_score)

        # B. Określenie rezultatu (Zwycięstwo/Remis/Porażka)
        def get_result_type(row):
            if pd.isna(row.get('wynik')): return None
            try:
                # Oczekujemy formatu "X-Y"
                parts = str(row['wynik']).split('-')
                if len(parts) < 2: return None
                g_tsp = int(parts[0])
                g_opp = int(parts[1])
                
                # Sprawdzamy czy TSP to gospodarz (uproszczone)
                # Zakładam, że wynik zawsze jest podawany jako TSP-Rywal w Twoim pliku
                # Jeśli wynik jest "Dom - Gość", logika musiałaby być inna.
                # Przyjmuję standard: Pierwsza liczba to TSP, druga Rywal (wg Twoich snippetów)
                
                if g_tsp > g_opp: return "Zwycięstwo"
                elif g_tsp == g_opp: return "Remis"
                else: return "Porażka"
            except: return None

        df_m['rezultat_calc'] = df_m.apply(get_result_type, axis=1)

        # C. Konwersja daty
        col_date = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
        if col_date:
            df_m['dt_obj'] = pd.to_datetime(df_m[col_date], dayfirst=True, errors='coerce')

        # --- TABS ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Analiza Rywala", "📊 Statystyki Ogólne", "📈 Forma", "📢 Frekwencja", "👥 Składy i Raporty"])
        # =========================================================
        # ZAKŁADKA 1: ANALIZA RYWALA
        # =========================================================
        with tab1:
            st.subheader("🆚 Historia spotkań z rywalem")
            
            if 'rywal' in df_m.columns:
                rivals = sorted(df_m['rywal'].dropna().unique())
                selected_rival = st.selectbox("Wybierz przeciwnika:", rivals)
                
                if selected_rival:
                    # Filtrujemy dane
                    matches_with_score = df_m[df_m['rywal'] == selected_rival].copy()
                    
                    # Sortowanie chronologiczne
                    if 'dt_obj' in matches_with_score.columns:
                        matches_with_score = matches_with_score.sort_values('dt_obj', ascending=False)

                    # PODSUMOWANIE BILANSU
                    if 'rezultat_calc' in matches_with_score.columns:
                        counts = matches_with_score['rezultat_calc'].value_counts()
                        w = counts.get("Zwycięstwo", 0)
                        d = counts.get("Remis", 0)
                        l = counts.get("Porażka", 0)
                        
                        col_a, col_b, col_c, col_d = st.columns(4)
                        col_a.metric("Mecze", len(matches_with_score))
                        col_a.info(f"Bilans: {w}Z - {d}R - {l}P") # Dodatkowy tekst pod metryką
                        
                        # Statystyki bramek
                        goals_scored = 0
                        goals_lost = 0
                        for _, row in matches_with_score.iterrows():
                            try:
                                p = str(row['wynik']).split('-')
                                goals_scored += int(p[0])
                                goals_lost += int(p[1])
                            except: pass
                        
                        col_b.metric("Bramki Strzelone", goals_scored)
                        col_c.metric("Bramki Stracone", goals_lost)
                        bilans = goals_scored - goals_lost
                        col_d.metric("Bilans Bramkowy", f"{bilans:+d}")

                    st.divider()

                    # WYKRES WYNIKÓW (Kołowy)
                    c1, c2 = st.columns([1, 2])
                    
                    with c1:
                        st.markdown("**Najczęstsze wyniki:**")
                        if 'wynik_std' in matches_with_score.columns:
                            # Naprawa błędu KeyError: wynik_std (teraz kolumna istnieje na pewno)
                            score_counts = matches_with_score['wynik_std'].value_counts().reset_index()
                            score_counts.columns = ['Wynik', 'Liczba']
                            st.dataframe(score_counts.head(5), hide_index=True, use_container_width=True)
                    
                    with c2:
                        st.markdown("**Historia spotkań:**")
                        
                        # Definiujemy kolumny do wyświetlenia
                        cols_to_show = ['data meczu', 'rozgrywki', 'wynik']
                        if 'frekwencja' in matches_with_score.columns:
                            cols_to_show.append('frekwencja')
                        
                        # Wybór kolumn (sprawdzamy czy istnieją)
                        final_cols = [c for c in cols_to_show if c in matches_with_score.columns]
                        
                        # NAPRAWA BŁĘDU KeyError w st.dataframe styling
                        # Musimy upewnić się, że 'wynik' jest w danych przekazywanych do style.map
                        if 'wynik' not in final_cols and 'wynik' in matches_with_score.columns:
                            final_cols.append('wynik')
                            
                        st.dataframe(
                            matches_with_score[final_cols].style.map(
                                color_results_logic, 
                                subset=['wynik'] if 'wynik' in final_cols else None
                            ),
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )

        # =========================================================
        # ZAKŁADKA 2: STATYSTYKI OGÓLNE
        # =========================================================
        with tab2:
            st.subheader("📊 Statystyki Historyczne")
            if 'rezultat_calc' in df_m.columns:
                res_counts = df_m['rezultat_calc'].value_counts().reset_index()
                res_counts.columns = ['Rezultat', 'Liczba']
                
                c1, c2 = st.columns(2)
                with c1:
                    if HAS_PLOTLY:
                        import plotly.express as px
                        color_map = {"Zwycięstwo": "green", "Remis": "gray", "Porażka": "red"}
                        fig = px.pie(res_counts, values='Liczba', names='Rezultat', 
                                     color='Rezultat', color_discrete_map=color_map, hole=0.4)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.bar_chart(res_counts.set_index('Rezultat'))
                
                with c2:
                    st.write("Sumarycznie:")
                    st.dataframe(res_counts, hide_index=True, use_container_width=True)

        # =========================================================
        # ZAKŁADKA 3: FORMA
        # =========================================================
        with tab3:
            st.subheader("📈 Wykres formy (Ostatnie 50 spotkań)")
            st.caption("Wykres pokazuje bramki strzelone (zielony) i stracone (czerwony) w czasie.")
            
            if 'dt_obj' in df_m.columns:
                df_form = df_m.dropna(subset=['dt_obj']).sort_values('dt_obj', ascending=True).tail(50).copy()
                
                # Parsowanie bramek
                def get_goals(row, idx):
                    try:
                        return int(str(row['wynik']).split('-')[idx])
                    except: return 0
                
                df_form['Strzelone'] = df_form.apply(lambda x: get_goals(x, 0), axis=1)
                df_form['Stracone'] = df_form.apply(lambda x: get_goals(x, 1), axis=1)
                
                if HAS_PLOTLY:
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_form['dt_obj'], y=df_form['Strzelone'], name='Strzelone', line=dict(color='green')))
                    fig.add_trace(go.Scatter(x=df_form['dt_obj'], y=df_form['Stracone'], name='Stracone', line=dict(color='red')))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(df_form[['Strzelone', 'Stracone']])

        # =========================================================
        # ZAKŁADKA 4: FREKWENCJA (Poprawiona)
        # =========================================================
        with tab4:
            st.subheader("📢 Statystyki Frekwencji")
            
            # Automatyczne wykrywanie kolumn
            col_att = next((c for c in df_m.columns if c.lower() in ['widzów', 'frekwencja', 'kibiców', 'widzow']), None)
            col_dom = next((c for c in df_m.columns if c.lower() in ['dom', 'gospodarz', 'u siebie']), None)
            col_liga = next((c for c in df_m.columns if c.lower() in ['rozgrywki', 'liga', 'turniej']), None)
            col_miejsce = next((c for c in df_m.columns if c.lower() in ['miejsce rozgrywania', 'miejsce', 'stadion']), None)
            
            if col_att and 'sezon' in df_m.columns:
                
                # 1. Logika 'U siebie'
                def check_is_home(row):
                    # Sprawdź kolumnę 'dom' jeśli istnieje
                    if col_dom and str(row[col_dom]).lower().strip() in ['1', '1.0', 'true', 'tak', 't']:
                        return True
                    # Sprawdź miejsce rozgrywania
                    if col_miejsce and pd.notna(row[col_miejsce]):
                        s = str(row[col_miejsce]).lower()
                        if any(x in s for x in ['bielsko', 'rekord', 'bks', 'rychlińskiego']): return True
                    return False

                df_m['is_home_calc'] = df_m.apply(check_is_home, axis=1)
                df_home = df_m[df_m['is_home_calc']].copy()
                
                # 2. Czyszczenie frekwencji (Usuwanie spacji i konwersja)
                df_home['att_clean'] = (
                    df_home[col_att]
                    .astype(str)
                    .str.replace(r'\s+', '', regex=True) # Usuwa wszystkie białe znaki (spacje)
                    .str.replace(',', '') 
                    .str.replace('nan', '')
                )
                df_home['att_clean'] = pd.to_numeric(df_home['att_clean'], errors='coerce').fillna(0).astype(int)
                
                df_home_valid = df_home[df_home['att_clean'] > 0].copy()

                if not df_home_valid.empty:
                    # Filtry
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        if col_liga:
                            all_comps = sorted(df_home_valid[col_liga].astype(str).unique())
                            sel_comps = st.multiselect("Rozgrywki:", all_comps, default=all_comps)
                            if sel_comps: df_home_valid = df_home_valid[df_home_valid[col_liga].isin(sel_comps)]
                    
                    with c2:
                        sel_metric = st.selectbox("Wskaźnik:", ["Średnia", "Rekord (Max)", "Suma", "Minimum"], index=0)

                    # Agregacja
                    stats = df_home_valid.groupby('sezon')['att_clean'].agg(['count', 'sum', 'mean', 'max', 'min']).reset_index()
                    stats.columns = ['Sezon', 'Mecze', 'Suma', 'Średnia', 'Max', 'Min']
                    
                    # Konwersja na int dla ładnego wyglądu
                    for c in ['Suma', 'Średnia', 'Max', 'Min']: stats[c] = stats[c].astype(int)
                    stats = stats.sort_values('Sezon')

                    # Wykres
                    if HAS_PLOTLY:
                        import plotly.express as px
                        y_col = sel_metric if sel_metric in stats.columns else "Średnia"
                        if sel_metric == "Rekord (Max)": y_col = "Max"
                        if sel_metric == "Minimum": y_col = "Min"
                        
                        fig = px.bar(stats, x='Sezon', y=y_col, text=y_col, title=f"Frekwencja: {sel_metric}")
                        fig.update_traces(textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.bar_chart(stats.set_index('Sezon'))
                    
                    with st.expander("Pokaż tabelę"):
                        st.dataframe(
                            stats.sort_values('Sezon', ascending=False), 
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Sezon": st.column_config.TextColumn("Sezon"),
                                "Średnia": st.column_config.NumberColumn(format="%d"),
                                "Suma": st.column_config.NumberColumn(format="%d")
                            }
                        )
                else:
                    st.warning("Brak danych o frekwencji (sprawdź czy są wpisani widzowie).")
            else:
                st.info("Nie znaleziono kolumny 'frekwencja' lub 'sezon'.")

        with tab5:
            st.subheader("📝 Raporty Meczowe (Składy, Minuty, Zmiany)")
            df_det = load_details("wystepy.csv")
            
            if df_det is not None:
                # 1. Wybór Sezonu
                seasons = sorted(df_det['Sezon'].unique(), reverse=True)
                sel_season = st.selectbox("Wybierz sezon:", seasons, key="squad_season")
                
                # 2. Wybór Meczu w sezonie
                matches_in_season = df_det[df_det['Sezon'] == sel_season]
                # Pobieramy unikalne etykiety meczów
                unique_matches = matches_in_season[['Mecz_Label', 'Data']].drop_duplicates().sort_values('Data', ascending=False)
                
                sel_match_lbl = st.selectbox("Wybierz mecz:", unique_matches['Mecz_Label'], key="squad_match")
                
                if sel_match_lbl:
                    # Filtrujemy wiersze dla tego konkretnego meczu
                    match_data = df_det[df_det['Mecz_Label'] == sel_match_lbl].copy()
                    
                    # Parsowanie wyniku dla nagłówka
                    try:
                        header_info = sel_match_lbl.split('|')[1].strip()
                    except: header_info = sel_match_lbl
                    
                    st.markdown(f"### {header_info}")
                    
                    # --- TUTAJ WKLEJASZ NOWY KOD ---
                    match_data['Gole'] = pd.to_numeric(match_data['Gole'], errors='coerce').fillna(0).astype(int)
                    scorers_match = match_data[match_data['Gole'] > 0].copy()
                    
                    if not scorers_match.empty:
                        st.markdown("##### ⚽ Strzelcy bramek (TSP)")
                        st.dataframe(
                            scorers_match[['Zawodnik_Clean', 'Gole', 'Minuty', 'Status']], 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "Zawodnik_Clean": st.column_config.TextColumn("Zawodnik"),
                                "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                                "Minuty": st.column_config.NumberColumn("Minuty", format="%d'"),
                                "Status": st.column_config.TextColumn("Rola")
                            }
                        )
                        st.divider()
                    # -------------------------------
                    
                    
                    col_pitch_1, col_pitch_2 = st.columns(2)
                    
                    # Podział na pierwszy skład i rezerwę
                    # Statusy w Twoim CSV to np.: 'Cały mecz', 'Zszedł', 'Wszedł', 'Czerwona kartka'
                    starters = match_data[match_data['Status'].isin(['Cały mecz', 'Zszedł', 'Czerwona kartka', 'Grał'])]
                    subs = match_data[match_data['Status'] == 'Wszedł']
                    
                    display_cols = ['Zawodnik_Clean', 'Minuty', 'Gole', 'Żółte', 'Status']
                    # Sprawdź czy kolumny Wejście/Zejście istnieją
                    if 'Wejście' in match_data.columns: display_cols.append('Wejście')
                    if 'Zejście' in match_data.columns: display_cols.append('Zejście')

                    with col_pitch_1:
                        st.info(f"🏃 Wyjściowa XI ({len(starters)})")
                        st.dataframe(starters[display_cols], hide_index=True, use_container_width=True)
                        
                    with col_pitch_2:
                        st.warning(f"🔄 Rezerwowi ({len(subs)})")
                        if not subs.empty:
                            st.dataframe(subs[display_cols], hide_index=True, use_container_width=True)
                        else:
                            st.write("Brak zmian w tym meczu.")
            else:
                st.error("Brak pliku 'wystepy.csv'. Nie można wyświetlić składów.")    
    else:
        st.error("Nie udało się załadować pliku mecze.csv")
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP")
    df = load_data("trenerzy.csv")
    if df is not None:
        def smart_date(s):
            d = pd.to_datetime(s, format='%d.%m.%Y', errors='coerce')
            if d.isna().mean() > 0.5: d = pd.to_datetime(s, errors='coerce')
            return d

        if 'początek' in df.columns: df['początek_dt'] = smart_date(df['początek'])
        if 'koniec' in df.columns: 
            df['koniec_dt'] = smart_date(df['koniec'])
            df['koniec_dt'] = df['koniec_dt'].fillna(pd.Timestamp.today())

        df = prepare_flags(df)
        t1, t2, t3, t4 = st.tabs(["Lista Trenerów", "Rankingi", "Analiza Szczegółowa", "⚔️ Porównywarka"])

        with t1:
            v = df.sort_values('początek_dt', ascending=False) if 'początek_dt' in df.columns else df
            cols = [c for c in ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'początek', 'koniec', 'mecze', 'punkty'] if c in v.columns]
            st.dataframe(v[cols], use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

        with t2:
            if 'punkty' in df.columns and 'mecze' in df.columns:
                df['punkty'] = pd.to_numeric(df['punkty'], errors='coerce').fillna(0)
                df['mecze'] = pd.to_numeric(df['mecze'], errors='coerce').fillna(0)
                st.markdown("### 🏆 Ranking")
                agg = df.groupby(['imię i nazwisko', 'Narodowość', 'Flaga'], as_index=False)[['mecze', 'punkty']].sum()
                agg['Śr. Pkt'] = (agg['punkty'] / agg['mecze']).fillna(0)
                agg = agg.sort_values('punkty', ascending=False)
                st.dataframe(agg, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small"), "Śr. Pkt": st.column_config.NumberColumn("Średnia Pkt", format="%.2f")})

        with t3:
            wybrany_trener = st.selectbox("Wybierz trenera:", sorted(df['imię i nazwisko'].unique()), key="sel_trener_adv")
            if wybrany_trener:
                coach_rows = df[df['imię i nazwisko'] == wybrany_trener]
                mecze_df = load_data("mecze.csv")
                if mecze_df is not None:
                    col_data_m = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None)
                    if col_data_m:
                        mecze_df['dt'] = pd.to_datetime(mecze_df[col_data_m], dayfirst=True, errors='coerce')
                        mask = pd.Series([False]*len(mecze_df))
                        for _, row in coach_rows.iterrows():
                            if pd.notnull(row.get('początek_dt')):
                                mask |= (mecze_df['dt'] >= row['początek_dt']) & (mecze_df['dt'] <= row['koniec_dt'])
                        
                        coach_matches = mecze_df[mask].sort_values('dt')
                        if not coach_matches.empty:
                            pts_list = []; matches_count = 0; wins = 0; draws = 0; losses = 0; gf = 0; ga = 0
                            scorers_dict = {}

                            for _, m in coach_matches.iterrows():
                                res = parse_result(m['wynik'])
                                if res:
                                    matches_count += 1; gf += res[0]; ga += res[1]
                                    if res[0]>res[1]: pts_list.append(3); wins+=1
                                    elif res[0]==res[1]: pts_list.append(1); draws+=1
                                    else: pts_list.append(0); losses+=1
                                else: pts_list.append(0)
                                if 'strzelcy' in m and pd.notnull(m['strzelcy']):
                                    for s, v in parse_scorers(m['strzelcy']).items(): scorers_dict[s] = scorers_dict.get(s, 0) + v
                            
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Mecze", matches_count)
                            c2.metric("Bilans", f"{wins}-{draws}-{losses}")
                            c3.metric("Bramki", f"{gf}:{ga}")
                            avg_pts = sum(pts_list)/len(pts_list) if pts_list else 0
                            c4.metric("Średnia pkt", f"{avg_pts:.2f}")

                            coach_matches['Punkty'] = pts_list
                            coach_matches['Forma'] = coach_matches['Punkty'].rolling(window=5, min_periods=1).mean()
                            coach_matches['Nr Meczu'] = range(1, len(coach_matches) + 1)
                            
                            if HAS_PLOTLY:
                                fig = px.line(coach_matches, x='Nr Meczu', y='Forma', markers=True, title=f"Forma: {wybrany_trener}")
                                fig.add_hline(y=avg_pts, line_dash="dot", annotation_text=f"Średnia: {avg_pts:.2f}")
                                fig.update_yaxes(range=[-0.1, 3.1])
                                st.plotly_chart(fig, use_container_width=True)

                            if scorers_dict:
                                st.markdown(f"**⚽ Strzelcy:**")
                                df_s = pd.DataFrame(list(scorers_dict.items()), columns=['Zawodnik', 'Gole']).sort_values('Gole', ascending=False)
                                st.dataframe(df_s, use_container_width=True)
                            
                            with st.expander("Lista meczów"):
                                st.dataframe(coach_matches[['data meczu', 'rywal', 'wynik']].style.map(color_results_logic, subset=['wynik']), use_container_width=True)
                        else: st.info("Brak meczów w bazie dla tego trenera.")

        with t4:
            all_coaches = sorted(df['imię i nazwisko'].unique())
            sel_compare = st.multiselect("Porównaj:", all_coaches, default=all_coaches[:2] if len(all_coaches)>1 else None)
            if sel_compare:
                comp_data = []
                mecze_df = load_data("mecze.csv")
                if mecze_df is not None:
                    col_data_m = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None)
                    if col_data_m:
                        mecze_df['dt'] = pd.to_datetime(mecze_df[col_data_m], dayfirst=True, errors='coerce')
                        for coach in sel_compare:
                            coach_rows = df[df['imię i nazwisko'] == coach]
                            mask = pd.Series([False]*len(mecze_df))
                            for _, row in coach_rows.iterrows():
                                if pd.notnull(row.get('początek_dt')):
                                    mask |= (mecze_df['dt'] >= row['początek_dt']) & (mecze_df['dt'] <= row['koniec_dt'])
                            
                            cm = mecze_df[mask]
                            if not cm.empty:
                                pts = []
                                w=0
                                for _, m in cm.iterrows():
                                    res = parse_result(m['wynik'])
                                    if res:
                                        if res[0]>res[1]: pts.append(3); w+=1
                                        elif res[0]==res[1]: pts.append(1)
                                        else: pts.append(0)
                                    else: pts.append(0)
                                avg = sum(pts)/len(pts) if pts else 0
                                comp_data.append({"Trener": coach, "Mecze": len(cm), "Śr. Pkt": avg, "% Wygranych": f"{(w/len(cm)*100):.1f}%"})
                        
                        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, column_config={"Śr. Pkt": st.column_config.NumberColumn(format="%.2f")})













