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
        /* --- MOBILE TWEAKS --- */
@media (max-width: 640px) {
    /* Zmniejszenie paddingu głównego bloku na telefonach */
    .block-container {
        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Zmniejszenie czcionki w metrykach, żeby nie ucinało liczb */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    /* Ukrywanie indeksów w tabelach na siłę, jeśli st.dataframe pominie config */
    [data-testid="stDataFrame"] th:first-child {
        display: none;
    }
    
    /* Poprawa kafelków w kalendarzu */
    .cal-card {
        font-size: 0.8rem;
        padding: 2px;
    }
    
    /* Zmniejszenie nagłówków */
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.3rem !important; }
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
                    "Data_Sort": st.column_config.DatetimeColumn("Data", format="DD.MM.YYYY, HH:mm"),
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
    """Generuje pełny profil trenera obsługujący WIELE KADENCJI."""
    
    # 1. Ładowanie danych
    df_t = load_data("trenerzy.csv")
    df_m = load_data("mecze.csv")
    
    if df_t is None: 
        st.error("Brak pliku trenerzy.csv")
        return
    
    # 2. Znalezienie WSZYSTKICH kadencji trenera
    coach_rows = df_t[df_t['imię i nazwisko'] == coach_name].copy()
    if coach_rows.empty:
        st.warning(f"Nie znaleziono trenera: {coach_name}")
        return
    
    # Pobieramy dane personalne z pierwszego wpisu
    base_info = coach_rows.iloc[0]
    
    # 3. Przetwarzanie dat dla wszystkich kadencji
    def smart_date(s):
        if pd.isna(s) or str(s).strip() == '-': return pd.NaT
        for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%Y/%m/%d']:
            try: return pd.to_datetime(s, format=fmt)
            except: continue
        return pd.to_datetime(s, errors='coerce')

    # Przygotowanie maski logicznej dla meczów (suma wszystkich okresów)
    matches_mask = pd.Series([False] * len(df_m)) if df_m is not None else pd.Series([], dtype=bool)
    
    tenure_list = []
    
    if df_m is not None:
        col_d = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
        if col_d:
            df_m['dt_temp'] = pd.to_datetime(df_m[col_d], dayfirst=True, errors='coerce')
            
            for _, row in coach_rows.iterrows():
                s_date = smart_date(row.get('początek'))
                e_date = smart_date(row.get('koniec'))
                
                is_curr = False
                if pd.isna(e_date):
                    e_date = pd.Timestamp.today() + pd.Timedelta(days=1) # Do dzisiaj (z zapasem)
                    is_curr = True
                
                # Formatowanie tekstu kadencji
                s_txt = s_date.strftime('%d.%m.%Y') if pd.notna(s_date) else "?"
                e_txt = "obecnie" if is_curr else (e_date.strftime('%d.%m.%Y') if pd.notna(row.get('koniec')) else "?")
                tenure_list.append(f"{s_txt} — {e_txt}")

                if pd.notna(s_date):
                    # Sumujemy zakresy dat (OR)
                    matches_mask |= (df_m['dt_temp'] >= s_date) & (df_m['dt_temp'] <= e_date)

    # 4. Filtrowanie meczów
    coach_matches = df_m[matches_mask].sort_values('dt_temp', ascending=False) if not matches_mask.empty else pd.DataFrame()

    # --- WIDOK PROFILU ---

    # A. Nagłówek
    st.markdown(f"## 👔 {coach_name}")
    nat = base_info.get('Narodowość', '-')
    flag_url = get_flag_url(nat)
    
    c1, c2 = st.columns([1, 4])
    with c1:
        if flag_url: st.image(flag_url, width=100)
        else: st.markdown("### 🏳️")
        
    with c2:
        # Wiek
        age_info = ""
        col_b = next((c for c in base_info.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
        if col_b:
            age, is_bday = get_age_and_birthday(base_info[col_b])
            if is_bday: 
                st.balloons()
                st.success(f"🎉🎂 Wszystkiego najlepszego Trenerze! ({age} lat)")
            if age: age_info = f"| **Wiek:** {age} lat"
        
        st.markdown(f"**Narodowość:** {nat} {age_info}")
        
        # Wyświetlanie wszystkich kadencji
        st.markdown("**Kadencje:**")
        for t in tenure_list:
            st.markdown(f"- 📅 {t}")

    st.divider()

    # B. Statystyki Zbiorcze
    if not coach_matches.empty:
        wins = 0; draws = 0; losses = 0; gf = 0; ga = 0
        
        for _, m in coach_matches.iterrows():
            res = parse_result(m.get('wynik'))
            if res:
                gf += res[0]; ga += res[1]
                if res[0] > res[1]: wins += 1
                elif res[0] == res[1]: draws += 1
                else: losses += 1
        
        total = wins + draws + losses
        pts = (wins * 3) + draws
        ppg = pts / total if total > 0 else 0
        
        # Kafelki ze statystykami
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Wszystkie Mecze", total)
        k2.metric("Bilans (Z-R-P)", f"{wins} - {draws} - {losses}")
        k3.metric("Średnia pkt", f"{ppg:.2f}")
        k4.metric("Bramki", f"{gf}:{ga}")
        
        # C. Lista Meczów
        with st.expander("📜 Pełna historia meczów (wszystkie kadencje)"):
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
        st.info("Brak zarejestrowanych meczów w bazie dla tego trenera.")
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
def format_scorers_html(scorers_str):
    """Formatuje tekst strzelców dodając ikony dla karnych i samobójów."""
    if not isinstance(scorers_str, str) or pd.isna(scorers_str) or scorers_str.strip() in ['-', '']:
        return "<span style='color: gray; font-style: italic;'>Brak bramek / Brak danych</span>"
    
    parts = scorers_str.split(',')
    html_parts = []
    
    for part in parts:
        part = part.strip()
        if not part: continue
        
        # Logika ikon
        icon = "⚽" # Domyślna piłka
        style = ""
        
        # Karne
        if '(k)' in part or 'k.' in part:
            icon = "⚽🥅 (karny)"
            part = re.sub(r'\(k\)|k\.', '', part).strip()
            style = "font-weight: bold; color: #28a745;"
            
        # Samobóje
        elif '(s)' in part or 's.' in part or 'sam.' in part:
            icon = "🔴 (sam.)"
            part = re.sub(r'\(s\)|s\.|sam\.', '', part).strip()
            style = "color: #dc3545;" # Czerwony dla samobója
            
        html_parts.append(f"<span style='{style}'>{icon} {part}</span>")
        
    return " | ".join(html_parts)
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

    # 2. WIDOK PROFILU TRENERA
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
        
        # --- PRZEŁĄCZNIK TRYBÓW ---
        c_mode1, c_mode2 = st.columns([2, 2])
        with c_mode1:
            cal_mode = st.radio("Tryb widoku:", ["Dzień w Historii (2026 + Archiwum)", "Konkretny Rocznik (Archiwum)"], horizontal=True)
        
        # Ustalanie roku bazowego
        if "Konkretny" in cal_mode:
            with c_mode2:
                target_year = st.number_input("Wybierz rok do przeglądania:", min_value=1990, max_value=2030, value=today.year)
            show_history_matches = False # Pokaż tylko mecze z target_year
        else:
            target_year = today.year # Domyślnie bieżący rok (2026)
            show_history_matches = True # Pokaż mecze z 2026 ORAZ historyczne z tego dnia
            # Ukryty input dla spójności UI (żeby layout nie skakał)
            with c_mode2:
                st.write("") 

        # Ładowanie danych
        df_m = load_data("mecze.csv")
        df_p = load_data("pilkarze.csv")
        df_curr = load_data("25_26.csv")
        df_t = load_data("trenerzy.csv")
        
        # --- ALERT DNIA MECZOWEGO (Tylko dla bieżącego roku) ---
        match_today_alert = None
        if df_m is not None:
            col_date_m = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
            if col_date_m:
                df_m['dt_obj'] = pd.to_datetime(df_m[col_date_m], dayfirst=True, errors='coerce')
                # Szukamy meczu DOKŁADNIE DZIŚ (dzień, miesiąc, rok bieżący)
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
                <p style="margin:0; font-weight:bold; color: #155724;">{match_today_alert.split('(')[1].replace(')', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            st.toast(f"⚽ Dziś mecz: {match_today_alert}!", icon="🏟️")

        # --- BUDOWANIE MAPY ZDARZEŃ ---
        events_map = {} 
        current_squad_names = [str(x).lower().strip() for x in df_curr['imię i nazwisko'].unique()] if df_curr is not None else []

        # A. Urodziny Piłkarzy (Deduplikacja + Wiek względem target_year)
        if df_p is not None:
            df_p['id_name'] = df_p['imię i nazwisko'].astype(str).str.lower().str.strip()
            df_unique = df_p.drop_duplicates(subset=['id_name'], keep='first')
            col_b = next((c for c in df_unique.columns if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
            if col_b:
                for _, row in df_unique.iterrows():
                    try:
                        bdate = pd.to_datetime(row[col_b], dayfirst=True, errors='coerce')
                        if pd.isna(bdate): continue
                        key = (bdate.month, bdate.day)
                        name = row['imię i nazwisko']
                        is_curr = row['id_name'] in current_squad_names
                        prefix = "🟢🎂" if is_curr else "🎂"
                        # Obliczamy wiek w wybranym roku
                        age = target_year - bdate.year
                        if age >= 0:
                            events_map.setdefault(key, []).append({'type': 'birthday', 'label': f"{prefix} {name} ({age})", 'name': name, 'sort': 1 if is_curr else 2})
                    except: pass
        
        # B. Urodziny Trenerów
        if df_t is not None:
            df_t['id_name'] = df_t['imię i nazwisko'].astype(str).str.lower().str.strip()
            df_t_unique = df_t.drop_duplicates(subset=['id_name'], keep='first')
            col_bt = next((c for c in df_t_unique.columns if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
            if col_bt:
                for _, row in df_t_unique.iterrows():
                    try:
                        bdate = pd.to_datetime(row[col_bt], dayfirst=True, errors='coerce')
                        if pd.isna(bdate): continue
                        key = (bdate.month, bdate.day)
                        name = row.get('imię i nazwisko', 'Trener')
                        age = target_year - bdate.year
                        if age >= 0:
                            events_map.setdefault(key, []).append({'type': 'coach_birthday', 'label': f"👔🎂 {name} ({age})", 'name': name, 'sort': 2})
                    except: pass

        # C. Mecze (Logika Hybrydowa)
        if df_m is not None and 'dt_obj' in df_m.columns:
            for _, row in df_m.dropna(subset=['dt_obj']).iterrows():
                d = row['dt_obj']; d_date = d.date(); key = (d.month, d.day)
                
                # Czy dodać ten mecz do widoku?
                should_add = False
                is_history_event = False

                if show_history_matches:
                    # Tryb Domyślny: Dodajemy jeśli rok się zgadza (Live) LUB jeśli to mecz historyczny z tego dnia
                    if d.year == target_year:
                        should_add = True
                        is_history_event = False
                    else:
                        should_add = True
                        is_history_event = True
                else:
                    # Tryb Konkretny Rocznik: Tylko mecze z tego roku
                    if d.year == target_year:
                        should_add = True
                        is_history_event = False
                
                if should_add:
                    raw_score = str(row.get('wynik', '')).strip()
                    if raw_score.lower() == 'nan': raw_score = ''
                    rywal = row.get('rywal', 'Rywal')
                    
                    if is_history_event:
                        # Stylizacja dla meczu historycznego - DODANO WYNIK
                        icon = "⚫" # Czarna kropka / Archiwum
                        sort_prio = 5 # Na samym dole
                        
                        score_part = f" {raw_score}" if raw_score else ""
                        label_str = f"{icon} {rywal}{score_part} ({d.year})"
                    else:
                        # Stylizacja dla meczu z wybranego roku (Live/Główny)
                        if d_date > today and d.year == today.year: 
                            icon = "🔜" 
                            info = raw_score if raw_score else "" 
                            sort_prio = 0 
                        elif d_date == today: 
                            icon = "🔥"
                            info = raw_score if raw_score else "DZIŚ"
                            sort_prio = 0
                        else: 
                            icon = "⚽"
                            info = raw_score
                            sort_prio = 3
                        
                        label_str = f"{icon} {rywal} {info}"

                    match_details = {'Rywal': rywal, 'Data_Txt': d.strftime('%d.%m.%Y'), 'Data_Obj': d, 'Wynik': f"{raw_score}", 'Strzelcy': row.get('strzelcy', '-'), 'Widzów': row.get('widzów', '-'), 'Dom': row.get('dom', '0')}
                    
                    events_map.setdefault(key, []).append({
                        'type': 'match', 
                        'label': label_str, 
                        'match_data': match_details, 
                        'sort': sort_prio,
                        'is_history': is_history_event # Flaga do stylizacji przycisku
                    })

        # --- WIDOK 1: TYGODNIOWY ---
        st.subheader(f"Ten tydzień ({today.strftime('%B')})")
        start_of_week = today - datetime.timedelta(days=today.weekday())
        cols = st.columns(7)
        days_pl = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]
        
        for i, col in enumerate(cols):
            curr_day = start_of_week + datetime.timedelta(days=i)
            is_today = (curr_day == today)
            # Klucz to (Miesiąc, Dzień)
            lookup_key = (curr_day.month, curr_day.day)
            
            day_events = events_map.get(lookup_key, [])
            # Sortowanie: Live Matches > Urodziny Current > Urodziny Inne > Mecze Historyczne
            day_events.sort(key=lambda x: (x.get('sort', 5)))
            
            with col:
                bg = "#d4edda" if is_today else "#e9ecef"; border = "#28a745" if is_today else "#dee2e6"
                st.markdown(f"<div style='background-color: {bg}; color: #000000; border: 2px solid {border}; border-radius: 5px; text-align: center; padding: 5px; margin-bottom: 5px;'><small>{days_pl[i]}</small><br><strong>{curr_day.strftime('%d.%m')}</strong></div>", unsafe_allow_html=True)
                
                if not day_events: st.markdown("<div style='text-align: center; opacity: 0.3; font-size: 10px;'>Brak</div>", unsafe_allow_html=True)
                
                for idx, ev in enumerate(day_events):
                    btn_key = f"ev_w_{i}_{idx}_{ev['label']}"
                    
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
                        # Styl przycisku: Historyczne na szaro (secondary), Live/Dziś na zielono (primary)
                        b_type = "secondary"
                        if not ev.get('is_history', False):
                             if "🔜" in ev['label'] or "🔥" in ev['label']: b_type = "primary"
                        
                        if st.button(ev['label'], key=btn_key, type=b_type, use_container_width=True):
                            st.session_state['cal_selected_item'] = ev['match_data']
                            st.session_state['cal_view_mode'] = 'match'
                            st.rerun()

        st.divider()

        # --- WIDOK 2: MIESIĘCZNY ---
        with st.expander(f"📅 Pełny Kalendarz - {target_year} (Widok Miesięczny)", expanded=False):
            c_m2 = st.container()
            pl_months = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
            sel_month_name = c_m2.selectbox("Miesiąc", pl_months, index=today.month-1)
            sel_month = pl_months.index(sel_month_name) + 1
            
            # W tym widoku używamy target_year do układu dni
            cols_h = st.columns(7)
            for i, d in enumerate(days_pl): cols_h[i].markdown(f"**{d}**")
            
            cal_data = calendar.monthcalendar(target_year, sel_month)
            for week in cal_data:
                cols_w = st.columns(7)
                for i, day_num in enumerate(week):
                    with cols_w[i]:
                        if day_num == 0: st.write(" ")
                        else:
                            is_today_cell = (day_num == today.day and sel_month == today.month and target_year == today.year)
                            bg = "#d4edda" if is_today_cell else "#f8f9fa"; border = "2px solid #28a745" if is_today_cell else "1px solid #dee2e6"
                            st.markdown(f"<div style='background-color: {bg}; color: #000000; border: {border}; border-radius: 5px; text-align: center; padding: 2px; margin-bottom: 2px;'><strong>{day_num}</strong></div>", unsafe_allow_html=True)
                            
                            valid_events = events_map.get((sel_month, day_num), [])
                            valid_events.sort(key=lambda x: (x.get('sort', 5)))

                            for idx, ev in enumerate(valid_events):
                                btn_key = f"ev_month_{target_year}_{sel_month}_{day_num}_{idx}_{ev['label']}"
                                
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
                                    b_type = "secondary"
                                    if not ev.get('is_history', False):
                                         if "🔜" in ev['label'] or "🔥" in ev['label']: b_type = "primary"

                                    if st.button(ev['label'], key=btn_key, type=b_type, use_container_width=True):
                                        st.session_state['cal_selected_item'] = ev['match_data']
                                        st.session_state['cal_view_mode'] = 'match'
                                        st.rerun()

    st.caption("Legenda: 🔥 Dzień Meczowy | 🔜 Nadchodzące | 🟢 Kadra | ⚫ Archiwum (inne lata)")
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
        # ZAKŁADKA 3: ARCHIWUM SPOTKAŃ (Zamiast Formy)
        # =========================================================
        with tab3:
            st.subheader("🗄️ Pełne Archiwum Spotkań")
            
            if df_m is not None:
                # Kopia do filtrowania
                df_arch = df_m.copy()
                if 'dt_obj' in df_arch.columns:
                    df_arch = df_arch.sort_values('dt_obj', ascending=False)
                
                # Filtry
                c_f1, c_f2, c_f3 = st.columns(3)
                with c_f1:
                    seasons = sorted(df_arch['sezon'].astype(str).unique(), reverse=True) if 'sezon' in df_arch.columns else []
                    sel_seas = st.multiselect("Sezon:", seasons)
                with c_f2:
                    rivals = sorted(df_arch['rywal'].astype(str).unique()) if 'rywal' in df_arch.columns else []
                    sel_riv = st.multiselect("Rywal:", rivals)
                with c_f3:
                    sel_dom = st.selectbox("Miejsce:", ["Wszystkie", "Dom", "Wyjazd"])

                # Aplikacja filtrów
                if sel_seas: df_arch = df_arch[df_arch['sezon'].isin(sel_seas)]
                if sel_riv: df_arch = df_arch[df_arch['rywal'].isin(sel_riv)]
                if sel_dom != "Wszystkie":
                    is_dom = ["1", "true", "tak", "dom"]
                    if sel_dom == "Dom":
                        df_arch = df_arch[df_arch['dom'].astype(str).str.lower().isin(is_dom)]
                    else:
                        df_arch = df_arch[~df_arch['dom'].astype(str).str.lower().isin(is_dom)]

                # Wyświetlanie
                cols_show = ['data meczu', 'sezon', 'rywal', 'wynik', 'rozgrywki', 'strzelcy', 'widzów']
                final_cols = [c for c in cols_show if c in df_arch.columns]
                
                st.dataframe(
                    df_arch[final_cols].style.map(color_results_logic, subset=['wynik'] if 'wynik' in df_arch.columns else None),
                    use_container_width=True,
                    hide_index=True,
                    height=500,
                    column_config={
                        "data meczu": st.column_config.TextColumn("Data"),
                        "strzelcy": st.column_config.TextColumn("Strzelcy", width="large"),
                        "widzów": st.column_config.NumberColumn("Frekwencja")
                    }
                )
            else:
                st.error("Brak danych w mecze.csv")

        # ... (tab4 bez zmian) ...

        # =========================================================
        # ZAKŁADKA 5: RAPORTY I SKŁADY (Nowy Layout)
        # =========================================================
        with tab5:
            st.subheader("📝 Raporty Meczowe")
            df_det = load_details("wystepy.csv")
            
            if df_det is not None:
                # 1. Wybór Meczu
                c_sel1, c_sel2 = st.columns([1, 2])
                seasons = sorted(df_det['Sezon'].unique(), reverse=True)
                sel_season = c_sel1.selectbox("Wybierz sezon:", seasons, key="sq_s")
                
                matches_in_season = df_det[df_det['Sezon'] == sel_season]
                unique_matches = matches_in_season[['Mecz_Label', 'Data_Sort']].drop_duplicates().sort_values('Data_Sort', ascending=False)
                sel_match_lbl = c_sel2.selectbox("Wybierz mecz:", unique_matches['Mecz_Label'], key="sq_m")
                
                if sel_match_lbl:
                    # Filtrujemy dane występow
                    match_squad = df_det[df_det['Mecz_Label'] == sel_match_lbl].copy()
                    
                    # Parsujemy label by wyciągnąć wynik i rywala (format: Data | Dom - Wyjazd (Wynik))
                    # Próba znalezienia tego meczu w mecze.csv aby pobrać "ładnych" strzelców
                    match_date_str = sel_match_lbl.split('|')[0].strip()
                    cols_match_info = sel_match_lbl.split('|')[1].strip() # Gospodarz - Gość (Wynik)
                    
                    # --- A. BANER WYNIKU ---
                    st.markdown("---")
                    col_res_A, col_res_B, col_res_C = st.columns([1, 2, 1])
                    with col_res_B:
                        st.markdown(f"<h3 style='text-align: center; margin-bottom:0;'>{cols_match_info}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: gray;'>{match_date_str}</p>", unsafe_allow_html=True)
                    
                    # --- B. STRZELCY (Z formatowaniem) ---
                    # Próbujemy znaleźć strzelców w mecze.csv po dacie
                    scorers_html = ""
                    if df_m is not None and 'dt_obj' in df_m.columns:
                        # Parsowanie daty z labela wystepow
                        try:
                            d_lbl = pd.to_datetime(match_date_str, dayfirst=True)
                            # Szukamy w mecze.csv (tolerancja 1 dnia na wszelki wypadek)
                            found_match = df_m[(df_m['dt_obj'] >= d_lbl - pd.Timedelta(days=1)) & (df_m['dt_obj'] <= d_lbl + pd.Timedelta(days=1))]
                            if not found_match.empty and 'strzelcy' in found_match.columns:
                                raw_scorers = found_match.iloc[0]['strzelcy']
                                scorers_html = format_scorers_html(raw_scorers)
                        except: pass
                    
                    if scorers_html:
                        st.markdown(f"<div style='background-color: rgba(40, 167, 69, 0.1); padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;'>{scorers_html}</div>", unsafe_allow_html=True)

                    # --- C. SKŁADY (Podział na kolumny) ---
                    match_squad['Gole'] = pd.to_numeric(match_squad['Gole'], errors='coerce').fillna(0).astype(int)
                    
                    # Definicje grup
                    starters = match_squad[match_squad['Status'].isin(['Cały mecz', 'Zszedł', 'Czerwona kartka', 'Grał'])]
                    subs = match_squad[match_squad['Status'] == 'Wszedł']
                    unused = match_squad[match_squad['Status'] == 'Ławka'] # Opcjonalnie jeśli masz taki status

                    # Konfiguracja kolumn tabeli
                    cfg_squad = {
                        "Zawodnik_Clean": st.column_config.TextColumn("Zawodnik", width="medium"),
                        "Minuty": st.column_config.NumberColumn("Min", format="%d'"),
                        "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                        "Żółte": st.column_config.NumberColumn("Kartki", format="%d 🟨"),
                        "Status": st.column_config.TextColumn("Status")
                    }
                    show_cols = ['Zawodnik_Clean', 'Minuty', 'Gole', 'Żółte', 'Status']

                    c_pitch, c_bench = st.columns([1, 1])
                    
                    with c_pitch:
                        st.markdown("### 🏟️ Wyjściowa XI")
                        if not starters.empty:
                            st.dataframe(starters[show_cols], hide_index=True, use_container_width=True, column_config=cfg_squad)
                        else: st.info("Brak danych o pierwszym składzie.")

                    with c_bench:
                        st.markdown("### 🔄 Rezerwowi")
                        if not subs.empty:
                            st.dataframe(subs[show_cols], hide_index=True, use_container_width=True, column_config=cfg_squad)
                        else:
                            st.caption("Brak zmian lub brak danych.")
                            
            else:
                st.error("Brak pliku wystepy.csv")
elif opcja == "Trenerzy":
    # --- A. ZARZĄDZANIE STANEM WIDOKU ---
    if 'coach_view_mode' not in st.session_state: st.session_state['coach_view_mode'] = 'list'
    if 'selected_coach' not in st.session_state: st.session_state['selected_coach'] = None

    # --- B. WIDOK PROFILU TRENERA (SZCZEGÓŁOWY) ---
    if st.session_state['coach_view_mode'] == 'profile':
        if st.button("⬅️ Wróć do listy trenerów"):
            st.session_state['coach_view_mode'] = 'list'
            st.session_state['selected_coach'] = None
            st.rerun()
        
        # Wywołanie funkcji profilu (tej z obsługą wielu kadencji)
        render_coach_profile(st.session_state['selected_coach'])

    # --- C. WIDOK GŁÓWNY (LISTA, RANKINGI, PORÓWNANIE) ---
    else:
        st.header("👔 Centrum Trenerów TSP")
        
        df = load_data("trenerzy.csv")
        if df is not None:
            # Przetwarzanie dat (potrzebne do sortowania listy)
            def smart_date(s):
                d = pd.to_datetime(s, format='%d.%m.%Y', errors='coerce')
                if d.isna().mean() > 0.5: d = pd.to_datetime(s, errors='coerce')
                return d

            if 'początek' in df.columns: df['początek_dt'] = smart_date(df['początek'])
            df = prepare_flags(df)

            # --- 1. WYSZUKIWARKA / PRZEJŚCIE DO PROFILU ---
            col_search, col_space = st.columns([1, 2])
            with col_search:
                all_coaches = sorted(df['imię i nazwisko'].unique())
                # Selectbox działa jako nawigacja
                selected_from_list = st.selectbox("🔍 Znajdź profil trenera:", [""] + all_coaches)
                
                if selected_from_list:
                    st.session_state['selected_coach'] = selected_from_list
                    st.session_state['coach_view_mode'] = 'profile'
                    st.rerun()

            st.divider()

            # --- 2. ZAKŁADKI (Usunąłem starą "Analizę", bo teraz jest Profil) ---
            t1, t2, t3 = st.tabs(["📜 Lista Trenerów", "🏆 Rankingi", "⚔️ Porównywarka"])

            # ZAKŁADKA 1: LISTA
            with t1:
                # Wyświetlamy unikalną listę trenerów (bez duplikatów kadencji dla czytelności listy głównej)
                # lub pełną listę - zależnie od preferencji. Tutaj pełna lista posortowana od najnowszej.
                v = df.sort_values('początek_dt', ascending=False) if 'początek_dt' in df.columns else df
                cols = [c for c in ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'początek', 'koniec', 'mecze', 'punkty'] if c in v.columns]
                
                st.dataframe(
                    v[cols], 
                    use_container_width=True, 
                    hide_index=True, 
                    column_config={
                        "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                        "mecze": st.column_config.NumberColumn("M"),
                        "punkty": st.column_config.NumberColumn("Pkt")
                    }
                )

            # ZAKŁADKA 2: RANKINGI
            with t2:
                if 'punkty' in df.columns and 'mecze' in df.columns:
                    # Kopia do obliczeń
                    df_rank = df.copy()
                    df_rank['punkty'] = pd.to_numeric(df_rank['punkty'], errors='coerce').fillna(0)
                    df_rank['mecze'] = pd.to_numeric(df_rank['mecze'], errors='coerce').fillna(0)
                    
                    st.markdown("### 📊 Tabela Wszechczasów")
                    # Grupujemy po imieniu, sumując statystyki ze wszystkich kadencji
                    agg = df_rank.groupby(['imię i nazwisko', 'Narodowość', 'Flaga'], as_index=False)[['mecze', 'punkty']].sum()
                    
                    # Obliczamy średnią
                    agg['Śr. Pkt'] = (agg['punkty'] / agg['mecze']).fillna(0)
                    
                    # Sortowanie
                    sort_metric = st.radio("Sortuj według:", ["Punkty (Suma)", "Mecze (Suma)", "Średnia Punktów"], horizontal=True)
                    
                    if "Średnia" in sort_metric:
                        # Filtr: minimum 5 meczów, żeby średnia była miarodajna
                        agg = agg[agg['mecze'] >= 5].sort_values('Śr. Pkt', ascending=False)
                        st.caption("*Dla średniej punktów uwzględniono trenerów z min. 5 meczami.*")
                    elif "Mecze" in sort_metric:
                        agg = agg.sort_values('mecze', ascending=False)
                    else:
                        agg = agg.sort_values('punkty', ascending=False)

                    st.dataframe(
                        agg, 
                        use_container_width=True, 
                        hide_index=True, 
                        column_config={
                            "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                            "Śr. Pkt": st.column_config.NumberColumn("Średnia Pkt", format="%.2f ⭐"),
                            "mecze": st.column_config.NumberColumn("Mecze", format="%d 🏟️"),
                            "punkty": st.column_config.NumberColumn("Punkty", format="%d 📈")
                        }
                    )

            # ZAKŁADKA 3: PORÓWNYWARKA
            with t3:
                st.markdown("### 🆚 Porównanie Trenerów")
                all_coaches = sorted(df['imię i nazwisko'].unique())
                sel_compare = st.multiselect("Wybierz trenerów do porównania:", all_coaches, default=all_coaches[:2] if len(all_coaches)>1 else None)
                
                if sel_compare:
                    comp_data = []
                    mecze_df = load_data("mecze.csv")
                    
                    if mecze_df is not None:
                        col_data_m = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None)
                        if col_data_m:
                            mecze_df['dt'] = pd.to_datetime(mecze_df[col_data_m], dayfirst=True, errors='coerce')
                            
                            for coach in sel_compare:
                                # Pobieramy wszystkie kadencje tego trenera
                                coach_rows = df[df['imię i nazwisko'] == coach]
                                
                                # Tworzymy maskę meczów dla wszystkich kadencji
                                mask = pd.Series([False]*len(mecze_df))
                                for _, row in coach_rows.iterrows():
                                    s_date = smart_date(row.get('początek'))
                                    e_date = smart_date(row.get('koniec'))
                                    if pd.isna(e_date): e_date = pd.Timestamp.today() + pd.Timedelta(days=1)
                                    
                                    if pd.notna(s_date):
                                        mask |= (mecze_df['dt'] >= s_date) & (mecze_df['dt'] <= e_date)
                                
                                cm = mecze_df[mask]
                                
                                if not cm.empty:
                                    pts = []
                                    w = 0; d = 0; l = 0; gf = 0; ga = 0
                                    
                                    for _, m in cm.iterrows():
                                        res = parse_result(m.get('wynik'))
                                        if res:
                                            gf += res[0]; ga += res[1]
                                            if res[0] > res[1]: pts.append(3); w+=1
                                            elif res[0] == res[1]: pts.append(1); d+=1
                                            else: pts.append(0); l+=1
                                        else: pts.append(0)
                                    
                                    avg = sum(pts)/len(pts) if pts else 0
                                    win_rate = (w/len(cm)*100) if len(cm) > 0 else 0
                                    
                                    comp_data.append({
                                        "Trener": coach,
                                        "Mecze": len(cm),
                                        "Śr. Pkt": avg,
                                        "Zwycięstwa": w,
                                        "Remisy": d,
                                        "Porażki": l,
                                        "Bramki": f"{gf}:{ga}",
                                        "% Wygranych": win_rate
                                    })
                            
                            if comp_data:
                                df_comp = pd.DataFrame(comp_data).set_index("Trener")
                                
                                # Formatowanie tabeli
                                st.dataframe(
                                    df_comp.style.format({
                                        "Śr. Pkt": "{:.2f}",
                                        "% Wygranych": "{:.1f}%"
                                    }).background_gradient(cmap="Greens", subset=["Śr. Pkt", "% Wygranych"]),
                                    use_container_width=True
                                )
                                
                                # Wykres porównawczy
                                if HAS_PLOTLY:
                                    fig = go.Figure(data=[
                                        go.Bar(name='Śr. Pkt', x=df_comp.index, y=df_comp['Śr. Pkt'], marker_color='#2ecc71'),
                                        go.Bar(name='% Wygranych', x=df_comp.index, y=df_comp['% Wygranych']/33, marker_color='#3498db', visible='legendonly') # Skalowane dla wizualizacji
                                    ])
                                    fig.update_layout(title="Porównanie punktowania", barmode='group')
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("Brak meczów w bazie dla wybranych trenerów.")
        else:
            st.error("Brak pliku 'trenerzy.csv'.")
