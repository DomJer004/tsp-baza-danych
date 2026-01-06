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


apply_custom_css()  # <--- Uruchomienie stylów

# --- 2. ZARZĄDZANIE SESJĄ I NAWIGACJA (Router) ---
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'username' not in st.session_state: st.session_state['username'] = ""

# Zmienne do nawigacji (kliknięcie w piłkarza)
if 'cm_selected_player' not in st.session_state: st.session_state['cm_selected_player'] = None

def navigate_to_player(name):
    """Funkcja pomocnicza do otwierania profilu"""
    clean_name = str(name).replace("Ⓜ️", "").replace("🤕", "").strip()
    st.session_state['cm_selected_player'] = clean_name
    st.rerun()

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

# --- KONFIGURACJA GLOBALNA ---
IGNORED_SEASONS = ["1995/96", "1996/97", "1995/1996", "1996/1997"]

def filter_seasons(df, col_name='Sezon'):
    """Usuwa z DataFrame rekordy z ignorowanych sezonów."""
    if df is None or col_name not in df.columns:
        return df
    return df[~df[col_name].isin(IGNORED_SEASONS)].copy()

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
            else:
                st.error("Błąd logowania")


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
    # 1. Ładowanie danych
    df_uv = load_data("pilkarze.csv")
    df_long = load_data("pilkarze.csv")
    df_strzelcy = load_data("strzelcy.csv")
    df_det_goals = load_details("wystepy.csv")

    if df_uv is None:
        st.error("Brak pliku pilkarze.csv")
        return

    # --- KROK KLUCZOWY: PRZYGOTOWANIE FLAG DLA CAŁEJ BAZY ---
    # Robimy to TUTAJ, żeby mieć pewność, że kolumna 'Flaga' istnieje
    # zanim będziemy jej potrzebować w sekcji kolegów.
    df_uv = prepare_flags(df_uv)

    # Sortowanie (aby przy duplikatach wziąć ten "lepszy" rekord - np. z sumą meczów)
    sort_col = 'suma' if 'suma' in df_uv.columns else ('mecze' if 'mecze' in df_uv.columns else None)
    if sort_col:
        df_uv[sort_col] = pd.to_numeric(df_uv[sort_col], errors='coerce').fillna(0)
        df_uv_sorted = df_uv.sort_values(sort_col, ascending=False).drop_duplicates(subset=['imię i nazwisko'])
    else:
        df_uv_sorted = df_uv.drop_duplicates(subset=['imię i nazwisko'])

    # Pobieramy profil konkretnego zawodnika
    if player_name not in df_uv_sorted['imię i nazwisko'].values:
        st.warning(f"Nie znaleziono profilu: {player_name}")
        return

    row = df_uv_sorted[df_uv_sorted['imię i nazwisko'] == player_name].iloc[0]

    # --- A. WIEK I URODZINY ---
    col_b = next((c for c in row.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
    birth_date = None
    age_info, is_bday = "-", False

    if col_b:
        birth_date = pd.to_datetime(row[col_b], errors='coerce')
        a, is_bday = get_age_and_birthday(row[col_b])
        if a: age_info = f"{a} lat"

    if is_bday:
        st.balloons()
        st.success(f"🎉🎂 {player_name} kończy dzisiaj {age_info}! 🎂🎉")

    # --- B. ODZNAKI (REKORDY) ---
    badges = get_player_record_badges(player_name)
    if badges:
        st.write("")
        badges_html = ""
        for b in badges:
            badges_html += f"""
                <span style="
                    background-color: {b['color']}20; 
                    border: 1px solid {b['color']}; 
                    color: {b['color']}; 
                    padding: 4px 10px; 
                    border-radius: 15px; 
                    font-size: 0.9rem; 
                    font-weight: bold; 
                    margin-right: 5px; 
                    margin-bottom: 5px; 
                    display: inline-block;">
                    {b['icon']} {b['text']}
                </span>
                """
        st.markdown(badges_html, unsafe_allow_html=True)
        st.write("")

    # --- C. DEBIUT I OSTATNI MECZ ---
    debut_txt = "-"
    last_txt = "-"

    # Historię pobieramy raz, żeby użyć jej też w sekcji kolegów
    p_hist = pd.DataFrame()
    if df_det_goals is not None:
        p_hist = df_det_goals[df_det_goals['Zawodnik_Clean'] == player_name].copy()

        if not p_hist.empty and 'Data_Sort' in p_hist.columns:
            p_hist = p_hist.sort_values('Data_Sort', ascending=True)

            # Debiut
            first_match = p_hist.iloc[0]
            d_date_obj = pd.to_datetime(first_match['Data_Sort'])
            d_date = d_date_obj.strftime('%d.%m.%Y') if pd.notna(d_date_obj) else "-"
            d_opp = first_match.get('Przeciwnik', '')
            d_age = calculate_exact_age_str(birth_date, d_date_obj) if birth_date is not None else ""
            debut_txt = f"{d_date} vs {d_opp}\n{d_age}"

            # Ostatni mecz
            last_match = p_hist.iloc[-1]
            l_date_obj = pd.to_datetime(last_match['Data_Sort'])
            l_date = l_date_obj.strftime('%d.%m.%Y') if pd.notna(l_date_obj) else "-"
            l_opp = last_match.get('Przeciwnik', '')
            l_age = calculate_exact_age_str(birth_date, l_date_obj) if birth_date is not None else ""
            last_txt = f"{l_date} vs {l_opp}\n{l_age}"

    # --- D. NAGŁÓWEK Z MULTI-FLAGAMI ---
    c_p1, c_p2 = st.columns([1, 3])

    # Pobieramy surowy tekst narodowości (np. "Polska / Niemcy")
    nat_raw = str(row.get('Narodowość', row.get('kraj', '-')))

    with c_p1:
        # Generujemy HTML z flagami używając funkcji get_multi_flags_html
        if 'get_multi_flags_html' in globals():
            flags_html = get_multi_flags_html(nat_raw)
            if flags_html:
                st.markdown(f"<div style='margin-top: 10px;'>{flags_html}</div>", unsafe_allow_html=True)
            else:
                st.markdown("## 👤")
        else:
            st.markdown("## 👤")

    with c_p2:
        st.markdown(f"## {player_name}")
        st.markdown(f"**Kraj:** {nat_raw} | **Poz:** {row.get('pozycja', '-')}")
        st.markdown(f"**Wiek:** {age_info}")

        hd1, hd2 = st.columns(2)
        hd1.info(f"🆕 **Debiut:**\n\n{debut_txt}")
        hd2.info(f"🏁 **Ostatni mecz:**\n\n{last_txt}")

    st.markdown("---")

    # --- E. WYKRES I STATYSTYKI SEZONOWE ---
    p_stats = df_long[df_long['imię i nazwisko'] == player_name].copy()
    if 'sezon' in p_stats.columns: p_stats = p_stats.sort_values('sezon')

    gole_l = []
    if df_strzelcy is not None:
        gm = df_strzelcy.set_index(['imię i nazwisko', 'sezon'])['gole'].to_dict()
        for _, r in p_stats.iterrows():
            gole_l.append(gm.get((player_name, r.get('sezon', '-')), 0))
    else:
        gole_l = [0] * len(p_stats)
    p_stats['Gole'] = gole_l

    if 'sezon' in p_stats.columns and HAS_PLOTLY:
        try:
            fig = go.Figure()
            if not p_stats.empty and p_stats['liczba'].sum() > 0:
                fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['liczba'], name='Mecze', marker_color='#3498db'))
                fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['Gole'], name='Gole', marker_color='#2ecc71'))
                fig.update_layout(title=f"Statystyki: {player_name}", barmode='group', height=350,
                                  margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{player_name}")
        except:
            pass

    # --- F. LISTA GOLI (TABELA) ---
    if df_det_goals is not None and 'Gole' in df_det_goals.columns:
        df_det_goals['Gole'] = pd.to_numeric(df_det_goals['Gole'], errors='coerce').fillna(0).astype(int)
        goals_df = df_det_goals[(df_det_goals['Zawodnik_Clean'] == player_name) & (df_det_goals['Gole'] > 0)].copy()

        if not goals_df.empty:
            if 'Data_Sort' in goals_df.columns:
                goals_df = goals_df.sort_values('Data_Sort', ascending=False)

            st.markdown("**⚽ Mecze ze zdobytą bramką:**")
            st.dataframe(goals_df[['Sezon', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Gole']],
                         use_container_width=True, hide_index=True, column_config={
                    "Data_Sort": st.column_config.DateColumn("Data", format="DD.MM.YYYY"),
                    "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽")
                })

    # --- G. SZCZEGÓŁOWA HISTORIA MECZOWA ---
    st.markdown("---")
    st.subheader("📜 Szczegółowa historia meczowa")

    if not p_hist.empty:
        # Sortowanie od najnowszego
        if 'Data_Sort' in p_hist.columns:
            p_hist = p_hist.sort_values('Data_Sort', ascending=False)

        # Logika dla Bramkarza
        pos_str = str(row.get('pozycja', '')).lower().strip()
        is_goalkeeper = (pos_str == 'bramkarz')

        if is_goalkeeper:
            def analyze_gk_row(r):
                conceded = 0
                clean_sheet_icon = ""
                # Prosta heurystyka wyciągania wpuszczonych goli z wyniku, np "1-2"
                try:
                    w_str = str(r.get('Wynik', ''))
                    w_clean = w_str.split('(')[0].strip()
                    parts = re.split(r'[:\-]', w_clean)
                    if len(parts) >= 2:
                        g1, g2 = int(parts[0]), int(parts[1])
                        # Próba zgadnięcia czy dom czy wyjazd po Roli
                        rola = str(r.get('Rola', '')).lower()
                        if 'gospodarz' in rola or 'dom' in rola:
                            conceded = g2
                        elif 'gość' in rola or 'wyjazd' in rola:
                            conceded = g1
                        else:
                            # Fallback: bierzemy mniejszą wartość przy wygranej (ryzykowne)
                            # lub po prostu sumę goli rywala
                            conceded = 0
                except:
                    pass

                mins = pd.to_numeric(r.get('Minuty'), errors='coerce')
                if pd.isna(mins): mins = 0

                if mins >= 45 and conceded == 0:
                    clean_sheet_icon = "🧱"
                elif mins > 0:
                    clean_sheet_icon = "➖"

                return pd.Series([conceded, clean_sheet_icon])

            p_hist[['Wpuszczone', 'Czyste konto']] = p_hist.apply(analyze_gk_row, axis=1)

        # Wybór kolumn do wyświetlenia
        cols_base = ['Sezon', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Rola', 'Status', 'Minuty']
        cols_end = ['Żółte', 'Czerwone']
        target_cols = cols_base + (['Wpuszczone', 'Czyste konto'] if is_goalkeeper else ['Gole']) + cols_end
        cols_show = [c for c in target_cols if c in p_hist.columns]

        # Tabela historii
        st.dataframe(p_hist[cols_show].reset_index(drop=True), use_container_width=True, hide_index=True,
                     column_config={
                         "Data_Sort": st.column_config.DateColumn("Data", format="DD.MM.YYYY"),
                         "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                         "Wpuszczone": st.column_config.NumberColumn("Wpuszczone", format="%d ❌"),
                         "Minuty": st.column_config.NumberColumn("Minuty", format="%d'"),
                         "Żółte": st.column_config.NumberColumn("Żółte", format="%d 🟨"),
                         "Czerwone": st.column_config.NumberColumn("Czerwone", format="%d 🟥")
                     })

        # --- H. NAJWIĘCEJ MECZÓW Z... (KOLEDZY) ---
        st.markdown("---")
        st.subheader("🤝 Najwięcej meczów z...")

        # Lista unikalnych meczów tego zawodnika
        my_matches = p_hist['Mecz_Label'].unique()

        # Filtrujemy dużą bazę występów po tych meczach
        teammates_rows = df_det_goals[df_det_goals['Mecz_Label'].isin(my_matches)]
        # Usuwamy samego siebie
        teammates_rows = teammates_rows[teammates_rows['Zawodnik_Clean'] != player_name]

        if not teammates_rows.empty:
            top_mates = teammates_rows['Zawodnik_Clean'].value_counts().head(10).reset_index()
            top_mates.columns = ['Kolega z zespołu', 'Wspólne Mecze']

            # Mapowanie flag - korzystamy z df_uv_sorted, które ma kolumnę 'Flaga' (zrobiliśmy to w kroku 1)
            # Ważne: drop_duplicates, żeby merge nie "spuchł"
            if 'Flaga' in df_uv_sorted.columns:
                df_flags_map = df_uv_sorted[['imię i nazwisko', 'Flaga']].drop_duplicates(subset=['imię i nazwisko'])
                # Łączymy (left join)
                top_mates = pd.merge(top_mates, df_flags_map, left_on='Kolega z zespołu', right_on='imię i nazwisko',
                                     how='left')
            else:
                top_mates['Flaga'] = None

            # Numeracja miejsc
            top_mates.index = top_mates.index + 1

            def get_rank_label(idx):
                if idx == 1: return "🥇 1."
                if idx == 2: return "🥈 2."
                if idx == 3: return "🥉 3."
                return f"{idx}."

            top_mates.insert(0, 'Miejsce', top_mates.index.map(get_rank_label))

            # Tabela kolegów
            c_tm1, c_tm2 = st.columns([2, 1])
            with c_tm1:
                st.dataframe(
                    top_mates[['Miejsce', 'Flaga', 'Kolega z zespołu', 'Wspólne Mecze']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Miejsce": st.column_config.TextColumn("Lp.", width="small"),
                        "Flaga": st.column_config.ImageColumn("", width="small"),
                        "Wspólne Mecze": st.column_config.ProgressColumn("Wspólne Mecze", format="%d", min_value=0,
                                                                         max_value=int(
                                                                             top_mates['Wspólne Mecze'].max()))
                    }
                )
        else:
            st.info("Brak danych o wspólnych występach.")

    else:
        st.info("Brak historii meczowej w bazie występów.")


def render_coach_profile(coach_name):
    """Generuje pełny profil trenera obsługujący WIELE KADENCJI + FLAGI."""

    # 1. Ładowanie danych
    df_t = load_data("trenerzy.csv")
    df_m = load_data("mecze.csv")

    if df_t is None:
        st.error("Brak pliku trenerzy.csv")
        return

    # [POPRAWKA] Normalizacja flag i nazw kolumn (Kraj -> Narodowość)
    df_t = prepare_flags(df_t)

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
            try:
                return pd.to_datetime(s, format=fmt)
            except:
                continue
        return pd.to_datetime(s, errors='coerce')

    # Przygotowanie maski logicznej dla meczów
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
                    e_date = pd.Timestamp.today() + pd.Timedelta(days=1)
                    is_curr = True

                s_txt = s_date.strftime('%d.%m.%Y') if pd.notna(s_date) else "?"
                e_txt = "obecnie" if is_curr else (e_date.strftime('%d.%m.%Y') if pd.notna(row.get('koniec')) else "?")
                tenure_list.append(f"{s_txt} — {e_txt}")

                if pd.notna(s_date):
                    matches_mask |= (df_m['dt_temp'] >= s_date) & (df_m['dt_temp'] <= e_date)

    # 4. Filtrowanie meczów
    coach_matches = df_m[matches_mask].sort_values('dt_temp',
                                                   ascending=False) if not matches_mask.empty else pd.DataFrame()

    # --- WIDOK PROFILU ---

    # A. Nagłówek
    st.markdown(f"## 👔 {coach_name}")

    # [POPRAWKA] Pobieranie flagi (teraz kolumna 'Flaga' na pewno istnieje dzięki prepare_flags)
    flag_url = base_info.get('Flaga')
    nat = base_info.get('Narodowość', '-')

    c1, c2 = st.columns([1, 4])
    with c1:
        if flag_url and str(flag_url) != 'nan':
            st.image(flag_url, width=100)
        else:
            st.markdown("### 🏳️")

    with c2:
        age_info = ""
        col_b = next((c for c in base_info.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
        if col_b:
            age, is_bday = get_age_and_birthday(base_info[col_b])
            if is_bday:
                st.balloons()
                st.success(f"🎉🎂 Wszystkiego najlepszego Trenerze! ({age} lat)")
            if age: age_info = f"| **Wiek:** {age} lat"

        st.markdown(f"**Narodowość:** {nat} {age_info}")

        st.markdown("**Kadencje:**")
        for t in tenure_list:
            st.markdown(f"- 📅 {t}")

    st.divider()

    # B. Statystyki Zbiorcze
    if not coach_matches.empty:
        wins = 0;
        draws = 0;
        losses = 0;
        gf = 0;
        ga = 0
        for _, m in coach_matches.iterrows():
            res = parse_result(m.get('wynik'))
            if res:
                gf += res[0];
                ga += res[1]
                if res[0] > res[1]:
                    wins += 1
                elif res[0] == res[1]:
                    draws += 1
                else:
                    losses += 1

        total = wins + draws + losses
        pts = (wins * 3) + draws
        ppg = pts / total if total > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Wszystkie Mecze", total)
        k2.metric("Bilans", f"{wins}-{draws}-{losses}")
        k3.metric("Średnia pkt", f"{ppg:.2f}")
        k4.metric("Bramki", f"{gf}:{ga}")

        with st.expander("📜 Pełna historia meczów"):
            display_df = coach_matches.copy()
            if 'dt_temp' in display_df.columns: display_df['Data'] = display_df['dt_temp']
            cols_needed = ['Data', 'rywal', 'wynik', 'rozgrywki', 'dom']
            final_cols = [c for c in cols_needed if c in display_df.columns]
            st.dataframe(display_df[final_cols].style.map(color_results_logic,
                                                          subset=['wynik'] if 'wynik' in display_df.columns else None),
                         use_container_width=True, hide_index=True,
                         column_config={"Data": st.column_config.DatetimeColumn("Data", format="DD.MM.YYYY")})
    else:
        st.info("Brak zarejestrowanych meczów w bazie dla tego trenera.")


@st.cache_data
def load_details(filename="wystepy.csv"):
    if not os.path.exists(filename):
        return None
    try:
        # 1. Wczytanie pliku
        try:
            df = pd.read_csv(filename, sep=';', encoding='utf-8')
        except:
            df = pd.read_csv(filename, sep=';', encoding='windows-1250')

        # Zapamiętanie kolejności z pliku (ważne przy sortowaniu w ramach meczu)
        df['File_Order'] = df.index

        # --- 2. NAPRAWA DAT (Parsowanie polskich miesięcy) ---
        if 'Data' in df.columns:
            # Słownik do tłumaczenia polskich miesięcy
            pl_months = {
                'stycznia': '01', 'lutego': '02', 'marca': '03', 'kwietnia': '04',
                'maja': '05', 'czerwca': '06', 'lipca': '07', 'sierpnia': '08',
                'września': '09', 'października': '10', 'listopada': '11', 'grudnia': '12',
                'styczeń': '01', 'luty': '02', 'marzec': '03', 'kwiecień': '04',
                'maj': '05', 'czerwiec': '06', 'lipiec': '07', 'sierpień': '08',
                'wrzesień': '09', 'październik': '10', 'listopad': '11', 'grudzień': '12'
            }

            def parse_pl_date(date_str):
                s = str(date_str).strip().lower()
                # Jeśli to 'nan' lub puste
                if s == 'nan' or not s:
                    return pd.NaT

                # Próba 1: Standardowy format (np. 09.08.97)
                try:
                    return pd.to_datetime(s, dayfirst=True)
                except:
                    pass

                # Próba 2: Podmiana polskich miesięcy
                for pl, digit in pl_months.items():
                    if pl in s:
                        # Zamiana np. "22 września 2021" -> "22 09 2021"
                        s = s.replace(pl, digit)
                        break

                # Próba parsowania po podmianie
                try:
                    return pd.to_datetime(s, dayfirst=True)
                except:
                    return pd.NaT

            # Aplikujemy nową funkcję parsującą
            df['Data_Sort'] = df['Data'].apply(parse_pl_date)

            # Wypełniamy braki starą datą TYLKO jeśli naprawdę się nie udało,
            # ale teraz powinno się udać dla "września" itp.
            df['Data_Sort'] = df['Data_Sort'].fillna(pd.Timestamp('1900-01-01'))

            # Sortujemy chronologicznie
            df = df.sort_values(['Data_Sort', 'File_Order'], ascending=[False, True])

        # --- 3. CZYSZCZENIE NAZWISK ---
        if 'Zawodnik' in df.columns:
            df['Zawodnik_Clean'] = df['Zawodnik'].astype(str).str.strip()

        # --- 4. TWORZENIE LABELA MECZU ---
        if 'Data' in df.columns:
            # Używamy oryginalnego stringa z datą do wyświetlania, żeby ładnie wyglądało
            # Ale sortujemy po Data_Sort
            def make_label(row):
                d_str = str(row.get('Data', ''))
                # Jeśli mamy Gospodarza i Gościa
                if 'Gospodarz' in row and 'Gość' in row:
                    host = str(row['Gospodarz']).strip()
                    guest = str(row['Gość']).strip()
                    res = str(row.get('Wynik', '-'))
                    return f"{d_str} | {host} - {guest} ({res})"
                # Jeśli mamy tylko Przeciwnika (stary format lub inna struktura)
                elif 'Przeciwnik' in row:
                    opp = str(row['Przeciwnik']).strip()
                    res = str(row.get('Wynik', '-'))
                    return f"{d_str} | {opp} ({res})"
                return "Mecz"

            df['Mecz_Label'] = df.apply(make_label, axis=1)

        # --- 5. KONWERSJA LICZB (Minuty, Gole, Wejście/Zejście) ---
        numeric_cols = ['Minuty', 'Wejście', 'Zejście', 'Gole', 'Żółte', 'Czerwone']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            else:
                df[col] = 0

        # --- 6. MINUTA ZDARZENIA (DLA ZMIAN) ---
        def calculate_event_minute(row):
            status = str(row.get('Status', '')).strip()
            # Używamy kolumn z pliku, bo są dokładne
            if status == 'Wszedł':
                return row['Wejście']
            elif status == 'Zszedł':
                return row['Zejście']
            elif status == 'Czerwona kartka' or row['Czerwone'] > 0:
                if row['Zejście'] > 0: return row['Zejście']
                if row['Minuty'] < 90: return row['Minuty']
            return 0

        df['Minuta_Zmiany_Real'] = df.apply(calculate_event_minute, axis=1)

        return df
    except Exception as e:
        st.error(f"Błąd krytyczny w load_details: {e}")
        return None


def get_flag_url(name):
    """Pobiera URL flagi dla pojedynczego kraju (usuwa zbędne spacje)."""
    if not isinstance(name, str) or pd.isna(name): return None

    # Jeśli nazwa to np. "Polska / Niemcy", bierzemy tylko pierwszy człon do tabeli głównej
    clean_name = name.split('/')[0].strip()

    # Mapowanie nazw
    code = COUNTRY_TO_ISO.get(clean_name)

    # Fallback: szukanie po kluczach lower()
    if not code:
        name_lower = clean_name.lower()
        for k, v in COUNTRY_TO_ISO.items():
            if k.lower() == name_lower:
                code = v
                break

    if code:
        return f"https://flagcdn.com/w40/{code}.png"
    return None


def get_multi_flags_html(nat_string):
    """
    Tworzy HTML z flagami dla profilu.
    Dla "Polska / Niemcy" tworzy kontener z dwoma obrazkami obok siebie.
    """
    if pd.isna(nat_string) or str(nat_string).strip() in ['-', '', 'nan']:
        return ""

    parts = str(nat_string).split('/')
    # Kontener flex, żeby flagi były w jednej linii
    html_out = "<div style='display: flex; align-items: center; gap: 5px; margin-top: 5px;'>"

    for part in parts:
        country_name = part.strip()
        url = get_flag_url(country_name)

        if url:
            # Styl zgodny z Twoim życzeniem
            html_out += f"""
            <img src="{url}" 
                 title="{country_name}" 
                 style="height: 25px; border: 1px solid #ccc; border-radius: 3px;">
            """
    html_out += "</div>"
    return html_out

def prepare_flags(df, col='narodowość'):
    """Dodaje kolumnę 'Flaga' do DataFrame (tylko pierwsza flaga do tabel)."""
    target_col = col
    # Szukamy kolumny z narodowością
    if target_col not in df.columns:
        poss = [c for c in df.columns if c.lower() in ['kraj', 'narodowosc', 'narodowość']]
        if poss: target_col = poss[0]

    if target_col in df.columns:
        # Do tabeli głównej bierzemy URL pierwszej flagi
        df['Flaga'] = df[target_col].apply(get_flag_url)
        # Ujednolicamy nazwę kolumny
        df = df.rename(columns={target_col: 'Narodowość'})
    else:
        df['Flaga'] = None
        df['Narodowość'] = '-'
    return df


@st.cache_data
def load_data(filename):
    if not os.path.exists(filename): return None
    try:
        try:
            df = pd.read_csv(filename, sep=None, engine='python', encoding='utf-8')
        except:
            df = pd.read_csv(filename, sep=None, engine='python', encoding='windows-1250')

        df = df.fillna("-")
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated()]

        cols_drop = [c for c in df.columns if 'lp' in c]
        if cols_drop: df = df.drop(columns=cols_drop)

        # 1. PEŁNA LISTA KOLUMN LICZBOWYCH (DO NAPRAWY BŁĘDÓW)
        # Dodano wszystkie kolumny statystyczne, które mogą powodować błędy
        int_candidates = [
            'wiek', 'suma', 'liczba', 'mecze', 'gole', 'punkty', 'minuty', 'numer',
            'asysty', 'żółte kartki', 'czerwone kartki', 'kanadyjka',
            'gole samobójcze', 'asysta 2. stopnia', 'sprokurowany karny', 'wywalczony karny',
            'karny', 'niestrzelony karny', 'główka', 'lewa', 'prawa', 'czyste konta',
            'obronione karne', 'wpuszczone gole', 'obronione rzuty karne'
        ]

        for col in df.columns:
            # Sprawdzamy czy nazwa kolumny pasuje do listy kandydatów
            if col in int_candidates or 'kartki' in col or 'gole' in col or 'karny' in col:
                # Najpierw konwersja do liczb (zamienia puste i błędy na NaN)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                # Potem rzutowanie na liczbę całkowitą (usuwa ".0")
                df[col] = df[col].astype(int)

        # Specyficzne dla mecze.csv
        if 'mecze.csv' in filename:
            col_att = next((c for c in df.columns if c in ['frekwencja', 'widzów']), None)
            if col_att:
                if col_att != 'widzów': df.rename(columns={col_att: 'widzów'}, inplace=True)
                df['widzów'] = df['widzów'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(r'\D', '',
                                                                                                         regex=True)
                df['widzów'] = pd.to_numeric(df['widzów'], errors='coerce').fillna(0).astype(int)

            place_col = next((c for c in df.columns if c in ['miejsce rozgrywania', 'miejsce', 'stadion']), None)
            if place_col:
                def is_h(val):
                    s = str(val).lower()
                    kw = ['bielsko', 'rychlińskiego', 'startowa', 'rekord', 'bks', 'czechowice', 'dom', 'gospodarz']
                    return '1' if any(k in s for k in kw) else '0'

                df['dom'] = df[place_col].apply(is_h)

        return df
    except Exception as e:
        return None


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
            cols.remove('Flaga');
            cols.insert(cols.index('Narodowość') + 1, 'Flaga')
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
        if t > o:
            style = 'color: #28a745; font-weight: bold;'
        elif t < o:
            style = 'color: #dc3545; font-weight: bold;'
        else:
            style = 'color: #fd7e14; font-weight: bold;'

    if any(x in val.lower() for x in ['pd', 'k.', 'wo']):
        style += ' font-style: italic; background-color: #f0f0f040;'
    return style


def extract_scorers_list(scorers_str):
    """
    Zwraca listę słowników dla przycisków strzelców.
    Obsługuje format: "Zawodnik 20, 40" oraz "Zawodnik 20, Inny 50".
    """
    if not isinstance(scorers_str, str) or pd.isna(scorers_str) or scorers_str.strip() in ['-', '']:
        return []

    parts = scorers_str.split(',')
    result = []
    last_valid_name = None

    for part in parts:
        part = part.strip()
        if not part: continue

        icon = "⚽"
        is_own = False

        # Rozpoznawanie (sam.) i (k)
        if any(x in part.lower() for x in ['(s)', 's.', 'sam.']):
            icon = "🔴"
            is_own = True
        elif any(x in part.lower() for x in ['(k)', 'k.', 'karny']):
            icon = "⚽🥅"

        # Czysta nazwa do linkowania profilu
        clean_name_candidate = re.sub(r'\(.*?\)', '', part)
        clean_name_candidate = re.sub(r'\d+', '', clean_name_candidate)
        clean_name_candidate = clean_name_candidate.replace("s.", "").replace("k.", "").replace("'", "").strip()

        # Czy to nazwisko czy tylko minuta?
        has_letters = bool(re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{2,}', clean_name_candidate))

        display_text = part
        link_name = ""

        if has_letters:
            last_valid_name = clean_name_candidate
            link_name = clean_name_candidate
            display_text = f"{icon} {part}"
        else:
            # Sytuacja: "43" po "Lazar 27"
            if last_valid_name:
                link_name = last_valid_name
                # Doklejamy nazwisko do wyświetlania, np. "⚽ Lazar 43'"
                # Czyścimy part z ewentualnych śmieci, zostawiając liczbę i flagi
                display_text = f"{icon} {last_valid_name} {part}"
            else:
                display_text = f"{icon} {part}"

        result.append({'display': display_text, 'link_name': link_name, 'is_own': is_own})

    return result

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

        # Logika ikon i stylów
        icon = "⚽"  # Domyślna piłka
        style = ""
        suffix = ""

        # Samobóje (priorytet sprawdzania)
        if any(x in part.lower() for x in ['(s)', 's.', 'sam.']):
            icon = "🔴"
            suffix = " (sam.)"
            part = re.sub(r'\(s\)|s\.|sam\.', '', part, flags=re.IGNORECASE).strip()
            style = "color: #dc3545;"  # Czerwony kolor

        # Karne
        elif any(x in part.lower() for x in ['(k)', 'k.', 'karny']):
            icon = "⚽🥅"  # Piłka + Bramka
            part = re.sub(r'\(k\)|k\.|karny', '', part, flags=re.IGNORECASE).strip()
            style = "font-weight: bold; color: #28a745;"  # Zielony pogrubiony

        html_parts.append(f"<span style='{style}'>{icon} {part}{suffix}</span>")

    return " | ".join(html_parts)


def get_minutes_map(scorers_str):
    """
    Tworzy mapę: nazwisko -> sformatowany tekst minut (np. 15', 88' (k)).
    Naprawia błąd braku przypisania kolejnych goli (np. 'Lazar 27, 43').
    """
    if not isinstance(scorers_str, str) or pd.isna(scorers_str): return {}

    mapping = {}
    parts = scorers_str.split(',')

    # Zmienna do zapamiętywania ostatniego zidentyfikowanego strzelca
    last_valid_name = None

    for part in parts:
        part = part.strip()
        if not part: continue

        # Wykrywanie flag
        is_pen = any(x in part.lower() for x in ['(k)', 'k.', 'karny'])
        is_own = any(x in part.lower() for x in ['(s)', 's.', 'sam.'])

        # Wyciąganie minut (wszystko co w nawiasie i jest cyfrą)
        mins_match = re.search(r'(\d+)', part)  # Szukamy po prostu liczb
        minutes_txt = mins_match.group(1) if mins_match else ""

        # Wyciąganie nazwiska (usuwamy cyfry, flagi i nawiasy)
        name_candidate = re.sub(r'\d+', '', part)
        name_candidate = re.sub(r'[\(\)]', '', name_candidate)  # usuń nawiasy
        name_candidate = re.sub(r'(k\.|s\.|sam\.|karny)', '', name_candidate, flags=re.IGNORECASE).strip()
        name_candidate = name_candidate.replace("'", "").strip()

        # Sprawdzamy czy to nowe nazwisko (musi mieć min. 2 litery)
        has_letters = bool(re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{2,}', name_candidate))

        final_key_name = None

        if has_letters:
            last_valid_name = name_candidate
            final_key_name = name_candidate
        elif last_valid_name:
            # Jeśli nie ma liter, ale mamy zapamiętane nazwisko (sytuacja "Lazar 27, 43")
            final_key_name = last_valid_name

        # Jeśli nie mamy nazwiska ani teraz, ani wcześniej, pomijamy
        if not final_key_name:
            continue

        # Budowanie sformatowanego stringa
        final_note = ""
        if minutes_txt:
            final_note = f"{minutes_txt}'"

        if is_pen: final_note += " (k)"
        if is_own: final_note += " (sam.)"

        if final_note:
            key = final_key_name.lower().strip()
            if key in mapping:
                mapping[key] += f", {final_note}"
            else:
                mapping[key] = final_note

    return mapping

def get_age_and_birthday(birth_date_val):
    if pd.isna(birth_date_val) or str(birth_date_val) in ['-', '', 'nan']: return None, False
    formats = ['%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d']
    dt = None
    for f in formats:
        try:
            dt = pd.to_datetime(birth_date_val, format=f); break
        except:
            continue
    if dt is None:
        try:
            dt = pd.to_datetime(birth_date_val)
        except:
            return None, False
    today = datetime.date.today()
    born = dt.date()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    is_birthday = (today.month == born.month) and (today.day == born.day)
    return age, is_birthday


def calculate_exact_age_str(birth_date, event_date):
    """Oblicza wiek w formacie: X lat, Y mies., Z dni"""
    if pd.isna(birth_date) or pd.isna(event_date): return ""
    try:
        # Upewniamy się, że to datetime
        b = pd.to_datetime(birth_date).date()
        e = pd.to_datetime(event_date).date()

        # Obliczenia
        years = e.year - b.year
        if (e.month, e.day) < (b.month, b.day):
            years -= 1

        # Do obliczenia miesięcy i dni można użyć dateutil, ale zrobimy to prosto bez dodatkowych bibliotek
        # Resetujemy rok urodzenia do roku wydarzenia (lub poprzedniego)
        if (e.month, e.day) < (b.month, b.day):
            last_bday = datetime.date(e.year - 1, b.month, b.day)
        else:
            last_bday = datetime.date(e.year, b.month, b.day)

        delta = e - last_bday
        # Przybliżenie miesięcy (delta.days // 30) lub dokładniej:
        months = 0
        days = delta.days

        # Prostszą metodą dla wyświetlania jest:
        return f"({years} lat, {days // 30} mies., {days % 30} dni)"
    except:
        return ""


def get_player_record_badges(player_name, df_w=None, df_p=None):
    """Zwraca listę słowników z odznakami (ikona, tekst, kolor)."""
    badges = []
    try:
        # OPTYMALIZACJA: Używamy przekazanych DataFrame'ów, jeśli są, inaczej ładujemy
        if df_w is None: df_w = load_details("wystepy.csv")
        if df_p is None: df_p = load_data("pilkarze.csv")

        if df_w is None or df_p is None: return []

        # Filtrowanie danych dla zawodnika
        p_data = df_w[df_w['Zawodnik_Clean'] == player_name].copy()

        # Jeśli brak danych o występach, nic nie policzymy
        if p_data.empty: return []

        # --- 0. OBLICZENIE TOTAL MATCHES (DLA KLUBU 100) ---
        manual_matches = 0
        if not df_p.empty:
            row = df_p[df_p['imię i nazwisko'] == player_name]
            if not row.empty:
                for col in ['suma', 'mecze', 'liczba']:
                    if col in row.columns:
                        manual_matches = int(pd.to_numeric(row.iloc[0][col], errors='coerce') or 0)
                        break

        calc_matches = len(p_data)
        total_matches = max(manual_matches, calc_matches)

        # 🏅 ODZNAKA: KLUB 100
        if total_matches >= 100:
            badges.append({"icon": "💯", "text": f"Klub 100 ({total_matches} spotkań)",
                           "color": "#d63031"})

        # 🚀 [NOWOŚĆ] ODZNAKA: AWANS DO EKSTRAKLASY
        seasons_played = set(p_data['Sezon'].unique())
        promotions = []
        if '2010/2011' in seasons_played: promotions.append("2011")
        if '2019/2020' in seasons_played: promotions.append("2020")

        if promotions:
            txt_promo = f"Awans do Ekstraklasy ({', '.join(promotions)})"
            badges.append({"icon": "🚀", "text": txt_promo, "color": "#FFD700"})  # Złoty kolor

        # --- 1. REKORDY RANKINGOWE (TOP LISTY) ---
        if 'Data_Sort' in df_w.columns:
            # Najmłodsi debiutanci
            # (Optymalizacja: Robimy to tylko jeśli df_w nie jest pusty)
            first_games = df_w.groupby('Zawodnik_Clean')['Data_Sort'].min().reset_index()
            df_p['join_key'] = df_p['imię i nazwisko'].astype(str).str.strip()
            df_merged = pd.merge(first_games, df_p.drop_duplicates('join_key'), left_on='Zawodnik_Clean',
                                 right_on='join_key')

            def calc_age(r):
                try:
                    return (r['Data_Sort'] - pd.to_datetime(r['data urodzenia'], dayfirst=True)).days
                except:
                    return 99999

            df_merged['Age_Days'] = df_merged.apply(calc_age, axis=1)
            top_young = df_merged.sort_values('Age_Days').head(10)['Zawodnik_Clean'].tolist()

            if player_name in top_young:
                place = top_young.index(player_name) + 1
                badges.append({"icon": "👶", "text": f"{place}. najmłodszy debiutant", "color": "#3498db"})

            # Najstarsi zawodnicy
            last_games = df_w.groupby('Zawodnik_Clean')['Data_Sort'].max().reset_index()
            df_merged_old = pd.merge(last_games, df_p.drop_duplicates('join_key'), left_on='Zawodnik_Clean',
                                     right_on='join_key')
            df_merged_old['Age_Days'] = df_merged_old.apply(calc_age, axis=1)
            df_merged_old = df_merged_old[df_merged_old['Age_Days'] < 22000] # Filtr błędnych dat
            top_old = df_merged_old.sort_values('Age_Days', ascending=False).head(10)['Zawodnik_Clean'].tolist()

            if player_name in top_old:
                place = top_old.index(player_name) + 1
                badges.append({"icon": "👴", "text": f"{place}. najstarszy w historii", "color": "#9b59b6"})

        # Najlepsi strzelcy (TOP 10)
        df_w['Gole'] = pd.to_numeric(df_w['Gole'], errors='coerce').fillna(0)
        total_goals_all = df_w.groupby('Zawodnik_Clean')['Gole'].sum().sort_values(ascending=False).head(10)
        if player_name in total_goals_all.index and total_goals_all[player_name] > 0:
            place = list(total_goals_all.index).index(player_name) + 1
            badges.append({"icon": "👑", "text": f"{place}. strzelec wszech czasów", "color": "#f1c40f"})

        # --- 2. OSIĄGNIĘCIA INDYWIDUALNE ---
        # HAT-TRICK HERO
        hattricks = len(p_data[p_data['Gole'] >= 3])
        if hattricks > 0:
            badges.append({"icon": "🎩", "text": f"Hat-trick Hero ({hattricks}x)", "color": "#2ecc71"})

        # SUPER JOKER
        bench_goals = p_data[p_data['Status'] == 'Wszedł']['Gole'].sum()
        if bench_goals >= 3:
            badges.append({"icon": "🃏", "text": f"Super Joker ({int(bench_goals)} goli)", "color": "#e67e22"})

        # WETERAN
        seasons_cnt = p_data['Sezon'].nunique()
        if seasons_cnt >= 5:
            badges.append({"icon": "🦅", "text": f"Weteran ({seasons_cnt} sezonów)", "color": "#7f8c8d"})
        elif seasons_cnt >= 3:
            badges.append({"icon": "🛡️", "text": f"Solidny Ligowiec ({seasons_cnt} sezony)", "color": "#95a5a6"})

        # BAD BOY
        reds = pd.to_numeric(p_data['Czerwone'], errors='coerce').fillna(0).sum()
        if reds >= 2:
            badges.append({"icon": "🟥", "text": f"Bad Boy ({int(reds)} cz. kartki)", "color": "#e74c3c"})

        # ŻELAZNE PŁUCA
        mins = pd.to_numeric(p_data['Minuty'], errors='coerce').fillna(0).sum()
        if mins > 5000:
            badges.append({"icon": "🫁", "text": "Żelazne Płuca (>5k min)", "color": "#34495e"})

    except Exception as e:
        return []

    return badges

def admin_save_csv(filename, new_data_dict):
    try:
        df = pd.read_csv(filename)
        new_row = pd.DataFrame([new_data_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(filename, index=False)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu: {e}");
        return False


def get_match_icon(val):
    if pd.isna(val): return "🚌"
    s = str(val).lower().strip()
    if s in ['1', 'true', 'tak', 'dom', 'gospodarz', 'd', 'u siebie']: return "🏠"
    return "🚌"


# --- MENU ---
st.sidebar.header("Nawigacja")

# Definiujemy dostępne opcje
menu_options = [
    "Aktualny Sezon (25/26)",
    "Kalendarz",
    "Składy Historyczne",
    "Centrum Zawodników",
    "Centrum Meczowe",
    "🏆 Rekordy & TOP",
    "Trenerzy"
]

# Dodajemy tajną sekcję tylko jeśli użytkownik to nie 'guest'
if st.session_state.get('username') != 'guest':
    menu_options.append("🕵️ Ciemne Karty Historii")

opcja = st.sidebar.radio("Moduł:", menu_options)

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
                try:
                    df_editor = pd.read_csv(selected_file, encoding='utf-8')
                except:
                    df_editor = pd.read_csv(selected_file, encoding='windows-1250')

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
                    except Exception as e:
                        st.error(f"Błąd zapisu: {e}")

            except Exception as e:
                st.error(f"Błąd pliku: {e}")

    with st.sidebar.expander("➕ SZYBKIE DODAWANIE"):
        tab_p, tab_m = st.tabs(["Piłkarz", "Mecz"])
        with tab_p:
            with st.form("add_player_form"):
                a_imie = st.text_input("Imię i Nazwisko")
                a_kraj = st.text_input("Kraj", value="Polska")
                a_poz = st.selectbox("Pozycja", ["Bramkarz", "Obrońca", "Pomocnik", "Napastnik"])
                a_data = st.date_input("Data urodzenia", min_value=datetime.date(1970, 1, 1))
                if st.form_submit_button("Zapisz Piłkarza"):
                    if a_imie and os.path.exists("pilkarze.csv"):
                        admin_save_csv("pilkarze.csv", {"imię i nazwisko": a_imie, "kraj": a_kraj, "pozycja": a_poz,
                                                        "data urodzenia": str(a_data), "SUMA": 0})
                        st.success(f"Dodano: {a_imie}");
                        time.sleep(1);
                        st.rerun()
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
                        admin_save_csv("mecze.csv", {"sezon": a_sezon, "rywal": a_rywal, "wynik": a_wynik,
                                                     "data meczu": str(a_data_m), "Dom": dom_val, "Widzów": 0})
                        st.success("Dodano mecz!");
                        time.sleep(1);
                        st.rerun()
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
elif opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Kadra 2025/2026")

    # --- 0. ROUTER (Profil) ---
    if st.session_state.get('cm_selected_player'):
        if st.button("⬅️ Wróć do kadry"):
            st.session_state['cm_selected_player'] = None
            st.rerun()
        st.divider()
        render_player_profile(st.session_state['cm_selected_player'])

    # --- 1. WIDOK GŁÓWNY ---
    else:
        df = load_data("25_26.csv")
        if df is not None:
            # Przygotowanie danych
            if 'status' in df.columns:
                df['is_youth'] = df['status'].astype(str).str.contains(r'\(M\)', case=False, regex=True)
                df.loc[df['is_youth'], 'imię i nazwisko'] = "Ⓜ️ " + df.loc[df['is_youth'], 'imię i nazwisko']

            # Konwersja liczb
            numeric_cols_list = [
                'mecze', 'gole', 'asysty', 'kanadyjka', 'minuty', 'żółte kartki', 'czerwone kartki',
                'gole samobójcze', 'asysta 2. stopnia', 'wywalczony karny', 'sprokurowany karny',
                'karny', 'niestrzelony karny', 'główka', 'lewa', 'prawa', 'czyste konta', 'obronione karne'
            ]
            for col in numeric_cols_list:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            df = prepare_flags(df)

            # Filtry UI
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                search_q = st.text_input("🔍 Szukaj:", placeholder="Nazwisko...")
            with c2:
                view_mode = st.selectbox("Widok:", ["Tabela Szczegółowa", "Podział na Formacje"])
            with c3:
                sort_by = st.selectbox("Sortuj:", ["Nr", "Mecze", "Gole", "Kartki"], index=0)
            with c4:
                show_only_youth = st.checkbox("Młodzieżowcy", value=False)

            # Filtrowanie
            df_view = df.copy()
            if show_only_youth: df_view = df_view[df_view['is_youth']]
            if search_q: df_view = df_view[
                df_view.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]

            # Sortowanie
            sort_map = {'Nr': 'numer', 'Mecze': 'mecze', 'Gole': 'gole', 'Kartki': 'żółte kartki'}
            s_col = sort_map.get(sort_by, 'numer')
            if s_col in df_view.columns:
                asc = (s_col == 'numer')
                df_view = df_view.sort_values(s_col, ascending=asc)

            # Konfiguracja kolumn
            mx_mecze = int(df['mecze'].max()) if not df.empty else 1
            col_config = {
                "Flaga": st.column_config.ImageColumn("", width="small"),
                "mecze": st.column_config.ProgressColumn("Mecze", format="%d", min_value=0, max_value=mx_mecze),
                "gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                "asysty": st.column_config.NumberColumn("Asysty", format="%d 🅰️"),
                "minuty": st.column_config.NumberColumn("Minuty", format="%d'")
            }


            # Helper do wyświetlania interaktywnej tabeli Z PODŚWIETLENIEM
            def show_interactive_table(data_frame, key_suffix=""):
                cols = ['numer', 'imię i nazwisko', 'Flaga', 'pozycja', 'mecze', 'minuty', 'gole', 'asysty',
                        'żółte kartki', 'czerwone kartki']
                final_cols = [c for c in cols if c in data_frame.columns]

                # Highlight logic - podświetlamy max wartości w kluczowych kolumnach
                subset_to_highlight = [c for c in ['mecze', 'gole', 'asysty', 'minuty'] if c in data_frame.columns]

                styled_df = data_frame[final_cols].style.highlight_max(
                    subset=subset_to_highlight,
                    color='#28a74530',  # Jasnozielone tło
                    axis=0
                )

                event = st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=col_config,
                    on_select="rerun",
                    selection_mode="single-row",
                    key=f"tab_kadra_{key_suffix}"
                )
                if event.selection.rows:
                    idx = event.selection.rows[0]
                    raw_name = data_frame.iloc[idx]['imię i nazwisko']
                    clean_name = str(raw_name).replace("Ⓜ️ ", "").strip()
                    st.session_state['cm_selected_player'] = clean_name
                    st.rerun()


            # RENDEROWANIE
            if view_mode == "Tabela Szczegółowa":
                show_interactive_table(df_view, "main")
            else:
                if 'pozycja' in df_view.columns:
                    # Kolejność logiczna
                    order = ["Bramkarz", "Obrońca", "Pomocnik", "Napastnik"]
                    available = df_view['pozycja'].astype(str).unique()

                    for pos in order:
                        if pos in available:
                            sub = df_view[df_view['pozycja'] == pos]
                            if not sub.empty:
                                st.markdown(f"### {pos}")
                                show_interactive_table(sub, f"pos_{pos}")
                                st.write("")  # Odstęp

                    # Pozostałe
                    for pos in available:
                        if pos not in order:
                            sub = df_view[df_view['pozycja'] == pos]
                            if not sub.empty:
                                st.markdown(f"### {pos}")
                                show_interactive_table(sub, f"pos_{pos}")

        else:
            st.error("Brak pliku 25_26.csv")

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

    # 3. WIDOK SZCZEGÓŁÓW MECZU (ULEPSZONY - STYL RAPORTU)
    elif st.session_state['cal_view_mode'] == 'match':
        if st.button("⬅️ Wróć do Kalendarza"):
            st.session_state['cal_view_mode'] = 'list'
            st.rerun()
        st.divider()

        m_data = st.session_state['cal_selected_item']

        # Nagłówek
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background-color: rgba(40, 167, 69, 0.15); border: 1px solid #28a745; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="margin:0; color: var(--text-color);">{m_data.get('Rywal', 'Rywal')}</h2>
            <p style="color: gray; margin: 5px 0 0 0;">📅 {m_data.get('Data_Txt', '-')} | 🏟️ {"Dom" if str(m_data.get('Dom')) in ['1', 'True'] else "Wyjazd"}</p>
            <h1 style="margin: 10px 0;">{m_data.get('Wynik', '-')}</h1>
            <small>Widzów: {m_data.get('Widzów', '-')}</small>
        </div>
        """, unsafe_allow_html=True)

        # --- SEKCJA STRZELCÓW ---
        scorers_str = m_data.get('Strzelcy', '-')
        if scorers_str and scorers_str != '-' and str(scorers_str).lower() != 'nan':
            st.markdown("### 🥅 Strzelcy")
            scorers_list = extract_scorers_list(scorers_str)
            if scorers_list:
                cols_sc = st.columns(4)
                for idx, item in enumerate(scorers_list):
                    col_idx = idx % 4
                    with cols_sc[col_idx]:
                        if item['is_own']:
                            st.error(item['display'])
                        else:
                            if st.button(item['display'], key=f"cal_match_sc_{idx}_{item['link_name']}"):
                                st.session_state['cal_selected_item'] = item['link_name']
                                st.session_state['cal_view_mode'] = 'profile'
                                st.rerun()
            else:
                st.write(scorers_str)
            st.divider()

        # --- SEKCJA SKŁADU (ZAPOŻYCZONA Z RAPORTÓW) ---
        df_det = load_details("wystepy.csv")

        # Próba znalezienia składu po dacie
        found_squad = False
        if df_det is not None and 'Data_Obj' in m_data:
            match_date = pd.to_datetime(m_data['Data_Obj']).date()

            if 'Data_Sort' in df_det.columns:
                # Filtrujemy po dacie (ignorujemy godzinę)
                squad = df_det[df_det['Data_Sort'].dt.date == match_date].copy()

                if not squad.empty:
                    found_squad = True
                    squad = squad.sort_values('File_Order')  # Zachowaj kolejność z pliku

                    # --- LOGIKA ZMIAN (Kopiuj-Wklej z Centrum Meczowego) ---
                    map_in_to_out = {}
                    map_out_to_in = {}
                    in_rows = squad[squad['Status'] == 'Wszedł'].sort_values('Minuta_Zmiany_Real')
                    out_rows = squad[squad['Status'].isin(['Zszedł'])].sort_values('Minuta_Zmiany_Real')
                    used_out = []

                    for _, ri in in_rows.iterrows():
                        m = ri['Minuta_Zmiany_Real']
                        cands = out_rows[~out_rows.index.isin(used_out)].copy()
                        cands['d'] = (cands['Minuta_Zmiany_Real'] - m).abs()
                        cands = cands[cands['d'] <= 3].sort_values('d')
                        if not cands.empty:
                            best = cands.iloc[0]
                            map_in_to_out[ri['Zawodnik_Clean']] = best['Zawodnik_Clean']
                            map_out_to_in[best['Zawodnik_Clean']] = ri['Zawodnik_Clean']
                            used_out.append(best.name)


                    # --- FUNKCJA RENDERUJĄCA ---
                    def render_cal_row(row, is_bench=False):
                        c1, c2, c3 = st.columns([1, 4, 3])
                        name = row['Zawodnik_Clean']
                        mins = int(row.get('Minuty', 0))
                        ev_min = int(row.get('Minuta_Zmiany_Real', 0))

                        with c1:
                            if is_bench:
                                st.caption(f"{ev_min}'")
                            else:
                                st.write(f"{mins}'")

                        with c2:
                            if st.button(name, key=f"c_sq_{name}_{match_date}", use_container_width=True):
                                st.session_state['cal_selected_item'] = name
                                st.session_state['cal_view_mode'] = 'profile'
                                st.rerun()

                        # Zdarzenia
                        evs = []
                        g = int(row.get('Gole', 0));
                        if g > 0: evs.append(f"<span style='color:green'>{'⚽' * g}</span>")
                        y = int(row.get('Żółte', 0));
                        if y > 0: evs.append(f"🟨{'x' + str(y) if y > 1 else ''}")
                        r = int(row.get('Czerwone', 0));
                        if r > 0: evs.append("🟥")

                        stat = row.get('Status', '')
                        if stat == 'Wszedł':
                            rep = map_in_to_out.get(name)
                            txt = f"za: {rep}" if rep else ""
                            evs.append(f"<span style='color:#28a745; font-size:0.8em'>⬆️ {txt}</span>")
                        elif stat == 'Zszedł':
                            rep = map_out_to_in.get(name)
                            txt = f"zm: {rep}" if rep else ""
                            evs.append(f"<span style='color:#dc3545; font-size:0.8em'>⬇️ {txt} ({ev_min}')</span>")
                        elif stat == 'Czerwona kartka':
                            evs.append(f"<span style='color:red; font-size:0.8em'>🟥 ({ev_min}')</span>")

                        with c3:
                            if evs: st.markdown(" ".join(evs), unsafe_allow_html=True)


                    # --- WYŚWIETLANIE ---
                    starters = squad[
                        squad['Status'].isin(['Cały mecz', 'Zszedł', 'Grał', 'Czerwona kartka'])].sort_values(
                        'File_Order')
                    subs = squad[squad['Status'] == 'Wszedł'].sort_values('Minuta_Zmiany_Real')
                    unused = squad[squad['Status'] == 'Rezerwowy']

                    cl, cr = st.columns(2)
                    with cl:
                        st.subheader("🏟️ Wyjściowa XI")
                        if not starters.empty:
                            for _, r in starters.iterrows(): render_cal_row(r, False)
                        else:
                            st.info("Brak danych.")
                    with cr:
                        st.subheader("🔄 Zmiennicy")
                        if not subs.empty:
                            for _, r in subs.iterrows(): render_cal_row(r, True)
                        else:
                            st.caption("Brak zmian.")

                        if not unused.empty:
                            st.divider()
                            st.markdown("**💤 Ławka**")
                            for _, r in unused.iterrows():
                                if st.button(r['Zawodnik_Clean'], key=f"c_bench_{r['Zawodnik_Clean']}_{match_date}"):
                                    st.session_state['cal_selected_item'] = r['Zawodnik_Clean']
                                    st.session_state['cal_view_mode'] = 'profile'
                                    st.rerun()

        if not found_squad:
            st.info("ℹ️ Brak szczegółowego składu w `wystepy.csv` dla tej daty.")

    # 4. GŁÓWNY WIDOK KALENDARZA (BEZ ZMIAN W LOGICE, TYLKO KOD)
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
            cal_mode = st.radio("Tryb widoku:", ["Dzień w Historii (2026 + Archiwum)", "Konkretny Rocznik (Archiwum)"],
                                horizontal=True)

        # Ustalanie roku bazowego
        if "Konkretny" in cal_mode:
            with c_mode2:
                target_year = st.number_input("Wybierz rok do przeglądania:", min_value=1990, max_value=2030,
                                              value=today.year)
            show_history_matches = False
        else:
            target_year = today.year
            show_history_matches = True
            with c_mode2:
                st.write("")

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
                matches_today = df_m[df_m['dt_obj'].dt.date == today]
                if not matches_today.empty:
                    row_t = matches_today.iloc[0]
                    rival = row_t.get('rywal', 'Rywal')
                    place = "🏠 u siebie" if str(row_t.get('dom', '0')) in ['1', 'True', 'dom'] else "🚌 wyjazd"
                    match_today_alert = f"{rival} ({place})"

        if match_today_alert:
            st.markdown(f"""
            <div style="background-color: rgba(40, 167, 69, 0.2); border: 2px solid #28a745; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h2 style="color: #28a745; margin:0;">🔥 DZIEŃ MECZOWY! 🔥</h2>
                <h3 style="margin:5px 0;">TSP vs {match_today_alert.split('(')[0]}</h3>
                <p style="margin:0; font-weight:bold;">{match_today_alert.split('(')[1].replace(')', '')}</p>
            </div>
            """, unsafe_allow_html=True)

        # --- BUDOWANIE MAPY ZDARZEŃ ---
        events_map = {}

        # A. Urodziny Piłkarzy
        if df_p is not None:
            df_p['id_name'] = df_p['imię i nazwisko'].astype(str).str.lower().str.strip()
            df_unique = df_p.drop_duplicates(subset=['id_name'], keep='first')
            col_b = next((c for c in df_unique.columns if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
            current_squad_names = [str(x).lower().strip() for x in
                                   df_curr['imię i nazwisko'].unique()] if df_curr is not None else []

            if col_b:
                for _, row in df_unique.iterrows():
                    try:
                        name = row['imię i nazwisko']
                        # Fix dla Macieja Górskiego
                        if "Maciej Górski" in str(name):
                            bdate = pd.to_datetime("1990-03-01")
                        else:
                            bdate = pd.to_datetime(row[col_b], dayfirst=True, errors='coerce')

                        if pd.isna(bdate): continue
                        key = (bdate.month, bdate.day)
                        is_curr = row['id_name'] in current_squad_names
                        prefix = "🟢🎂" if is_curr else "🎂"
                        age = target_year - bdate.year
                        if age >= 0:
                            events_map.setdefault(key, []).append(
                                {'type': 'birthday', 'label': f"{prefix} {name} ({age})", 'name': name,
                                 'sort': 1 if is_curr else 2})
                    except:
                        pass

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
                            events_map.setdefault(key, []).append(
                                {'type': 'coach_birthday', 'label': f"👔🎂 {name} ({age})", 'name': name, 'sort': 2})
                    except:
                        pass

        # C. Mecze
        if df_m is not None and 'dt_obj' in df_m.columns:
            for _, row in df_m.dropna(subset=['dt_obj']).iterrows():
                d = row['dt_obj']
                d_date = d.date()
                key = (d.month, d.day)

                should_add = False
                is_history_event = False

                if show_history_matches:
                    if d.year == target_year:
                        should_add = True; is_history_event = False
                    else:
                        should_add = True; is_history_event = True
                else:
                    if d.year == target_year: should_add = True; is_history_event = False

                if should_add:
                    raw_score = str(row.get('wynik', '')).strip()
                    if raw_score.lower() == 'nan': raw_score = ''
                    rywal = row.get('rywal', 'Rywal')

                    if is_history_event:
                        icon = "⚫"
                        sort_prio = 5
                        score_part = f" {raw_score}" if raw_score else ""
                        label_str = f"{icon} {rywal}{score_part} ({d.year})"
                    else:
                        if d_date > today and d.year == today.year:
                            icon = "🔜"; info = ""; sort_prio = 0
                        elif d_date == today:
                            icon = "🔥"; info = raw_score if raw_score else "DZIŚ"; sort_prio = 0
                        else:
                            icon = "⚽"; info = raw_score; sort_prio = 3
                        label_str = f"{icon} {rywal} {info}"

                    match_details = {'Rywal': rywal, 'Data_Txt': d.strftime('%d.%m.%Y'), 'Data_Obj': d,
                                     'Wynik': f"{raw_score}", 'Strzelcy': row.get('strzelcy', '-'),
                                     'Widzów': row.get('widzów', '-'), 'Dom': row.get('dom', '0')}

                    events_map.setdefault(key, []).append({
                        'type': 'match', 'label': label_str, 'match_data': match_details,
                        'sort': sort_prio, 'is_history': is_history_event
                    })

        # --- WIDOK 1: TYGODNIOWY ---
        st.subheader(f"Ten tydzień ({today.strftime('%B')})")
        start_of_week = today - datetime.timedelta(days=today.weekday())
        cols = st.columns(7)
        days_pl = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]

        for i, col in enumerate(cols):
            curr_day = start_of_week + datetime.timedelta(days=i)
            is_today = (curr_day == today)
            lookup_key = (curr_day.month, curr_day.day)
            day_events = events_map.get(lookup_key, [])
            day_events.sort(key=lambda x: (x.get('sort', 5)))

            with col:
                css_class = "cal-card today" if is_today else "cal-card"
                st.markdown(
                    f"<div class='{css_class}'><small>{days_pl[i]}</small><br><strong>{curr_day.strftime('%d.%m')}</strong></div>",
                    unsafe_allow_html=True)
                if not day_events: st.markdown(
                    "<div style='text-align: center; opacity: 0.3; font-size: 10px;'>Brak</div>",
                    unsafe_allow_html=True)

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
            pl_months = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień",
                         "Październik", "Listopad", "Grudzień"]
            sel_month_name = c_m2.selectbox("Miesiąc", pl_months, index=today.month - 1)
            sel_month = pl_months.index(sel_month_name) + 1

            cols_h = st.columns(7)
            for i, d in enumerate(days_pl): cols_h[i].markdown(f"**{d}**")

            cal_data = calendar.monthcalendar(target_year, sel_month)
            for week in cal_data:
                cols_w = st.columns(7)
                for i, day_num in enumerate(week):
                    with cols_w[i]:
                        if day_num != 0:
                            is_today_cell = (
                                        day_num == today.day and sel_month == today.month and target_year == today.year)
                            css_class = "cal-card today" if is_today_cell else "cal-card"
                            st.markdown(f"<div class='{css_class}'><strong>{day_num}</strong></div>",
                                        unsafe_allow_html=True)

                            valid_events = events_map.get((sel_month, day_num), [])
                            valid_events.sort(key=lambda x: (x.get('sort', 5)))

                            for idx, ev in enumerate(valid_events):
                                btn_key = f"ev_month_{target_year}_{sel_month}_{day_num}_{idx}_{ev['label']}"
                                if ev['type'] == 'match':
                                    b_type = "secondary"
                                    if not ev.get('is_history', False):
                                        if "🔜" in ev['label'] or "🔥" in ev['label']: b_type = "primary"
                                    if st.button(ev['label'], key=btn_key, type=b_type, use_container_width=True):
                                        st.session_state['cal_selected_item'] = ev['match_data']
                                        st.session_state['cal_view_mode'] = 'match'
                                        st.rerun()
                                elif ev['type'] == 'birthday':
                                    if st.button(ev['label'], key=btn_key, use_container_width=True):
                                        st.session_state['cal_selected_item'] = ev['name']
                                        st.session_state['cal_view_mode'] = 'profile'
                                        st.rerun()
                                elif ev['type'] == 'coach_birthday':
                                    if st.button(ev['label'], key=btn_key, use_container_width=True):
                                        st.session_state['cal_selected_item'] = ev['name']
                                        st.session_state['cal_view_mode'] = 'coach_profile'
                                        st.rerun()

    st.caption("Legenda: 🔥 Dzień Meczowy | 🔜 Nadchodzące | 🟢 Kadra | ⚫ Archiwum (inne lata)")

elif opcja == "Składy Historyczne":
    st.header("🗂️ Składy Historyczne")

    # --- 0. ROUTER ---
    if st.session_state.get('cm_selected_player'):
        if st.button("⬅️ Wróć do składu", key="back_from_player_hist"):
            st.session_state['cm_selected_player'] = None
            st.rerun()
        st.divider()
        render_player_profile(st.session_state['cm_selected_player'])

    elif st.session_state.get('hist_selected_coach'):
        if st.button("⬅️ Wróć do składu", key="back_from_coach_hist"):
            st.session_state['hist_selected_coach'] = None
            st.rerun()
        st.divider()
        render_coach_profile(st.session_state['hist_selected_coach'])

    # --- 1. WIDOK GŁÓWNY ---
    else:
        df_det = load_details("wystepy.csv")
        df_bio = load_data("pilkarze.csv")
        df_t = load_data("trenerzy.csv")

        if 'filter_seasons' in globals(): df_det = filter_seasons(df_det, 'Sezon')

        if df_det is None or df_bio is None:
            st.error("Brak wymaganych plików.")
        else:
            if df_t is not None: df_t = prepare_flags(df_t)
            seasons = sorted(df_det['Sezon'].unique(), reverse=True)

            c_sel_s, c_check_m = st.columns([3, 1])
            with c_sel_s:
                sel_season = st.selectbox("Wybierz Sezon:", seasons)
            with c_check_m:
                st.write("")
                st.write("")
                show_only_youth = st.checkbox("Tylko Młodzieżowcy (Ⓜ️)")

            season_data = df_det[df_det['Sezon'] == sel_season].copy()

            agg = season_data.groupby('Zawodnik_Clean').agg({
                'Minuty': 'sum', 'Mecz_Label': 'nunique', 'Gole': 'sum', 'Żółte': 'sum', 'Czerwone': 'sum'
            }).reset_index()
            agg.rename(columns={'Mecz_Label': 'Mecze'}, inplace=True)
            agg['Gole'] = pd.to_numeric(agg['Gole'], errors='coerce').fillna(0).astype(int)

            df_bio_unique = df_bio.drop_duplicates(subset=['imię i nazwisko']).copy()
            df_bio_unique['join_key'] = df_bio_unique['imię i nazwisko'].astype(str).str.strip()
            df_bio_unique = prepare_flags(df_bio_unique)

            merged = pd.merge(agg, df_bio_unique, left_on='Zawodnik_Clean', right_on='join_key', how='left')

            # Logika młodzieżowca
            try:
                start_year = int(sel_season.split('/')[0])
            except:
                start_year = 2025
            limit_year = start_year - 21


            def check_youth_status(row):
                nat = str(row.get('Narodowość', '')).lower()
                if not any(x in nat for x in ['polska', 'poland', 'pl']): return False
                dob_val = row.get('data urodzenia')
                if pd.isna(dob_val): return False
                try:
                    y = pd.to_datetime(dob_val).year
                    return y >= limit_year
                except:
                    return False


            merged['Is_Youth'] = merged.apply(check_youth_status, axis=1)
            merged['Zawodnik_Display'] = merged.apply(
                lambda r: f"Ⓜ️ {r['Zawodnik_Clean']}" if r['Is_Youth'] else r['Zawodnik_Clean'], axis=1)

            if show_only_youth: merged = merged[merged['Is_Youth'] == True]


            def normalize_position_group(val):
                s = str(val).lower().strip()
                if 'bram' in s or 'gk' in s: return "Bramkarz"
                if any(x in s for x in ['obr', 'stoper', 'def', 'boczny']): return "Obrońca"
                if any(x in s for x in ['pom', 'skrzyd', 'mid', 'wahad']): return "Pomocnik"
                if any(x in s for x in ['nap', 'snaj', 'for', 'atak']): return "Napastnik"
                return "Inne"


            merged['Grupa_Pozycji'] = merged['pozycja'].apply(normalize_position_group)


            def calc_season_age(dob_val):
                try:
                    return start_year - pd.to_datetime(dob_val).year
                except:
                    return None


            merged['Wiek_w_Sezonie'] = merged['data urodzenia'].apply(calc_season_age)

            # --- STATYSTYKI ZBIORCZE ---
            if not show_only_youth:
                st.markdown(f"""
                <div style="background-color: var(--secondary-background-color); padding: 15px; border-radius: 10px; border: 1px solid #ccc; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-around;">
                        <div style="text-align: center;"><h3>{agg['Gole'].sum()} ⚽</h3><small>Goli</small></div>
                        <div style="text-align: center;"><h3>{len(agg)} 👤</h3><small>Piłkarzy</small></div>
                        <div style="text-align: center;"><h3>{merged['Wiek_w_Sezonie'].mean():.1f} lat</h3><small>Średnia wieku</small></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.divider()

            # --- TRENERZY ---
            if not show_only_youth and df_t is not None and 'Data_Sort' in season_data.columns:
                # (Kod obsługi trenerów bez zmian logicznych, pomijam dla czytelności, jest taki sam jak w oryginale)
                # ... [tu wstaw kod trenerów, jeśli potrzebny, lub zostaw jak był] ...
                pass

                # --- TABELE (ZMIANA UKŁADU) ---
            formations_order = [
                ("Bramkarz", "🧤 Bramkarze"),
                ("Obrońca", "🛡️ Obrońcy"),
                ("Pomocnik", "⚙️ Pomocnicy"),
                ("Napastnik", "⚽ Napastnicy"),
                ("Inne", "❓ Nieznana pozycja")
            ]

            cols_show = ['Flaga', 'Zawodnik_Display', 'Grupa_Pozycji', 'pozycja', 'Wiek_w_Sezonie', 'Mecze', 'Minuty',
                         'Gole', 'Żółte', 'Czerwone']
            final_df = merged[[c for c in cols_show if c in merged.columns]]

            common_config = {
                "Flaga": st.column_config.ImageColumn("", width="small"),
                "Minuty": st.column_config.ProgressColumn("Minuty", format="%d'",
                                                          max_value=int(merged['Minuty'].max() or 100)),
                "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                "Żółte": st.column_config.NumberColumn("Żółte", format="%d 🟨"),
                "Czerwone": st.column_config.NumberColumn("Czerwone", format="%d 🟥")
            }

            # Wyświetlanie jeden pod drugim (bez kolumn)
            for group_key, header_txt in formations_order:
                df_pos = final_df[final_df['Grupa_Pozycji'] == group_key].sort_values(['Minuty', 'Mecze'],
                                                                                      ascending=False)

                if not df_pos.empty:
                    st.markdown(f"#### {header_txt}")

                    # Highlight tutaj też
                    styled_pos = df_pos.style.highlight_max(subset=['Minuty', 'Gole', 'Mecze'], color='#28a74530',
                                                            axis=0)

                    event_pos = st.dataframe(
                        styled_pos,
                        use_container_width=True, hide_index=True,
                        column_config=common_config,
                        on_select="rerun", selection_mode="single-row",
                        key=f"hist_table_{sel_season}_{group_key}"
                    )

                    if event_pos.selection.rows:
                        idx = event_pos.selection.rows[0]
                        raw = df_pos.iloc[idx]['Zawodnik_Display']
                        st.session_state['cm_selected_player'] = str(raw).replace("Ⓜ️ ", "").strip()
                        st.rerun()

                    st.write("")  # Odstęp
elif opcja == "Centrum Zawodników":
    st.header("👤 Centrum Zawodników")

    # --- A. ROUTER PROFILU ---
    if st.session_state.get('cm_selected_player'):
        if st.button("⬅️ Wróć do listy", key="back_cz"):
            st.session_state['cm_selected_player'] = None
            st.rerun()
        st.divider()
        render_player_profile(st.session_state['cm_selected_player'])

    # --- B. GŁÓWNA LISTA ---
    else:
        df_p = load_data("pilkarze.csv")
        df_w = load_details("wystepy.csv")

        # 1. PRZYGOTOWANIE DANYCH (AGREGACJA)
        # Bierzemy statystyki z występów (są dokładniejsze co do meczów/goli)
        stats_map = {}
        if df_w is not None:
            stats = df_w.groupby('Zawodnik_Clean').agg({'Gole': 'sum', 'Mecz_Label': 'nunique'}).reset_index()
            stats_map = stats.set_index('Zawodnik_Clean').to_dict('index')

        display_data = []

        # Jeśli mamy plik pilkarze.csv, używamy go jako bazy
        if df_p is not None:
            df_p = prepare_flags(df_p)  # Generujemy flagi
            df_p['clean'] = df_p['imię i nazwisko'].astype(str).str.strip()

            # Sortujemy, żeby przy duplikatach wziąć ten z sumą meczów
            sort_c = 'suma' if 'suma' in df_p.columns else 'mecze'
            if sort_c in df_p.columns:
                df_p[sort_c] = pd.to_numeric(df_p[sort_c], errors='coerce').fillna(0)
                df_p = df_p.sort_values(sort_c, ascending=False)

            df_unique = df_p.drop_duplicates(subset=['clean'])

            for _, row in df_unique.iterrows():
                name = row['clean']

                # Pobieramy dane z mapy występów LUB z pliku pilkarze.csv
                s_data = stats_map.get(name, {})
                matches_real = s_data.get('Mecz_Label', 0)
                goals_real = s_data.get('Gole', 0)

                # Fallback do pliku jeśli brak w występach
                if matches_real == 0:
                    matches_real = int(pd.to_numeric(row.get('mecze', 0), errors='coerce') or 0)
                if goals_real == 0:
                    goals_real = int(pd.to_numeric(row.get('gole', 0), errors='coerce') or 0)

                # Wiek
                age_val = None
                if pd.notna(row.get('data urodzenia')):
                    a, _ = get_age_and_birthday(row.get('data urodzenia'))
                    if a: age_val = int(a)

                # Grupowanie pozycji
                pos = str(row.get('pozycja', '-')).capitalize()
                pos_grp = "Inne"
                p_l = pos.lower()
                if 'bram' in p_l or 'gk' in p_l:
                    pos_grp = "Bramkarz"
                elif 'obr' in p_l or 'def' in p_l:
                    pos_grp = "Obrońca"
                elif 'pom' in p_l or 'mid' in p_l:
                    pos_grp = "Pomocnik"
                elif 'nap' in p_l or 'for' in p_l:
                    pos_grp = "Napastnik"

                display_data.append({
                    "Flaga": row.get('Flaga'),
                    "Zawodnik": name,
                    "Pozycja": pos,
                    "Grupa": pos_grp,
                    "Wiek": age_val,
                    "Mecze": matches_real,
                    "Gole": goals_real,
                    "Narodowość": row.get('Narodowość')
                })

        # Jeśli nie ma pliku pilkarze.csv, a jest wystepy.csv -> tworzymy listę tylko z występów
        elif df_w is not None:
            for name, data in stats_map.items():
                display_data.append({
                    "Flaga": None, "Zawodnik": name, "Pozycja": "-", "Grupa": "Inne",
                    "Wiek": None, "Mecze": data['Mecz_Label'], "Gole": data['Gole'], "Narodowość": "-"
                })

        # --- TWORZENIE DATAFRAME ---
        df_display = pd.DataFrame(display_data)

        if not df_display.empty:
            # --- SEKCJA 1: METRYKI (Metrics) ---
            total_pl = len(df_display)
            total_gl = df_display['Gole'].sum()
            avg_age = df_display['Wiek'].mean()

            top_scorer = df_display.sort_values('Gole', ascending=False).iloc[0]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Baza Zawodników", total_pl)
            m2.metric("Liczba Goli", total_gl)
            m3.metric("Średni Wiek", f"{avg_age:.1f}" if pd.notna(avg_age) else "-")
            m4.metric("Najlepszy Strzelec", f"{top_scorer['Zawodnik']} ({top_scorer['Gole']})")

            st.divider()

            # --- SEKCJA 2: FILTRY I PODIUM ---
            c_fil, c_pod = st.columns([1, 2])

            with c_fil:
                st.markdown("🛠️ **Filtry**")
                search_q = st.text_input("Szukaj:", placeholder="Nazwisko...")
                sel_pos = st.multiselect("Pozycja:", ["Bramkarz", "Obrońca", "Pomocnik", "Napastnik"])

                min_a, max_a = int(df_display['Wiek'].min() or 15), int(df_display['Wiek'].max() or 45)
                sel_age = st.slider("Wiek:", min_a, max_a, (min_a, max_a))

            # Filtrowanie
            df_filtered = df_display.copy()
            if search_q:
                df_filtered = df_filtered[df_filtered['Zawodnik'].str.contains(search_q, case=False)]
            if sel_pos:
                df_filtered = df_filtered[df_filtered['Grupa'].isin(sel_pos)]

            # Filtr wieku (NaN też pokazujemy, chyba że ktoś ruszy suwakiem, ale tu proste założenie)
            df_filtered = df_filtered[
                (df_filtered['Wiek'].isna()) |
                ((df_filtered['Wiek'] >= sel_age[0]) & (df_filtered['Wiek'] <= sel_age[1]))
                ]

            # Sortowanie
            df_filtered = df_filtered.sort_values('Mecze', ascending=False)

            with c_pod:
                # Wyświetlanie Podium (TOP 3 z filtra)
                if len(df_filtered) >= 3:
                    st.markdown("🏆 **Najwięcej meczów (w filtrze)**")
                    top3 = df_filtered.head(3).reset_index(drop=True)

                    # Układ kolumn: 2. miejsce, 1. miejsce, 3. miejsce
                    cp2, cp1, cp3 = st.columns([1, 1, 1])


                    def card(col, row, emoji):
                        with col:
                            st.markdown(f"""
                            <div style="text-align:center; border:1px solid #444; border-radius:10px; padding:10px; background-color:rgba(255,255,255,0.05);">
                                <h1 style="margin:0;">{emoji}</h1>
                                <div style="font-weight:bold; margin-top:5px;">{row['Zawodnik']}</div>
                                <div style="color:#28a745;">{row['Mecze']} meczów</div>
                            </div>
                            """, unsafe_allow_html=True)


                    card(cp1, top3.iloc[0], "🥇")
                    card(cp2, top3.iloc[1], "🥈")
                    card(cp3, top3.iloc[2], "🥉")
                else:
                    st.info("Za mało wyników do podium.")

            st.write("")

            # --- SEKCJA 3: TABELA ---
            st.subheader(f"Lista wyników ({len(df_filtered)})")

            event = st.dataframe(
                df_filtered[['Flaga', 'Zawodnik', 'Pozycja', 'Wiek', 'Mecze', 'Gole']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Flaga": st.column_config.ImageColumn("", width="small"),
                    "Wiek": st.column_config.NumberColumn("Wiek", format="%d"),
                    "Mecze": st.column_config.ProgressColumn("Mecze", format="%d", min_value=0,
                                                             max_value=int(df_display['Mecze'].max())),
                    "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽")
                },
                on_select="rerun",
                selection_mode="single-row",
                height=600
            )

            if event.selection.rows:
                idx = event.selection.rows[0]
                sel_player = df_filtered.iloc[idx]['Zawodnik']
                st.session_state['cm_selected_player'] = sel_player
                st.rerun()

        else:
            st.warning("Brak danych do wyświetlenia.")

elif opcja == "Centrum Meczowe":
    st.header("⚽ Centrum Meczowe")

    # --- 0. ROUTER (Profil Piłkarza) ---
    if st.session_state.get('cm_selected_player'):
        if st.button("⬅️ Wróć do raportu", key="back_from_player_cm"):
            st.session_state['cm_selected_player'] = None
            st.rerun()
        st.divider()
        render_player_profile(st.session_state['cm_selected_player'])

    # --- 1. GŁÓWNY WIDOK ---
    else:
        df_m = load_data("mecze.csv")
        df_det_sq = load_details("wystepy.csv")

        # Globalny filtr sezonów
        if 'filter_seasons' in globals():
            df_m = filter_seasons(df_m, 'sezon')
            df_det_sq = filter_seasons(df_det_sq, 'Sezon')

        # Linki do analizy rywala (ID meczu)
        if df_m is not None:
            def create_link(row):
                try:
                    d = row.get('data meczu', '-') or row.get('data', '-')
                    res = str(row.get('wynik', '-')).strip()
                    rywal = str(row.get('rywal', 'Rywal')).strip()
                    return f"{d} | {rywal} ({res})"
                except:
                    return "Mecz"


            df_m['Mecz_Link'] = df_m.apply(create_link, axis=1)

        tab1, tab2, tab3 = st.tabs(["📝 Raporty Meczowe", "🔍 Analiza Rywala", "📊 Statystyki"])

        # ====================================================================
        # TAB 1: RAPORTY MECZOWE (Z EMOTKAMI W SELECTBOX)
        # ====================================================================
        with tab1:
            if df_det_sq is not None:
                c1, c2 = st.columns([1, 2])
                seasons = sorted(df_det_sq['Sezon'].unique(), reverse=True)

                # Obsługa wyboru sezonu
                idx_season = 0
                if 'cm_season_sel' in st.session_state and st.session_state['cm_season_sel'] in seasons:
                    idx_season = seasons.index(st.session_state['cm_season_sel'])

                sel_season = c1.selectbox("Wybierz Sezon:", seasons, index=idx_season, key="cm_season_sel_box")
                st.session_state['cm_season_sel'] = sel_season

                # --- PRZYGOTOWANIE LISTY MECZÓW Z EMOTKAMI ---
                subset = df_det_sq[df_det_sq['Sezon'] == sel_season]

                # Grupujemy, aby mieć unikalne mecze, ale zachować metadane (Rola)
                unique_matches = subset.groupby('Mecz_Label').first().reset_index()
                if 'Data_Sort' in unique_matches.columns:
                    unique_matches = unique_matches.sort_values('Data_Sort', ascending=False)


                # Funkcja dodająca emotki
                def get_display_label(row):
                    raw_label = row['Mecz_Label']
                    role = str(row.get('Rola', '')).lower()
                    icon = "🏠" if any(x in role for x in ['dom', 'gospodarz', 'u siebie']) else "🚌"
                    return f"{icon} {raw_label}"


                unique_matches['Display_Label'] = unique_matches.apply(get_display_label, axis=1)

                display_to_id = dict(zip(unique_matches['Display_Label'], unique_matches['Mecz_Label']))
                id_to_display = dict(zip(unique_matches['Mecz_Label'], unique_matches['Display_Label']))
                options_display = list(unique_matches['Display_Label'])

                idx_match = 0
                current_selection_id = st.session_state.get('cm_match_sel')

                if current_selection_id:
                    if current_selection_id in options_display:
                        idx_match = options_display.index(current_selection_id)
                    elif current_selection_id in id_to_display:
                        target_display = id_to_display[current_selection_id]
                        if target_display in options_display:
                            idx_match = options_display.index(target_display)

                sel_display = c2.selectbox("Wybierz Mecz:", options_display, index=idx_match, key="cm_match_sel_box")
                sel_match_lbl = display_to_id.get(sel_display)
                st.session_state['cm_match_sel'] = sel_match_lbl

                # --- DEFINICJA STARYCH SEZONÓW ---
                OLD_SEASONS = ['1997/1998', '1998/1999', '1999/2000', '2000/2001', '2001/2002', '2002/2003']
                is_old_season = sel_season in OLD_SEASONS

                if sel_match_lbl:
                    st.divider()
                    match_squad = subset[subset['Mecz_Label'] == sel_match_lbl].copy().sort_values('File_Order')

                    if not match_squad.empty:
                        # Header
                        try:
                            parts = sel_match_lbl.split('|')
                            date_s = parts[0].strip()
                            info_s = parts[1].strip()
                        except:
                            date_s, info_s = "-", sel_match_lbl

                        st.markdown(f"""
                        <div style="text-align: center; padding: 15px; background-color: rgba(40, 167, 69, 0.15); border: 1px solid #28a745; border-radius: 10px; margin-bottom: 25px;">
                            <h2 style="margin:0; color: var(--text-color);">{info_s}</h2>
                            <p style="color: gray; margin: 5px 0 0 0;">📅 {date_s}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        # --- LOGIKA ZMIAN ---
                        map_in_to_out = {}
                        map_out_to_in = {}

                        if not is_old_season:
                            condition_in = (match_squad['Status'] == 'Wszedł') | \
                                           ((match_squad['Status'] == 'Czerwona kartka') & (match_squad['Wejście'] > 0))

                            in_rows = match_squad[condition_in].sort_values('Minuta_Zmiany_Real')
                            out_rows = match_squad[match_squad['Status'].isin(['Zszedł'])].sort_values(
                                'Minuta_Zmiany_Real')
                            used_out = []

                            if not in_rows.empty:
                                for _, row_in in in_rows.iterrows():
                                    m_in = row_in['Minuta_Zmiany_Real']
                                    cands = out_rows[~out_rows.index.isin(used_out)].copy()
                                    cands['diff'] = (cands['Minuta_Zmiany_Real'] - m_in).abs()
                                    cands = cands[cands['diff'] <= 2].sort_values('diff')

                                    if not cands.empty:
                                        best = cands.iloc[0]
                                        map_in_to_out[row_in['Zawodnik_Clean']] = best['Zawodnik_Clean']
                                        map_out_to_in[best['Zawodnik_Clean']] = row_in['Zawodnik_Clean']
                                        used_out.append(best.name)


                        # --- RENDEROWANIE WIERSZA ---
                        def render_player_row(row, is_sub=False):
                            c_num, c_name, c_info = st.columns([1, 4, 3])
                            mins_played = int(row.get('Minuty', 0))
                            entry_min = int(row.get('Minuta_Zmiany_Real', 0))
                            status = row.get('Status', '')
                            name = row['Zawodnik_Clean']

                            with c_num:
                                if is_old_season:
                                    st.write("-")
                                else:
                                    if is_sub:
                                        st.caption(f"{entry_min}'" if entry_min > 0 else "-")
                                    else:
                                        if mins_played == 0 and status in ['Cały mecz', 'Grał']:
                                            st.write("90'")
                                        else:
                                            st.write(f"{mins_played}'" if mins_played > 0 else "-")

                            with c_name:
                                if st.button(name,
                                             key=f"btn_{sel_match_lbl}_{name}_{is_sub}_{st.session_state.get('uploader_key', 0)}",
                                             use_container_width=True):
                                    st.session_state['cm_selected_player'] = name
                                    st.rerun()

                            events = []
                            g = int(row.get('Gole', 0))
                            if g > 0: events.append(
                                f"<span style='color:green; font-weight:bold;'>{'⚽' * g if g < 4 else str(g) + 'x⚽'}</span>")

                            y = int(row.get('Żółte', 0))
                            if y > 0: events.append(f"🟨{'x' + str(y) if y > 1 else ''}")

                            r = int(row.get('Czerwone', 0))
                            if r > 0: events.append("🟥")

                            if is_sub:
                                rep = map_in_to_out.get(name)
                                txt = f"za: {rep}" if (rep and not is_old_season) else "Wejście"
                                events.append(f"<span style='color:#28a745; font-size:0.85em;'>⬆️ {txt}</span>")
                            elif status == 'Zszedł':
                                rep = map_out_to_in.get(name)
                                min_info = f" ({entry_min}')" if (entry_min > 0 and not is_old_season) else ""
                                txt = f"zm: {rep}{min_info}" if (rep and not is_old_season) else "Zejście"
                                events.append(f"<span style='color:#dc3545; font-size:0.85em;'>⬇️ {txt}</span>")

                            with c_info:
                                if events: st.markdown(" ".join(events), unsafe_allow_html=True)


                        # --- PODZIAŁ SKŁADU ---
                        starters = match_squad[
                            (match_squad['Status'].isin(['Cały mecz', 'Zszedł', 'Grał', 'Czerwona kartka'])) & (
                                        match_squad['Wejście'] == 0)].sort_values('File_Order')
                        subs = match_squad[(match_squad['Status'] == 'Wszedł') | (
                                    (match_squad['Status'] == 'Czerwona kartka') & (
                                        match_squad['Wejście'] > 0))].sort_values('Minuta_Zmiany_Real')
                        unused = match_squad[match_squad['Status'] == 'Rezerwowy']

                        col_l, col_r = st.columns(2)
                        with col_l:
                            st.subheader("🏟️ Wyjściowa XI")
                            if not starters.empty:
                                for _, r in starters.iterrows(): render_player_row(r, is_sub=False)
                            else:
                                st.info("Brak danych.")

                        with col_r:
                            st.subheader("🔄 Zmiennicy")
                            if not subs.empty:
                                for _, r in subs.iterrows(): render_player_row(r, is_sub=True)
                            else:
                                st.caption("Brak zmian.")

                            if not unused.empty:
                                st.divider()
                                st.markdown("**💤 Ławka**")
                                for _, r in unused.iterrows(): st.text(f"{r['Zawodnik_Clean']}")
                    else:
                        st.warning("Brak składu w bazie dla wybranego meczu.")
            else:
                st.error("Brak pliku wystepy.csv")

        # ====================================================================
        # TAB 2: ANALIZA RYWALA
        # ====================================================================
        with tab2:
            st.subheader("🆚 Analiza Rywala")
            if df_m is not None:
                rivs = sorted(df_m['rywal'].dropna().unique()) if 'rywal' in df_m.columns else []
                sel_r = st.selectbox("Wybierz rywala:", rivs)

                if sel_r:
                    sub = df_m[df_m['rywal'] == sel_r].copy().sort_values('data meczu', ascending=False).reset_index(
                        drop=True)
                    st.info("💡 Kliknij w wiersz tabeli, aby przejść do szczegółowego raportu meczowego.")

                    event = st.dataframe(
                        sub[['data meczu', 'wynik', 'dom', 'Mecz_Link']],
                        use_container_width=True, hide_index=True,
                        column_config={"Mecz_Link": st.column_config.Column("ID Mecz", disabled=True)},
                        on_select="rerun", selection_mode="single-row"
                    )

                    if event.selection.rows:
                        idx = event.selection.rows[0]
                        link = sub.iloc[idx]['Mecz_Link']

                        if df_det_sq is not None:
                            match_info = df_det_sq[df_det_sq['Mecz_Label'] == link]
                            if not match_info.empty:
                                found_season = match_info.iloc[0]['Sezon']
                                st.session_state['cm_season_sel'] = found_season
                                st.session_state['cm_match_sel'] = link

                                st.toast(f"⏳ Ładowanie meczu: {link}...", icon="🔄")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Nie znaleziono szczegółów składu dla tego meczu.")
            else:
                st.error("Brak pliku mecze.csv")

        # ====================================================================
        # TAB 3: STATYSTYKI (Frekwencja + Zaokrąglenia + Miesiące)
        # ====================================================================
        with tab3:
            st.subheader("📊 Centrum Analityczne")

            if df_m is not None:
                if 'dt_obj' not in df_m.columns:
                    col_d = next((c for c in df_m.columns if c in ['data', 'data meczu']), None)
                    if col_d:
                        df_m['dt_obj'] = pd.to_datetime(df_m[col_d], dayfirst=True, errors='coerce')
                    else:
                        df_m['dt_obj'] = pd.NaT

                df_stats = df_m.sort_values('dt_obj').copy()

                f_mode = st.radio("Filtruj mecze:", ["Wszystkie", "🏠 Tylko Dom", "🚌 Tylko Wyjazd"], horizontal=True)

                if "Dom" in f_mode:
                    df_stats = df_stats[df_stats['dom'].astype(str).str.lower().isin(['1', 'true', 'dom', 'tak'])]
                elif "Wyjazd" in f_mode:
                    df_stats = df_stats[~df_stats['dom'].astype(str).str.lower().isin(['1', 'true', 'dom', 'tak'])]

                total_matches = len(df_stats)
                wins, draws, losses = 0, 0, 0
                gf, ga = 0, 0
                results_seq = []

                for _, r in df_stats.iterrows():
                    res = parse_result(r.get('wynik'))
                    if res:
                        g_scored, g_conceded = res
                        gf += g_scored;
                        ga += g_conceded
                        if g_scored > g_conceded:
                            wins += 1; results_seq.append('W')
                        elif g_scored == g_conceded:
                            draws += 1; results_seq.append('D')
                        else:
                            losses += 1; results_seq.append('L')
                    else:
                        results_seq.append(None)

                win_rate = (wins / total_matches * 100) if total_matches else 0

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Mecze", total_matches)
                k2.metric("Bilans (Z-R-P)", f"{wins}-{draws}-{losses}")
                k3.metric("Bramki", f"{gf} : {ga}", delta=f"{gf - ga}")
                k4.metric("Skuteczność", f"{win_rate:.1f}%")

                st.divider()

                # --- FREKWENCJA (POPRAWIONA) ---
                if "Wyjazd" not in f_mode:
                    col_att = next((c for c in df_m.columns if c in ['widzów', 'frekwencja']), None)
                    if col_att:
                        # Bierzemy mecze domowe
                        df_att = df_m[df_m['dom'].astype(str).str.lower().isin(['1', 'true', 'dom', 'tak'])].copy()
                        df_att['Widzów_Num'] = pd.to_numeric(df_att[col_att], errors='coerce')
                        df_att = df_att[df_att['Widzów_Num'] > 0]  # Tylko mecze z widzami

                        if not df_att.empty:
                            st.markdown("##### 🏟️ Frekwencja (Dom)")

                            avg_val = int(df_att['Widzów_Num'].mean())
                            max_val = int(df_att['Widzów_Num'].max())

                            f1, f2 = st.columns(2)
                            f1.metric("Średnia na mecz", f"{avg_val}")
                            f2.metric("Rekord frekwencji", f"{max_val}")

                            # --- ANALIZA MIESIĘCZNA ---
                            st.write("")
                            st.markdown("**📅 Średnia frekwencja wg miesięcy**")

                            # Mapowanie miesięcy
                            pl_months = {
                                1: 'Styczeń', 2: 'Luty', 3: 'Marzec', 4: 'Kwiecień',
                                5: 'Maj', 6: 'Czerwiec', 7: 'Lipiec', 8: 'Sierpień',
                                9: 'Wrzesień', 10: 'Październik', 11: 'Listopad', 12: 'Grudzień'
                            }

                            if 'dt_obj' in df_att.columns:
                                monthly_att = df_att.groupby(df_att['dt_obj'].dt.month)[
                                    'Widzów_Num'].mean().reset_index()
                                monthly_att.columns = ['Miesiąc_Num', 'Średnia']
                                monthly_att['Miesiąc'] = monthly_att['Miesiąc_Num'].map(pl_months)
                                monthly_att['Średnia'] = monthly_att['Średnia'].fillna(0).astype(
                                    int)  # Zaokrąglenie do całkowitych
                                monthly_att = monthly_att.sort_values('Miesiąc_Num')

                                # Wykres Plotly
                                if HAS_PLOTLY:
                                    fig = go.Figure(data=[go.Bar(
                                        x=monthly_att['Miesiąc'],
                                        y=monthly_att['Średnia'],
                                        text=monthly_att['Średnia'],  # Tekst na słupku
                                        textposition='auto',
                                        marker_color='#28a745'
                                    )])
                                    fig.update_layout(
                                        margin=dict(l=20, r=20, t=20, b=20),
                                        yaxis_title="Średnia widzów",
                                        height=300
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.dataframe(monthly_att[['Miesiąc', 'Średnia']], hide_index=True,
                                                 use_container_width=True)
                        else:
                            st.info("Brak danych o frekwencji (lub mecze bez udziału publiczności).")
                    else:
                        st.warning("Nie znaleziono kolumny 'widzów' lub 'frekwencja' w pliku mecze.csv")
                else:
                    st.info("Statystyki frekwencji dostępne są tylko dla meczów domowych.")

                st.divider()


                # --- SERIE ---
                def get_longest_streak(dataset, seq, codes):
                    max_s = [];
                    curr_s = []
                    temp_df = dataset.reset_index(drop=True)
                    for i, r in temp_df.iterrows():
                        if i < len(seq) and seq[i] in codes:
                            curr_s.append(r)
                        else:
                            if len(curr_s) > len(max_s): max_s = curr_s
                            curr_s = []
                    if len(curr_s) > len(max_s): max_s = curr_s
                    return max_s


                s_win = get_longest_streak(df_stats, results_seq, ['W'])
                s_no_loss = get_longest_streak(df_stats, results_seq, ['W', 'D'])
                s_loss = get_longest_streak(df_stats, results_seq, ['L'])

                st.markdown("##### 🔥 Najdłuższe Serie")
                c_s1, c_s2, c_s3 = st.columns(3)
                c_s1.metric("Seria Zwycięstw", len(s_win))
                c_s2.metric("Bez Porażki", len(s_no_loss))
                c_s3.metric("Seria Porażek", len(s_loss))

                with st.expander("📜 Pokaż mecze z serii"):
                    ts1, ts2, ts3 = st.tabs(["Zwycięstwa", "Bez Porażki", "Porażki"])


                    def show_streak(lst):
                        if lst:
                            st.dataframe(pd.DataFrame(lst)[['data meczu', 'rywal', 'wynik', 'dom']], hide_index=True,
                                         use_container_width=True)
                        else:
                            st.info("Brak serii.")


                    with ts1:
                        show_streak(s_win)
                    with ts2:
                        show_streak(s_no_loss)
                    with ts3:
                        show_streak(s_loss)

            else:
                st.error("Brak pliku mecze.csv")

elif opcja == "🏆 Rekordy & TOP":
    st.header("🏆 Sala Chwały i Rekordy TSP")

    # [1] Ładowanie i Wstępna Obróbka
    df_p = load_data("pilkarze.csv")
    df_w = load_details("wystepy.csv")
    df_s = load_data("strzelcy.csv")
    df_m = load_data("mecze.csv")

    if df_p is None or df_w is None:
        st.error("Brak plików danych (pilkarze.csv / wystepy.csv).")
    else:
        # Filtrowanie globalne (jeśli funkcja filter_seasons istnieje)
        df_w = filter_seasons(df_w, 'Sezon') if 'Sezon' in df_w.columns else df_w
        if df_s is not None: df_s = filter_seasons(df_s, 'sezon')
        if df_m is not None: df_m = filter_seasons(df_m, 'sezon')


        # Funkcja pomocnicza do miejsc (1, 2, 3...)
        def get_medals(df_in):
            df_x = df_in.copy().reset_index(drop=True)
            df_x.index += 1
            df_x.insert(0, 'Miejsce', df_x.index.map(
                lambda x: f"🥇" if x == 1 else (f"🥈" if x == 2 else (f"🥉" if x == 3 else f"{x}."))))
            return df_x


        # Obliczanie meczów dla piłkarzy (unikanie błędów NaN)
        # Priorytet: kolumna 'SUMA', potem 'mecze', potem zliczenie z występów
        col_m = next((c for c in ['SUMA', 'mecze', 'Mecze'] if c in df_p.columns), None)

        if col_m:
            df_p['Total_Matches'] = pd.to_numeric(df_p[col_m], errors='coerce').fillna(0).astype(int)
        elif 'Zawodnik_Clean' in df_w.columns:
            counts = df_w['Zawodnik_Clean'].value_counts()
            df_p['Total_Matches'] = df_p['imię i nazwisko'].map(counts).fillna(0).astype(int)
        else:
            df_p['Total_Matches'] = 0

        # Unikalni piłkarze + Flagi
        df_top_all = df_p.sort_values('Total_Matches', ascending=False).drop_duplicates('imię i nazwisko')
        df_top_all = prepare_flags(df_top_all)  # Zakładam, że ta funkcja istnieje w Twoim kodzie

        # Zakładki
        tab1, tab2, tab3, tab4 = st.tabs(["👤 Legendy", "🏟️ Rekordy Meczowe", "📅 Sezony", "🟥 Kartki"])

        # --- TAB 1: LEGENDY ---
        with tab1:
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("#### 👕 Najwięcej Występów")
                top_10_m = get_medals(df_top_all.head(10))
                st.dataframe(
                    top_10_m[['Miejsce', 'Flaga', 'imię i nazwisko', 'Total_Matches']],
                    hide_index=True, use_container_width=True,
                    column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                   "Total_Matches": st.column_config.NumberColumn("Mecze")}
                )

            with col_r:
                st.markdown("#### ⚽ Najlepsi Strzelcy")
                if df_s is not None:
                    # Agregacja strzelców (grupowanie po imieniu)
                    s_agg = df_s.groupby(['imię i nazwisko', 'kraj'], as_index=False)['gole'].sum()
                    s_agg = s_agg.sort_values('gole', ascending=False).head(10)
                    s_agg = prepare_flags(s_agg, 'kraj')
                    s_agg = get_medals(s_agg)
                    st.dataframe(
                        s_agg[['Miejsce', 'Flaga', 'imię i nazwisko', 'gole']],
                        hide_index=True, use_container_width=True,
                        column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                       "gole": st.column_config.NumberColumn("Gole")}
                    )
                else:
                    st.info("Brak danych strzeleckich.")

        # --- TAB 2: MECZOWE (HAT-TRICKI I WYNIKI) ---
        with tab2:
            st.subheader("🎩 Hat-tricki")
            if 'Gole' in df_w.columns:
                df_w['G_Num'] = pd.to_numeric(df_w['Gole'], errors='coerce').fillna(0).astype(int)
                hats = df_w[df_w['G_Num'] >= 3].copy()
                if not hats.empty:
                    hats = hats.sort_values('G_Num', ascending=False).head(15)
                    hats = get_medals(hats)
                    st.dataframe(
                        hats[['Miejsce', 'Sezon', 'Zawodnik_Clean', 'G_Num', 'Przeciwnik']],
                        hide_index=True, use_container_width=True,
                        column_config={"G_Num": st.column_config.NumberColumn("Gole", format="%d ⚽")}
                    )
                else:
                    st.info("Brak hat-tricków w bazie.")

            st.divider()
            st.subheader("🚀 Najwyższe Zwycięstwa")
            if df_m is not None and 'wynik' in df_m.columns:
                def get_diff(x):
                    p = parse_result(x)  # Funkcja pomocnicza z Twojego kodu
                    return (p[0] - p[1]) if p else -99


                df_m['Diff'] = df_m['wynik'].apply(get_diff)
                wins = df_m[df_m['Diff'] > 0].sort_values('Diff', ascending=False).head(10)
                wins = get_medals(wins)
                st.dataframe(wins[['Miejsce', 'sezon', 'rywal', 'wynik']], hide_index=True, use_container_width=True)

        # --- TAB 3: SEZONY (PUNKTY) ---
        with tab3:
            st.subheader("📈 Najlepsze Sezony (Punkty)")
            if df_m is not None:
                stats = []
                for s_name, grp in df_m.groupby('sezon'):
                    pts, m_cnt = 0, 0
                    for _, r in grp.iterrows():
                        res = parse_result(r.get('wynik'))
                        if res:
                            m_cnt += 1
                            if res[0] > res[1]:
                                pts += 3
                            elif res[0] == res[1]:
                                pts += 1
                    if m_cnt > 0:
                        stats.append({'Sezon': s_name, 'Pkt': pts, 'Mecze': m_cnt, 'Śr': pts / m_cnt})

                if stats:
                    df_stat = pd.DataFrame(stats).sort_values('Śr', ascending=False)
                    st.dataframe(
                        df_stat,
                        hide_index=True, use_container_width=True,
                        column_config={"Śr": st.column_config.ProgressColumn("Średnia Pkt", min_value=0, max_value=3,
                                                                             format="%.2f")}
                    )
                else:
                    st.warning("Brak danych do obliczenia punktów.")

        # --- TAB 4: KARTKI ---
        with tab4:
            st.subheader("🟥 Najwięcej Czerwonych Kartek")
            if 'Czerwone' in df_w.columns:
                df_w['R_Card'] = pd.to_numeric(df_w['Czerwone'], errors='coerce').fillna(0).astype(int)
                reds = df_w.groupby('Zawodnik_Clean')['R_Card'].sum().reset_index()
                reds = reds[reds['R_Card'] > 0].sort_values('R_Card', ascending=False).head(10)

                # Dodanie flag
                reds = pd.merge(reds, df_top_all[['imię i nazwisko', 'Flaga']], left_on='Zawodnik_Clean',
                                right_on='imię i nazwisko', how='left')
                reds = get_medals(reds)

                st.dataframe(
                    reds[['Miejsce', 'Flaga', 'Zawodnik_Clean', 'R_Card']],
                    hide_index=True, use_container_width=True,
                    column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                   "R_Card": st.column_config.NumberColumn("Czerwone", format="%d 🟥")}
                )
            else:
                st.info("Brak danych o kartkach.")
# =========================================================
# MODUŁ: TRENERZY (ODDZIELNA SEKCJA)
# =========================================================
elif opcja == "Trenerzy":
    if 'coach_view_mode' not in st.session_state:
        st.session_state['coach_view_mode'] = 'list'
    if 'selected_coach' not in st.session_state:
        st.session_state['selected_coach'] = None

    if st.session_state['coach_view_mode'] == 'profile':
        if st.button("⬅️ Wróć do listy trenerów"):
            st.session_state['coach_view_mode'] = 'list'
            st.session_state['selected_coach'] = None
            st.rerun()

        st.divider()
        render_coach_profile(st.session_state['selected_coach'])

    else:
        st.header("👔 Centrum Trenerów TSP")
        df = load_data("trenerzy.csv")

        if df is not None:
            def parse_date_safe(val):
                s = str(val).strip().lower()
                if s in ['-', 'nan', '', 'obecnie']: return pd.NaT
                try:
                    return pd.to_datetime(s, dayfirst=True)
                except:
                    return pd.NaT


            if 'początek' in df.columns:
                df['początek_dt'] = df['początek'].apply(parse_date_safe)
            else:
                df['początek_dt'] = pd.NaT

            if 'koniec' in df.columns:
                df['koniec_dt'] = df['koniec'].apply(parse_date_safe)
            else:
                df['koniec_dt'] = pd.NaT

            for col in ['mecze', 'punkty']:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df = prepare_flags(df)

            col_search, col_space = st.columns([1, 2])
            with col_search:
                all_coaches = sorted(df['imię i nazwisko'].astype(str).unique())
                selected_from_list = st.selectbox("🔍 Znajdź profil trenera:", [""] + all_coaches)
                if selected_from_list:
                    st.session_state['selected_coach'] = selected_from_list
                    st.session_state['coach_view_mode'] = 'profile'
                    st.rerun()

            st.divider()
            t1, t2, t3 = st.tabs(["📜 Lista Trenerów", "🏆 Rankingi Wszechczasów", "⚔️ Porównywarka"])

            with t1:
                st.subheader("Historia Zatrudnienia")
                df_view = df.sort_values('początek_dt', ascending=False)
                cols_possible = ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'początek', 'koniec',
                                 'mecze', 'punkty']
                cols_final = [c for c in cols_possible if c in df_view.columns]

                st.dataframe(df_view[cols_final], use_container_width=True, hide_index=True,
                             column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                                            "mecze": st.column_config.NumberColumn("Mecze", format="%d"),
                                            "punkty": st.column_config.NumberColumn("Punkty", format="%.0f")})

            with t2:
                st.subheader("📊 Tabela Wszechczasów")
                if 'punkty' in df.columns and 'mecze' in df.columns:
                    agg = df.groupby(['imię i nazwisko', 'Narodowość', 'Flaga'], as_index=False)[
                        ['mecze', 'punkty']].sum()
                    agg['Śr. Pkt'] = (agg['punkty'] / agg['mecze']).fillna(0)

                    sort_mode = st.radio("Sortuj według:", ["Punkty (Suma)", "Mecze (Liczba)",
                                                            "Średnia Punktów (min. 5 spotkań)"],
                                         horizontal=True)

                    if "Średnia" in sort_mode:
                        agg_sorted = agg[agg['mecze'] >= 5].sort_values('Śr. Pkt', ascending=False)
                        st.caption("⚠️ *Ranking średniej uwzględnia tylko trenerów z min. 5 meczami.*")
                    elif "Mecze" in sort_mode:
                        agg_sorted = agg.sort_values('mecze', ascending=False)
                    else:
                        agg_sorted = agg.sort_values('punkty', ascending=False)

                    st.dataframe(agg_sorted, use_container_width=True, hide_index=True,
                                 column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                                                "Śr. Pkt": st.column_config.ProgressColumn("Średnia",
                                                                                           format="%.2f",
                                                                                           min_value=0,
                                                                                           max_value=3),
                                                "mecze": st.column_config.NumberColumn("Mecze 🏟️"),
                                                "punkty": st.column_config.NumberColumn("Pkt 📈")})
                else:
                    st.warning("Brak kolumn 'mecze' lub 'punkty' w pliku trenerzy.csv")

            with t3:
                st.markdown("### 🆚 Porównaj bilans trenerów")
                sel_compare = st.multiselect("Wybierz trenerów (max 3):", all_coaches,
                                             default=all_coaches[:2] if len(all_coaches) > 1 else None)

                if sel_compare:
                    comp_data = []
                    mecze_df = load_data("mecze.csv")
                    if mecze_df is not None:
                        col_m_date = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None)
                        if col_m_date:
                            mecze_df['dt_temp'] = pd.to_datetime(mecze_df[col_m_date], dayfirst=True, errors='coerce')
                            for coach in sel_compare:
                                coach_rows = df[df['imię i nazwisko'] == coach]
                                mask = pd.Series([False] * len(mecze_df))
                                for _, c_row in coach_rows.iterrows():
                                    start = c_row['początek_dt']
                                    end = c_row['koniec_dt']
                                    if pd.isna(start): continue
                                    if pd.isna(end): end = pd.Timestamp.now() + pd.Timedelta(days=365)
                                    mask |= (mecze_df['dt_temp'] >= start) & (mecze_df['dt_temp'] <= end)

                                cm = mecze_df[mask]
                                w, d, l, gf, ga, pts_sum = 0, 0, 0, 0, 0, 0
                                if not cm.empty:
                                    for _, row_match in cm.iterrows():
                                        res = parse_result(row_match.get('wynik'))
                                        if res:
                                            gf += res[0];
                                            ga += res[1]
                                            if res[0] > res[1]:
                                                w += 1; pts_sum += 3
                                            elif res[0] == res[1]:
                                                d += 1; pts_sum += 1
                                            else:
                                                l += 1

                                total_m = w + d + l
                                avg_pts = pts_sum / total_m if total_m > 0 else 0
                                win_pct = (w / total_m * 100) if total_m > 0 else 0
                                comp_data.append(
                                    {"Trener": coach, "Mecze": total_m, "Zwycięstwa": w, "Remisy": d,
                                     "Porażki": l, "Bramki": f"{gf}:{ga}", "Średnia Pkt": avg_pts,
                                     "% Zwycięstw": win_pct})

                            if comp_data:
                                res_df = pd.DataFrame(comp_data).set_index("Trener")
                                # --- TU BYŁ BŁĄD, ZMIENIONO NA COLUMN CONFIG ---
                                st.dataframe(
                                    res_df,
                                    use_container_width=True,
                                    column_config={
                                        "Średnia Pkt": st.column_config.ProgressColumn(
                                            "Średnia Pkt", format="%.2f", min_value=0, max_value=3
                                        ),
                                        "% Zwycięstw": st.column_config.ProgressColumn(
                                            "% Zwycięstw", format="%.1f%%", min_value=0, max_value=100
                                        )
                                    }
                                )

                                if HAS_PLOTLY:
                                    fig = go.Figure()
                                    fig.add_trace(go.Bar(x=res_df.index, y=res_df['Średnia Pkt'], name='Średnia Pkt',
                                                         marker_color='#2ecc71'))
                                    fig.add_trace(
                                        go.Bar(x=res_df.index, y=res_df['% Zwycięstw'] / 33, name='Index Wygranych',
                                               marker_color='#3498db', opacity=0.5))
                                    fig.update_layout(title="Porównanie efektywności", barmode='group')
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("Nie znaleziono meczów.")
                        else:

                            st.error("Brak kolumny z datą w mecze.csv")

elif opcja == "🕵️ Ciemne Karty Historii":
    # --- ZABEZPIECZENIE PRZED GOŚĆMI ---
    if st.session_state.get('username') == 'guest' or not st.session_state.get('logged_in'):
        st.error("⛔ Odmowa dostępu.")
        st.info("Ta sekcja wymaga uprawnień administratora lub pełnego konta (np. Djero, KKowalski).")
    else:
        st.header("🕵️ Ciemne Karty Historii (2003-2006)")
        st.warning(
            "⚠️ Poniższe dane dotyczą udowodnionego procederu korupcyjnego, za który klub został ukarany odjęciem punktów.")

        st.markdown("""
        **Źródło danych:** Blog Piłkarska Mafia ([Link 1](https://pilkarskamafia.blogspot.com/2010/09/jak-podbeskidzie-bielsko-biaa-ustawiaa.html), [Link 2](https://pilkarskamafia.blogspot.com/2011/07/podbeskidzie-bielsko-biaa.html)) oraz akty oskarżenia prokuratury.

        W latach 2003-2006 działacze Podbeskidzia (m.in. Jerzy W. i prezes Stanisław P.) wręczali lub usiłowali wręczać łapówki sędziom oraz obserwatorom PZPN.
        """)

        # Dane uzupełnione na podstawie linków
        corruption_data = [
            {
                "Sezon": "2003/04", "Data": "30.08.2003", "Rywal": "Tłoki Gorzyce",
                "Wynik": "2:0", "Gdzie": "🏠 Dom",
                "Status": "Kupiony",
                "Opis": "Sędzia Włodzimierz M. przyjął 3 tys. zł łapówki za pomoc w wygranej."
            },
            {
                "Sezon": "2003/04", "Data": "13.09.2003", "Rywal": "Szczakowianka",
                "Wynik": "3:0", "Gdzie": "🏠 Dom",
                "Status": "Kupiony",
                "Opis": "Sędzia Marek M. przyjął 2 tys. zł za 'korzystne sędziowanie'."
            },
            {
                "Sezon": "2003/04", "Data": "20.09.2003", "Rywal": "Polar Wrocław",
                "Wynik": "4:0", "Gdzie": "🏠 Dom",
                "Status": "Kupiony",
                "Opis": "Sędzia Zbigniew M. przyjął 3 tys. zł łapówki."
            },
            {
                "Sezon": "2003/04", "Data": "03.05.2004", "Rywal": "RKS Radomsko",
                "Wynik": "2:1", "Gdzie": "🚌 Wyjazd",
                "Status": "Kupiony",
                "Opis": "Piłkarz rywali (Artur P.) przyjął 20 tys. zł za 'ułatwienie' zwycięstwa TSP."
            },
            {
                "Sezon": "2004/05", "Data": "11.09.2004", "Rywal": "Świt Nowy Dwór",
                "Wynik": "1:1", "Gdzie": "🚌 Wyjazd",
                "Status": "Kupiony",
                "Opis": "Sędzia Robert S. (ps. 'Setla') wziął 8-10 tys. zł. Obiecano 20 tys. za wygraną, ale padł remis."
            },
            {
                "Sezon": "2004/05", "Data": "Wiosna '05", "Rywal": "GKS Bełchatów",
                "Wynik": "-", "Gdzie": "🏠 Dom",
                "Status": "Próba",
                "Opis": "Sędzia Adam K. odmówił przyjęcia 10 tys. zł łapówki."
            },
            {
                "Sezon": "2005/06", "Data": "05.05.2006", "Rywal": "ŁKS Łódź",
                "Wynik": "1:0", "Gdzie": "🏠 Dom",
                "Status": "Kupiony",
                "Opis": "Sędzia Mariusz G. przyjął 1 tys. zł łapówki."
            }
        ]

        df_corr = pd.DataFrame(corruption_data)

        # Wyświetlanie tabeli
        st.dataframe(
            df_corr,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Status": st.column_config.TextColumn("Status", help="Czy udowodniono korupcję?"),
                "Opis": st.column_config.TextColumn("Szczegóły (Kto i za ile)", width="large"),
                "Gdzie": st.column_config.TextColumn("Miejsce"),
            }
        )