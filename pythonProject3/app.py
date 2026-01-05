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

    # Przygotowanie danych (unikamy duplikatów przy wyświetlaniu profilu)
    sort_col = 'suma' if 'suma' in df_uv.columns else ('mecze' if 'mecze' in df_uv.columns else None)

    if sort_col:
        df_uv[sort_col] = pd.to_numeric(df_uv[sort_col], errors='coerce').fillna(0)
        df_uv_sorted = df_uv.sort_values(sort_col, ascending=False).drop_duplicates(subset=['imię i nazwisko'])
    else:
        df_uv_sorted = df_uv.drop_duplicates(subset=['imię i nazwisko'])

    # [WAŻNE] Tu tworzymy wersję z flagami, której użyjemy później
    df_uv_sorted = prepare_flags(df_uv_sorted)

    if player_name not in df_uv_sorted['imię i nazwisko'].values:
        st.warning(f"Nie znaleziono profilu: {player_name}")
        return

    row = df_uv_sorted[df_uv_sorted['imię i nazwisko'] == player_name].iloc[0]

    # Pobranie daty urodzenia
    col_b = next((c for c in row.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
    birth_date = None
    age_info, is_bday = "-", False

    if col_b:
        birth_date = pd.to_datetime(row[col_b], errors='coerce')
        a, is_bday = get_age_and_birthday(row[col_b])
        if a: age_info = f"{a} lat"

    if is_bday: st.balloons(); st.success(f"🎉🎂 {player_name} kończy dzisiaj {age_info}! 🎂🎉")

    # --- ODZNAKI ---
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

    # --- DATY DEBIUTU I OSTATNIEGO MECZU ---
    debut_txt = "-"
    last_txt = "-"

    if df_det_goals is not None:
        p_hist = df_det_goals[df_det_goals['Zawodnik_Clean'] == player_name]
        if not p_hist.empty and 'Data_Sort' in p_hist.columns:
            p_hist = p_hist.sort_values('Data_Sort', ascending=True)

            # Debiut
            first_match = p_hist.iloc[0]
            d_date_obj = first_match['Data_Sort']
            d_date = d_date_obj.strftime('%d.%m.%Y') if pd.notna(d_date_obj) else "-"
            d_opp = first_match.get('Przeciwnik', '')
            d_age = calculate_exact_age_str(birth_date, d_date_obj) if birth_date is not None else ""
            debut_txt = f"{d_date} vs {d_opp}\n{d_age}"

            # Ostatni mecz
            last_match = p_hist.iloc[-1]
            l_date_obj = last_match['Data_Sort']
            l_date = l_date_obj.strftime('%d.%m.%Y') if pd.notna(l_date_obj) else "-"
            l_opp = last_match.get('Przeciwnik', '')
            l_age = calculate_exact_age_str(birth_date, l_date_obj) if birth_date is not None else ""
            last_txt = f"{l_date} vs {l_opp}\n{l_age}"

    # A. NAGŁÓWEK
    c_p1, c_p2 = st.columns([1, 3])
    with c_p1:
        if 'Flaga' in row and pd.notna(row['Flaga']) and str(row['Flaga']) != 'nan':
            st.image(row['Flaga'], width=100)
        else:
            st.markdown("## 👤")

    with c_p2:
        st.markdown(f"## {player_name}")
        st.markdown(f"**Kraj:** {row.get('Narodowość', '-')} | **Poz:** {row.get('pozycja', '-')}")
        st.markdown(f"**Wiek:** {age_info}")

        hd1, hd2 = st.columns(2)
        hd1.info(f"🆕 **Debiut:**\n\n{debut_txt}")
        hd2.info(f"🏁 **Ostatni mecz:**\n\n{last_txt}")

    st.markdown("---")

    # B. Wykres i Statystyki
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

    if 'sezon' in p_stats.columns:
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            if not p_stats.empty and p_stats['liczba'].sum() > 0:
                fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['liczba'], name='Mecze', marker_color='#3498db'))
                fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['Gole'], name='Gole', marker_color='#2ecc71'))
                fig.update_layout(title=f"Statystyki: {player_name}", barmode='group', height=350,
                                  margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{player_name}")
        except:
            pass

    # C. LISTA GOLI
    if df_det_goals is not None and 'Gole' in df_det_goals.columns:
        df_det_goals['Gole'] = pd.to_numeric(df_det_goals['Gole'], errors='coerce').fillna(0).astype(int)
        goals_df = df_det_goals[(df_det_goals['Zawodnik_Clean'] == player_name) & (df_det_goals['Gole'] > 0)].copy()

        if not goals_df.empty:
            if 'Data_Sort' in goals_df.columns: goals_df = goals_df.sort_values('Data_Sort', ascending=False)
            st.markdown("**Mecze z bramkami:**")
            st.dataframe(goals_df[['Sezon', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Gole']],
                         use_container_width=True, hide_index=True, column_config={
                    "Data_Sort": st.column_config.DateColumn("Data"),
                    "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽")
                })

    # D. SZCZEGÓŁOWA HISTORIA
    st.markdown("---")
    st.subheader("📜 Szczegółowa historia meczowa")

    if df_det_goals is not None:
        if 'Zawodnik_Clean' in df_det_goals.columns:
            player_history = df_det_goals[df_det_goals['Zawodnik_Clean'] == player_name].copy()
        else:
            player_history = pd.DataFrame()

        if not player_history.empty:
            if 'Data_Sort' in player_history.columns: player_history = player_history.sort_values('Data_Sort',
                                                                                                  ascending=False)

            pos_str = str(row.get('pozycja', '')).lower().strip()
            is_goalkeeper = (pos_str == 'bramkarz')

            if is_goalkeeper:
                def analyze_gk_row(r):
                    conceded = 0;
                    clean_sheet_icon = ""
                    w_str = str(r.get('Wynik', ''))
                    w_clean = w_str.split('(')[0].strip()
                    parts = re.split(r'[:\-]', w_clean)
                    if len(parts) >= 2:
                        try:
                            conceded = int(parts[1].strip())
                        except:
                            pass
                    mins = pd.to_numeric(r.get('Minuty'), errors='coerce')
                    if pd.isna(mins): mins = 0
                    if mins >= 46 and conceded == 0:
                        clean_sheet_icon = "🧱"
                    elif mins > 0:
                        clean_sheet_icon = "➖"
                    return pd.Series([conceded, clean_sheet_icon])

                player_history[['Wpuszczone', 'Czyste konto']] = player_history.apply(analyze_gk_row, axis=1)

            cols_base = ['Sezon', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Rola', 'Status', 'Minuty']
            cols_end = ['Żółte', 'Czerwone']
            target_cols = cols_base + (['Wpuszczone', 'Czyste konto'] if is_goalkeeper else ['Gole']) + cols_end
            cols_show = [c for c in target_cols if c in player_history.columns]

            st.dataframe(player_history[cols_show].reset_index(drop=True), use_container_width=True, hide_index=True,
                         column_config={
                             "Data_Sort": st.column_config.DatetimeColumn("Data", format="DD.MM.YYYY, HH:mm"),
                             "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                             "Wpuszczone": st.column_config.NumberColumn("Wpuszczone", format="%d ❌"),
                             "Minuty": st.column_config.NumberColumn("Minuty", format="%d'"),
                             "Żółte": st.column_config.NumberColumn("Żółte", format="%d 🟨"),
                             "Czerwone": st.column_config.NumberColumn("Czerwone", format="%d 🟥")
                         })

            # --- [POPRAWKA] E. NAJWIĘCEJ MECZÓW Z... (KOLEDZY) ---
            st.markdown("---")
            st.subheader("🤝 Najwięcej meczów z...")

            my_matches = player_history['Mecz_Label'].unique()
            teammates_rows = df_det_goals[df_det_goals['Mecz_Label'].isin(my_matches)]
            teammates_rows = teammates_rows[teammates_rows['Zawodnik_Clean'] != player_name]

            if not teammates_rows.empty:
                top_mates = teammates_rows['Zawodnik_Clean'].value_counts().head(10).reset_index()
                top_mates.columns = ['Kolega z zespołu', 'Wspólne Mecze']

                # [POPRAWKA] Używamy df_uv_sorted, który ma już kolumnę 'Flaga'
                df_flags_map = df_uv_sorted[['imię i nazwisko', 'Flaga']].drop_duplicates()
                top_mates = pd.merge(top_mates, df_flags_map, left_on='Kolega z zespołu', right_on='imię i nazwisko',
                                     how='left')

                # --- NOWOŚĆ: NUMERACJA I MEDALE ---
                top_mates.reset_index(drop=True, inplace=True)
                top_mates.index = top_mates.index + 1  # Numeracja od 1

                def get_rank_label(idx):
                    if idx == 1: return "🥇 1."
                    if idx == 2: return "🥈 2."
                    if idx == 3: return "🥉 3."
                    return f"{idx}."

                top_mates.insert(0, 'Miejsce', top_mates.index.map(get_rank_label))

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
        st.warning("Nie wczytano wystepy.csv")


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
        # Próba wczytania z różnymi kodowaniami
        try:
            df = pd.read_csv(filename, sep=';', encoding='utf-8')
        except:
            df = pd.read_csv(filename, sep=';', encoding='windows-1250')

        # --- 1. ZAPAMIĘTANIE KOLEJNOŚCI Z PLIKU ---
        df['File_Order'] = df.index

        # --- 2. UNIWERSALNE PARSOWANIE DATY (NAPRAWA REKORDÓW) ---
        PL_MONTHS = {
            'stycznia': '01', 'lutego': '02', 'marca': '03', 'kwietnia': '04',
            'maja': '05', 'czerwca': '06', 'lipca': '07', 'sierpnia': '08',
            'września': '09', 'października': '10', 'listopada': '11', 'grudnia': '12'
        }

        def smart_date_parser(val):
            if pd.isna(val) or val == '-': return pd.NaT
            s = str(val).strip().lower()

            # 1. Próba formatu polskiego (np. 20 maja 2024)
            for pl, num in PL_MONTHS.items():
                if pl in s:
                    s = s.replace(pl, num)
                    try:
                        return pd.to_datetime(s, dayfirst=True)
                    except:
                        pass
                    break

            # 2. Próba standardowych formatów (RRRR-MM-DD, DD.MM.RRRR)
            try:
                return pd.to_datetime(s, dayfirst=True)
            except:
                return pd.NaT

        if 'Data' in df.columns:
            df['Data_Sort'] = df['Data'].apply(smart_date_parser)
            # Wypełniamy puste daty (dla starych rekordów) minimalną datą, żeby nie znikały
            df['Data_Sort'] = df['Data_Sort'].fillna(pd.Timestamp('1900-01-01'))
            # Sortujemy, ale zachowujemy stabilność dla tego samego meczu
            df = df.sort_values(['Data_Sort', 'File_Order'], ascending=[False, True])

        # --- 3. CZYSZCZENIE DANYCH ---
        if 'Zawodnik' in df.columns:
            df['Zawodnik_Clean'] = df['Zawodnik'].astype(str).apply(
                lambda x: re.sub(r'^\s*\(\d+\)\s*', '', x).strip()
            )

        if 'Data' in df.columns and 'Przeciwnik' in df.columns:
            df['Mecz_Label'] = df['Data'] + " | " + df['Gospodarz'] + " - " + df['Gość'] + " (" + df['Wynik'] + ")"

        # --- 4. OBLICZANIE MINUT I GOLI (GWARANCJA LICZB) ---
        # Naprawa kolumny Gole (usuwa śmieci, zamienia na int)
        if 'Gole' in df.columns:
            df['Gole'] = pd.to_numeric(df['Gole'], errors='coerce').fillna(0).astype(int)

        if 'Minuty' in df.columns:
            df['Czas_Zdarzenia'] = pd.to_numeric(df['Minuty'], errors='coerce').fillna(0).astype(int)
        else:
            df['Czas_Zdarzenia'] = 0

        def process_match_stats(row):
            status = str(row.get('Status', '')).strip()
            val_csv = row['Czas_Zdarzenia']

            min_played = 0
            event_min = val_csv  # Domyślnie minuta z pliku

            if status == 'Cały mecz':
                min_played = 90
                event_min = 0
            elif status == 'Zszedł':
                min_played = val_csv
                event_min = val_csv
            elif status == 'Wszedł':
                calc = 90 - val_csv
                min_played = max(1, calc)
                event_min = val_csv
            elif status == 'Czerwona kartka':
                min_played = val_csv
                event_min = val_csv
            elif status == 'Grał':
                min_played = val_csv
                event_min = 0

            current_red = int(pd.to_numeric(row.get('Czerwone', 0), errors='coerce') or 0)
            if status == 'Czerwona kartka': current_red = 1
            if status == 'Zszedł': current_red = 0

            return pd.Series([min_played, event_min, current_red])

        df[['Minuty', 'Minuta_Zmiany_Calc', 'Czerwone']] = df.apply(process_match_stats, axis=1)

        return df
    except Exception as e:
        st.error(f"Błąd ładowania wystepy.csv: {e}")
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

# --- TO JEST BRAKUJĄCY FRAGMENT ---
opcja = st.sidebar.radio("Moduł:",
    ["Aktualny Sezon (25/26)", "Kalendarz", "Składy Historyczne", "Centrum Zawodników", "Centrum Meczowe", "🏆 Rekordy & TOP", "Trenerzy"]
)
# ----------------------------------

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
if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Kadra 2025/2026")
    df = load_data("25_26.csv")
    if df is not None:
        if 'status' in df.columns:
            df['is_youth'] = df['status'].astype(str).str.contains(r'\(M\)', case=False, regex=True)
            df.loc[df['is_youth'], 'imię i nazwisko'] = "Ⓜ️ " + df.loc[df['is_youth'], 'imię i nazwisko']

        # Konwersja kluczowych kolumn na liczby (dla pewności)
        numeric_cols_list = [
            'mecze', 'gole', 'asysty', 'kanadyjka', 'minuty', 'żółte kartki', 'czerwone kartki',
            'gole samobójcze', 'asysta 2. stopnia', 'wywalczony karny', 'sprokurowany karny',
            'karny', 'niestrzelony karny', 'główka', 'lewa', 'prawa', 'czyste konta', 'obronione karne'
        ]
        for col in numeric_cols_list:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        df = prepare_flags(df)

        # Sortowanie i Filtry
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            search_q = st.text_input("🔍 Szukaj:", placeholder="Nazwisko...")
        with c2:
            view_mode = st.selectbox("Widok:", ["Tabela Szczegółowa", "Podział na Formacje"])
        with c3:
            sort_by = st.selectbox("Sortuj:", ["Nr", "Mecze", "Gole", "Żółte Kartki", "Kanadyjka"], index=0)
        with c4:
            show_only_youth = st.checkbox("Młodzieżowcy", value=False)

        # Filtrowanie danych
        df_view = df.copy()
        if show_only_youth: df_view = df_view[df_view['is_youth']]
        if search_q: df_view = df_view[
            df_view.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]

        sort_map = {'Nr': 'numer', 'Mecze': 'mecze', 'Gole': 'gole', 'Żółte Kartki': 'żółte kartki',
                    'Kanadyjka': 'kanadyjka'}
        s_col = sort_map.get(sort_by, 'numer')
        if s_col in df_view.columns:
            asc = (s_col == 'numer')
            df_view = df_view.sort_values(s_col, ascending=asc)


        # --- DYNAMICZNE OBLICZANIE MAKSIMÓW DLA PASKÓW ---
        def get_max(col_name):
            if col_name in df.columns and not df[col_name].empty:
                val = df[col_name].max()
                return int(val) if val > 0 else 1
            return 1


        mx_mecze = get_max('mecze')
        mx_gole = get_max('gole')
        mx_asysty = get_max('asysty')
        mx_kan = get_max('kanadyjka')
        mx_min = get_max('minuty')

        # KONFIGURACJA KOLUMN Z DYNAMICZNYMI ZAKRESAMI
        col_config = {
            "Flaga": st.column_config.ImageColumn("Kraj", width="small"),
            "mecze": st.column_config.ProgressColumn("Mecze", format="%d", min_value=0, max_value=mx_mecze),
            "minuty": st.column_config.ProgressColumn("Minuty", format="%d'", min_value=0, max_value=mx_min),
            "gole": st.column_config.ProgressColumn("Gole", format="%d ⚽", min_value=0, max_value=mx_gole),
            "asysty": st.column_config.ProgressColumn("Asysty", format="%d 🅰️", min_value=0, max_value=mx_asysty),
            "kanadyjka": st.column_config.ProgressColumn("Kanadyjka", format="%d 🍁", min_value=0, max_value=mx_kan),

            # Kartki i inne (Liczbowe)
            "żółte kartki": st.column_config.NumberColumn("Żółte", format="%d 🟨"),
            "czerwone kartki": st.column_config.NumberColumn("Czerwone", format="%d 🟥"),
            "gole samobójcze": st.column_config.NumberColumn("Samobóje", format="%d 🔴"),
            "asysta 2. stopnia": st.column_config.NumberColumn("Asysty 2.st", format="%d 🅰️²"),
            "wywalczony karny": st.column_config.NumberColumn("Wywalczone K.", format="%d 🚑"),
            "sprokurowany karny": st.column_config.NumberColumn("Sprokurowane K.", format="%d 🦶"),
            "karny": st.column_config.NumberColumn("Gole z Karnych", format="%d 🥅"),
            "niestrzelony karny": st.column_config.NumberColumn("Zmarnowane K.", format="%d ❌"),
            "główka": st.column_config.NumberColumn("Głową", format="%d 🧠"),
            "lewa": st.column_config.NumberColumn("Lewą", format="%d 🦶"),
            "prawa": st.column_config.NumberColumn("Prawą", format="%d 🦶"),
            "czyste konta": st.column_config.NumberColumn("Czyste Konta", format="%d 🧱"),
            "obronione karne": st.column_config.NumberColumn("Obronione K.", format="%d 🧤")
        }

        # Wybór kolumn do wyświetlenia
        all_possible_cols = [
            'numer', 'imię i nazwisko', 'Flaga', 'pozycja', 'wiek', 'mecze', 'minuty', 'gole', 'asysty', 'kanadyjka',
            'żółte kartki', 'czerwone kartki', 'gole samobójcze', 'asysta 2. stopnia', 'wywalczony karny',
            'sprokurowany karny', 'karny', 'niestrzelony karny', 'główka', 'lewa', 'prawa', 'czyste konta',
            'obronione karne'
        ]
        final_cols = [c for c in all_possible_cols if c in df_view.columns]


        # --- STYLIZACJA (PODŚWIETLANIE LIDERÓW) ---
        def highlight_leaders(s):
            # Podświetla komórkę, jeśli jest równa maksymalnej wartości w kolumnie (i > 0)
            is_max = s == s.max()
            return ['background-color: rgba(255, 215, 0, 0.15)' if v and v == s.max() and v > 0 else '' for v in s]


        # Stosujemy styl do kolumn liczbowych w widoku
        cols_to_style = [c for c in final_cols if c in numeric_cols_list]

        if view_mode == "Tabela Szczegółowa":
            # Aplikujemy styl do całego dataframe
            styled_df = df_view[final_cols].style.apply(highlight_leaders, subset=cols_to_style)
            st.dataframe(styled_df, use_container_width=True, hide_index=True, column_config=col_config, height=600)
        else:
            if 'pozycja' in df_view.columns:
                unique_pos = sorted(df_view['pozycja'].astype(str).unique())
                for pos in unique_pos:
                    sub = df_view[df_view['pozycja'] == pos]
                    if not sub.empty:
                        st.markdown(f"### {pos}")
                        # Stylowanie podzbioru
                        styled_sub = sub[final_cols].style.apply(highlight_leaders, subset=cols_to_style)
                        st.dataframe(styled_sub, use_container_width=True, hide_index=True, column_config=col_config)
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

    # 3. WIDOK SZCZEGÓŁÓW MECZU (ULEPSZONY RAPORT)
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
            c3.metric("Miejsce", "Dom" if str(m_data.get('Dom')) in ['1', 'True'] else "Wyjazd")

        # --- SEKCJA STRZELCÓW (POPRAWIONA) ---
        scorers_str = m_data.get('Strzelcy', '-')
        if scorers_str and scorers_str != '-' and str(scorers_str).lower() != 'nan':
            st.markdown("### 🥅 Strzelcy")
            # Używamy helpera extract_scorers_list dla ładnych przycisków
            scorers_list = extract_scorers_list(scorers_str)
            if scorers_list:
                cols_sc = st.columns(4)
                for idx, item in enumerate(scorers_list):
                    col_idx = idx % 4
                    with cols_sc[col_idx]:
                        if item['is_own']:
                            st.error(item['display'])
                        else:
                            # Unikalny klucz dla każdego przycisku
                            if st.button(item['display'], key=f"cal_match_sc_{idx}_{item['link_name']}"):
                                st.session_state['cal_selected_item'] = item['link_name']
                                st.session_state['cal_view_mode'] = 'profile'
                                st.rerun()
            else:
                st.write(scorers_str)

        # --- SEKCJA SKŁADU ---
        df_det = load_details("wystepy.csv")
        if df_det is not None and 'Data_Obj' in m_data:
            match_date = pd.to_datetime(m_data['Data_Obj']).date()
            if 'Data_Sort' in df_det.columns:
                # Szukamy składu z tego konkretnego dnia
                squad = df_det[df_det['Data_Sort'].dt.date == match_date]
                if not squad.empty:
                    st.markdown("### 👥 Skład TSP")
                    # Sortujemy: Minuty malejąco
                    squad = squad.sort_values('Minuty', ascending=False)

                    # Wyświetlamy jako przyciski
                    for _, pl_row in squad.iterrows():
                        p_name = pl_row['Zawodnik_Clean']
                        mins = pl_row['Minuty']
                        gols = pd.to_numeric(pl_row['Gole'], errors='coerce')

                        btn_lbl = f"{p_name} ({mins}')"
                        if gols > 0:
                            btn_lbl += f" ⚽{int(gols)}"

                        # Przyciski jeden pod drugim (lub w kolumnach, jeśli wolisz)
                        if st.button(btn_lbl, key=f"cal_sq_btn_{p_name}_{match_date}"):
                            st.session_state['cal_selected_item'] = p_name
                            st.session_state['cal_view_mode'] = 'profile'
                            st.rerun()
                else:
                    st.caption("Brak szczegółowego składu w bazie występów dla tego meczu.")

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
            cal_mode = st.radio("Tryb widoku:", ["Dzień w Historii (2026 + Archiwum)", "Konkretny Rocznik (Archiwum)"],
                                horizontal=True)

        # Ustalanie roku bazowego
        if "Konkretny" in cal_mode:
            with c_mode2:
                target_year = st.number_input("Wybierz rok do przeglądania:", min_value=1990, max_value=2030,
                                              value=today.year)
            show_history_matches = False  # Pokaż tylko mecze z target_year
        else:
            target_year = today.year  # Domyślnie bieżący rok
            show_history_matches = True  # Pokaż mecze z bieżącego roku ORAZ historyczne z tego dnia
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
            <div style="background-color: rgba(40, 167, 69, 0.2); border: 2px solid #28a745; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h2 style="color: #28a745; margin:0;">🔥 DZIEŃ MECZOWY! 🔥</h2>
                <h3 style="margin:5px 0;">TSP vs {match_today_alert.split('(')[0]}</h3>
                <p style="margin:0; font-weight:bold;">{match_today_alert.split('(')[1].replace(')', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            st.toast(f"⚽ Dziś mecz: {match_today_alert}!", icon="🏟️")

        # --- BUDOWANIE MAPY ZDARZEŃ ---
        events_map = {}
        current_squad_names = [str(x).lower().strip() for x in
                               df_curr['imię i nazwisko'].unique()] if df_curr is not None else []

        # A. Urodziny Piłkarzy
        if df_p is not None:
            df_p['id_name'] = df_p['imię i nazwisko'].astype(str).str.lower().str.strip()
            df_unique = df_p.drop_duplicates(subset=['id_name'], keep='first')
            col_b = next((c for c in df_unique.columns if c in ['data urodzenia', 'urodzony', 'data_ur']), None)

            if col_b:
                for _, row in df_unique.iterrows():
                    try:
                        name = row['imię i nazwisko']
                        # [POPRAWKA] Ręczna korekta dla Macieja Górskiego
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

        # C. Mecze (Logika Hybrydowa)
        if df_m is not None and 'dt_obj' in df_m.columns:
            for _, row in df_m.dropna(subset=['dt_obj']).iterrows():
                d = row['dt_obj']
                d_date = d.date()
                key = (d.month, d.day)

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
                        # Stylizacja dla meczu historycznego
                        icon = "⚫"
                        sort_prio = 5  # Na samym dole
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

                    match_details = {'Rywal': rywal, 'Data_Txt': d.strftime('%d.%m.%Y'), 'Data_Obj': d,
                                     'Wynik': f"{raw_score}", 'Strzelcy': row.get('strzelcy', '-'),
                                     'Widzów': row.get('widzów', '-'), 'Dom': row.get('dom', '0')}

                    events_map.setdefault(key, []).append({
                        'type': 'match',
                        'label': label_str,
                        'match_data': match_details,
                        'sort': sort_prio,
                        'is_history': is_history_event
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
                # Klasy CSS 'cal-card' i 'today' zdefiniowane w apply_custom_css
                css_class = "cal-card today" if is_today else "cal-card"
                st.markdown(
                    f"<div class='{css_class}'><small>{days_pl[i]}</small><br><strong>{curr_day.strftime('%d.%m')}</strong></div>",
                    unsafe_allow_html=True)

                if not day_events:
                    st.markdown("<div style='text-align: center; opacity: 0.3; font-size: 10px;'>Brak</div>",
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
                        if day_num == 0:
                            st.write(" ")
                        else:
                            is_today_cell = (
                                        day_num == today.day and sel_month == today.month and target_year == today.year)
                            css_class = "cal-card today" if is_today_cell else "cal-card"

                            st.markdown(
                                f"<div class='{css_class}'><strong>{day_num}</strong></div>",
                                unsafe_allow_html=True)

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

elif opcja == "Składy Historyczne":
    st.header("🗂️ Składy Historyczne")

    df_det = load_details("wystepy.csv")
    df_bio = load_data("pilkarze.csv")
    df_t = load_data("trenerzy.csv")

    if df_det is None or df_bio is None:
        st.error("Brak wymaganych plików (wystepy.csv lub pilkarze.csv).")
    else:
        # Generowanie flag dla trenerów
        if df_t is not None:
            df_t = prepare_flags(df_t)

        seasons = sorted(df_det['Sezon'].unique(), reverse=True)

        # UI: Sezon + Checkbox Młodzieżowca
        c_sel_s, c_check_m = st.columns([3, 1])
        with c_sel_s:
            sel_season = st.selectbox("Wybierz Sezon:", seasons)
        with c_check_m:
            st.write("")  # Odstęp
            st.write("")
            show_only_youth = st.checkbox("Tylko Młodzieżowcy (Ⓜ️)")

        # --- PRZYGOTOWANIE DANYCH ---
        season_data = df_det[df_det['Sezon'] == sel_season].copy()

        # Agregacja statystyk
        agg = season_data.groupby('Zawodnik_Clean').agg({
            'Minuty': 'sum', 'Mecz_Label': 'nunique', 'Gole': 'sum', 'Żółte': 'sum', 'Czerwone': 'sum'
        }).reset_index()
        agg.rename(columns={'Mecz_Label': 'Mecze'}, inplace=True)
        agg['Gole'] = pd.to_numeric(agg['Gole'], errors='coerce').fillna(0).astype(int)

        # Łączenie z bazą piłkarzy
        df_bio_unique = df_bio.drop_duplicates(subset=['imię i nazwisko']).copy()
        df_bio_unique['join_key'] = df_bio_unique['imię i nazwisko'].astype(str).str.strip()
        df_bio_unique = prepare_flags(df_bio_unique)

        merged = pd.merge(agg, df_bio_unique, left_on='Zawodnik_Clean', right_on='join_key', how='left')

        # --- LOGIKA MŁODZIEŻOWCA (M) ---
        try:
            start_year = int(sel_season.split('/')[0])
        except:
            start_year = 2025

        if start_year >= 2024:
            limit_year = start_year - 20
        else:
            limit_year = start_year - 19

        def check_youth(dob_val):
            if pd.isna(dob_val): return False
            try:
                y = pd.to_datetime(dob_val).year
                return y >= limit_year
            except:
                return False

        merged['Is_Youth'] = merged['data urodzenia'].apply(check_youth)

        def mark_youth_name(row):
            name = row['Zawodnik_Clean']
            if row['Is_Youth']:
                # ZMIANA: Użycie emotki Ⓜ️ jako prefixu (spójnie z Aktualnym Sezonem)
                return f"Ⓜ️ {name}"
            return name

        merged['Zawodnik_Display'] = merged.apply(mark_youth_name, axis=1)

        # FILTROWANIE PO CHECKBOXIE
        if show_only_youth:
            merged = merged[merged['Is_Youth'] == True]

        # Normalizacja pozycji
        def normalize_position_group(val):
            s = str(val).lower().strip()
            if 'bram' in s or 'gk' in s: return "Bramkarz"
            if any(x in s for x in ['obr', 'stoper', 'def', 'boczny']): return "Obrońca"
            if any(x in s for x in ['pom', 'skrzyd', 'mid', 'wahad']): return "Pomocnik"
            if any(x in s for x in ['nap', 'snaj', 'for', 'atak']): return "Napastnik"
            return "Inne"

        merged['Grupa_Pozycji'] = merged['pozycja'].apply(normalize_position_group)

        # Wiek w sezonie
        def calc_season_age(dob_val):
            if pd.isna(dob_val): return None
            try:
                val = start_year - pd.to_datetime(dob_val).year
                return val if val > 0 and val < 100 else None
            except:
                return None

        merged['Wiek_w_Sezonie'] = merged['data urodzenia'].apply(calc_season_age)

        # ==========================================
        # 1. PANEL STATYSTYK (DRUŻYNOWE + INDYWIDUALNE)
        # ==========================================
        if not show_only_youth:
            # --- A. DRUŻYNOWE ---
            total_goals = agg['Gole'].sum()
            total_players = len(agg)
            avg_age = merged['Wiek_w_Sezonie'].mean()
            avg_age_str = f"{avg_age:.1f}" if pd.notna(avg_age) else "-"

            st.markdown(f"""
            <div style="background-color: var(--secondary-background-color); padding: 15px; border-radius: 10px; border: 1px solid #ccc; margin-bottom: 20px;">
                <h4 style="margin-top:0; text-align: center; border-bottom: 1px solid #666; padding-bottom: 5px; opacity: 0.8;">📊 Statystyki Drużynowe</h4>
                <div style="display: flex; justify-content: space-around; align-items: center; margin-top: 10px;">
                    <div style="text-align: center;">
                        <h3 style="margin: 0; color: #2ecc71;">{total_goals} ⚽</h3>
                        <small>Goli w sezonie</small>
                    </div>
                    <div style="text-align: center;">
                        <h3 style="margin: 0;">{total_players} 👤</h3>
                        <small>Użytych piłkarzy</small>
                    </div>
                    <div style="text-align: center;">
                        <h3 style="margin: 0;">{avg_age_str} lat</h3>
                        <small>Średnia wieku</small>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 10px; font-size: 0.8em; opacity: 0.7;">
                    Ⓜ️ - Status młodzieżowca (rocznik {limit_year} i młodsi)
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- B. INDYWIDUALNE (LIDERZY) ---
            if not merged.empty:
                # 1. Strzelcy
                max_goals = merged['Gole'].max()
                if max_goals > 0:
                    best_scorers = merged[merged['Gole'] == max_goals]['Zawodnik_Display'].tolist()
                    scorer_val = f"{max_goals} goli"
                else:
                    best_scorers = ["-"]
                    scorer_val = "0 goli"

                # 2. Minuty
                max_mins = merged['Minuty'].max()
                most_mins = merged[merged['Minuty'] == max_mins]['Zawodnik_Display'].tolist()

                # 3. Występy
                max_apps = merged['Mecze'].max()
                most_apps = merged[merged['Mecze'] == max_apps]['Zawodnik_Display'].tolist()

                # Helper do formatowania listy nazwisk
                def fmt_leaders(lst):
                    if len(lst) > 2: return f"{len(lst)} zawodników"
                    return ", ".join(lst)

                st.markdown("#### 🏅 Liderzy Sezonu")
                c_i1, c_i2, c_i3 = st.columns(3)

                c_i1.metric("👑 Najlepszy Strzelec", fmt_leaders(best_scorers), scorer_val)
                c_i2.metric("⏱️ Najwięcej Minut", fmt_leaders(most_mins), f"{max_mins} min")
                c_i3.metric("👕 Najwięcej Występów", fmt_leaders(most_apps), f"{max_apps} meczy")

            st.divider()
        else:
            st.info(f"Wyświetlam tylko młodzieżowców (rocznik {limit_year} i młodsi).")

        # ==========================================
        # 2. SEKCJA TRENERÓW
        # ==========================================
        if not show_only_youth and df_t is not None and 'Data_Sort' in season_data.columns:
            st.markdown("### 👔 Sztab Szkoleniowy")

            s_start = season_data['Data_Sort'].min()
            s_end = season_data['Data_Sort'].max()

            coach_list = []

            if pd.notna(s_start) and pd.notna(s_end):
                def parse_coach_date(v):
                    if str(v).lower() in ['-', 'nan', '', 'obecnie']: return pd.NaT
                    return pd.to_datetime(v, dayfirst=True, errors='coerce')

                df_t['d_start'] = df_t['początek'].apply(parse_coach_date)
                df_t['d_end'] = df_t['koniec'].apply(parse_coach_date)

                for _, crow in df_t.iterrows():
                    c_start = crow['d_start']
                    c_end = crow['d_end']
                    if pd.isna(c_end): c_end = pd.Timestamp.now() + pd.Timedelta(days=365)

                    if pd.notna(c_start):
                        if (c_start <= s_end) and (c_end >= s_start):
                            flaga_url = crow.get('Flaga')
                            if str(flaga_url) == 'nan' or not flaga_url: flaga_url = None

                            coach_list.append({
                                "Flaga": flaga_url,
                                "Trener": crow['imię i nazwisko'],
                                "Funkcja": crow.get('funkcja', 'Trener'),
                                "Od": c_start.strftime('%d.%m.%Y') if pd.notna(c_start) else "-",
                                "Do": crow['koniec'] if pd.notna(crow['koniec']) else "obecnie"
                            })

            if coach_list:
                df_coaches_season = pd.DataFrame(coach_list)
                st.dataframe(
                    df_coaches_season,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Flaga": st.column_config.ImageColumn("Kraj", width="small"),
                        "Trener": st.column_config.TextColumn("Nazwisko", width="medium"),
                        "Funkcja": st.column_config.TextColumn("Rola"),
                        "Od": st.column_config.TextColumn("Data objęcia"),
                        "Do": st.column_config.TextColumn("Data odejścia")
                    }
                )

        st.divider()

        # ==========================================
        # 3. TABELE PIŁKARZY
        # ==========================================
        cols_show = ['Flaga', 'Zawodnik_Display', 'Grupa_Pozycji', 'pozycja', 'Wiek_w_Sezonie', 'Mecze', 'Minuty',
                     'Gole', 'Żółte', 'Czerwone']
        final_cols = [c for c in cols_show if c in merged.columns]
        final_df = merged[final_cols]

        formations_order = [
            ("Bramkarz", "🧤 Bramkarze"),
            ("Obrońca", "🛡️ Obrońcy"),
            ("Pomocnik", "⚙️ Pomocnicy"),
            ("Napastnik", "⚽ Napastnicy")
        ]

        common_config = {
            "Flaga": st.column_config.ImageColumn("Kraj", width="small"),
            "Zawodnik_Display": st.column_config.TextColumn("Zawodnik"),
            "Minuty": st.column_config.ProgressColumn("Minuty", format="%d'",
                                                      max_value=int(merged['Minuty'].max() or 100)),
            "Gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
            "Żółte": st.column_config.NumberColumn("Żółte", format="%d 🟨"),
            "Czerwone": st.column_config.NumberColumn("Czerwone", format="%d 🟥"),
            "Wiek_w_Sezonie": st.column_config.NumberColumn("Wiek", format="%d lat"),
            "pozycja": st.column_config.TextColumn("Pozycja")
        }

        has_any_data = False
        for group_key, header_txt in formations_order:
            df_pos = final_df[final_df['Grupa_Pozycji'] == group_key].sort_values(['Minuty', 'Mecze'], ascending=False)
            if not df_pos.empty:
                has_any_data = True
                st.markdown(f"#### {header_txt}")
                cols_to_display = [c for c in final_df.columns if c != 'Grupa_Pozycji']
                st.dataframe(df_pos[cols_to_display], use_container_width=True, hide_index=True,
                             column_config=common_config)

        df_other = final_df[final_df['Grupa_Pozycji'] == "Inne"].sort_values(['Minuty', 'Mecze'], ascending=False)
        if not df_other.empty:
            has_any_data = True
            st.markdown("#### ❓ Nieznana pozycja")
            cols_to_display = [c for c in final_df.columns if c != 'Grupa_Pozycji']
            st.dataframe(df_other[cols_to_display], use_container_width=True, hide_index=True,
                         column_config=common_config)

        if show_only_youth and not has_any_data:
            st.warning("Brak młodzieżowców w składzie dla tego sezonu (lub brak danych o wieku).")

        # --- TABELA 4: RUCHY KADROWE ---
        if not show_only_youth:
            st.divider()
            st.subheader("🔄 Ruchy Kadrowe")
            curr_idx = seasons.index(sel_season)
            prev_season_str = seasons[curr_idx + 1] if curr_idx + 1 < len(seasons) else None

            if prev_season_str:
                prev_players = set(df_det[df_det['Sezon'] == prev_season_str]['Zawodnik_Clean'])
                curr_players = set(season_data['Zawodnik_Clean'])

                new_players = sorted(list(curr_players - prev_players))
                left_players = sorted(list(prev_players - curr_players))

                c_new, c_left = st.columns(2)
                with c_new:
                    st.markdown(f"**🟢 Przybyli (Nowi względem {prev_season_str})**")
                    if new_players:
                        df_new = pd.DataFrame(new_players, columns=['Zawodnik'])
                        df_new = pd.merge(df_new, df_bio_unique[['join_key', 'Flaga', 'pozycja']], left_on='Zawodnik',
                                          right_on='join_key', how='left')
                        st.dataframe(df_new[['Flaga', 'Zawodnik', 'pozycja']], hide_index=True,
                                     use_container_width=True,
                                     column_config={"Flaga": st.column_config.ImageColumn("", width="small")})
                    else:
                        st.info("Brak debiutantów.")

                with c_left:
                    st.markdown(f"**🔴 Ubyli (Grali w {prev_season_str}, brak w tym)**")
                    if left_players:
                        df_left = pd.DataFrame(left_players, columns=['Zawodnik'])
                        df_left = pd.merge(df_left, df_bio_unique[['join_key', 'Flaga', 'pozycja']], left_on='Zawodnik',
                                           right_on='join_key', how='left')
                        st.dataframe(df_left[['Flaga', 'Zawodnik', 'pozycja']], hide_index=True,
                                     use_container_width=True,
                                     column_config={"Flaga": st.column_config.ImageColumn("", width="small")})
                    else:
                        st.info("Nikt nie odszedł.")
            else:
                st.caption("Brak danych historycznych dla sezonu poprzedzającego.")

elif opcja == "Centrum Zawodników":
    st.header("🏃 Centrum Zawodników TSP")
    # ZMIANA: 4 zakładki zamiast 3
    tab1, tab2, tab3, tab4 = st.tabs(["Baza Zawodników", "Strzelcy", "Klub 100", "🎖️ Sala Chwał (Odznaki)"])

    # Wspólne ładowanie danych dla wszystkich zakładek (Optymalizacja)
    df_uv = load_data("pilkarze.csv")
    df_det = load_details("wystepy.csv")

    if df_uv is not None:
        # Obliczenia globalne meczów
        minutes_dict = {}
        matches_real_dict = {}

        # Statystyki z detali
        if df_det is not None and 'Zawodnik_Clean' in df_det.columns:
            minutes_dict = df_det.groupby('Zawodnik_Clean')['Minuty'].sum().to_dict()
            matches_real_dict = df_det['Zawodnik_Clean'].value_counts().to_dict()

        col_s = 'SUMA'
        if 'SUMA' not in df_uv.columns:
            col_s = 'mecze' if 'mecze' in df_uv.columns else ('liczba' if 'liczba' in df_uv.columns else None)

        if col_s and col_s in df_uv.columns:
            if isinstance(df_uv[col_s], pd.DataFrame): df_uv[col_s] = df_uv[col_s].iloc[:, 0]
            df_uv[col_s] = pd.to_numeric(df_uv[col_s], errors='coerce').fillna(0).astype(int)
        else:
            col_s = 'Total_Calc'
            df_uv[col_s] = 0

        df_uv['Minuty'] = df_uv['imię i nazwisko'].map(minutes_dict).fillna(0).astype(int)
        df_uv['Mecze_Calc'] = df_uv['imię i nazwisko'].map(matches_real_dict).fillna(0).astype(int)
        df_uv['Total_Matches'] = df_uv[[col_s, 'Mecze_Calc']].max(axis=1)

        # Unikalna lista
        df_uv = df_uv.sort_values(['Total_Matches', 'Minuty'], ascending=[False, False]).drop_duplicates(
            subset=['imię i nazwisko'])
        df_uv = prepare_flags(df_uv)

    # =========================================================
    # TAB 1: BAZA ZAWODNIKÓW
    # =========================================================
    with tab1:
        st.subheader("Baza Zawodników")
        if df_uv is not None:
            # Filtry i Sortowanie
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                search = st.text_input("Szukaj zawodnika:", key="search_pl")
            with c2:
                sort_opt = st.selectbox("Sortuj wg:", ["Mecze (Najwięcej)", "Mecze (Najmniej)", "Minuty (Najwięcej)",
                                                       "Nazwisko (A-Z)"])
            with c3:
                st.write("")
                st.write("")
                obcy = st.checkbox("Tylko obcokrajowcy", key="chk_for")

            df_show = df_uv.copy()
            if search: df_show = df_show[df_show['imię i nazwisko'].astype(str).str.contains(search, case=False)]
            if obcy and 'narodowość' in df_show.columns:
                df_show = df_show[~df_show['narodowość'].astype(str).str.contains("Polska", na=False, case=False)]

            if sort_opt == "Mecze (Najwięcej)":
                df_show = df_show.sort_values(['Total_Matches', 'Minuty'], ascending=[False, False])
            elif sort_opt == "Mecze (Najmniej)":
                df_show = df_show.sort_values(['Total_Matches', 'Minuty'], ascending=[True, True])
            elif sort_opt == "Minuty (Najwięcej)":
                df_show = df_show.sort_values(['Minuty', 'Total_Matches'], ascending=[False, False])
            elif sort_opt == "Nazwisko (A-Z)":
                df_show = df_show.sort_values('imię i nazwisko')

            st.dataframe(
                df_show[['imię i nazwisko', 'Flaga', 'Narodowość', 'pozycja', 'Total_Matches', 'Minuty']],
                use_container_width=True, hide_index=True, height=500,
                column_config={
                    "Flaga": st.column_config.ImageColumn("", width="small"),
                    "Total_Matches": st.column_config.NumberColumn("Mecze", format="%d 👕"),
                    "Minuty": st.column_config.NumberColumn("Minuty", format="%d ⏱️")
                }
            )

            st.divider()
            st.subheader("📈 Profil i Analiza")
            lista_zawodnikow = [""] + sorted(df_uv['imię i nazwisko'].unique().tolist())
            wyb = st.selectbox("Wybierz zawodnika, aby zobaczyć szczegóły:", lista_zawodnikow)
            if wyb: render_player_profile(wyb)
        else:
            st.error("Brak pliku pilkarze.csv")

    # =========================================================
    # TAB 2: STRZELCY
    # =========================================================
    with tab2:
        st.subheader("⚽ Klasyfikacja Strzelców")
        df_s = load_data("strzelcy.csv")
        if df_s is not None:
            c1, c2 = st.columns(2)
            search_s = c1.text_input("Szukaj strzelca:", key="ss")
            unique_seasons = sorted(df_s['sezon'].astype(str).unique(), reverse=True) if 'sezon' in df_s.columns else []
            sezs = c2.multiselect("Filtruj Sezon:", unique_seasons)

            df_v = df_s.copy()
            if sezs: df_v = df_v[df_v['sezon'].isin(sezs)]
            if search_s: df_v = df_v[df_v['imię i nazwisko'].astype(str).str.contains(search_s, case=False)]

            if 'gole' in df_v.columns:
                grp = df_v.groupby(['imię i nazwisko', 'kraj'], as_index=False)['gole'].sum().sort_values('gole',
                                                                                                          ascending=False)
                grp = prepare_flags(grp, 'kraj')
                st.dataframe(grp[['imię i nazwisko', 'Flaga', 'Narodowość', 'gole']], use_container_width=True,
                             hide_index=True,
                             column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                            "gole": st.column_config.NumberColumn("Gole", format="%d ⚽")})
            else:
                st.warning("Brak kolumny 'gole'.")
        else:
            st.error("Brak pliku strzelcy.csv")

    # =========================================================
    # TAB 3: KLUB 100
    # =========================================================
    with tab3:
        st.subheader("🏛️ Klub 100 (Najwięcej występów)")
        if df_uv is not None:
            k100 = df_uv[df_uv['Total_Matches'] >= 100].sort_values('Total_Matches', ascending=False)
            st.caption(f"Znaleziono {len(k100)} zawodników w Klubie 100.")
            st.dataframe(k100[['imię i nazwisko', 'Flaga', 'Narodowość', 'Total_Matches']], use_container_width=True,
                         hide_index=True,
                         column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                        "Total_Matches": st.column_config.NumberColumn("Liczba Meczów",
                                                                                       format="%d 👕")})

    # =========================================================
    # TAB 4: SALA CHWAŁ (ZOPTYMALIZOWANA)
    # =========================================================
    with tab4:
        st.subheader("🎖️ Sala Chwał i Osiągnięcia")
        st.markdown("Zestawienie zawodników z unikalnymi osiągnięciami w historii klubu.")

        if df_uv is not None and df_det is not None:
            # OPTYMALIZACJA: Przekazujemy załadowane już dane (df_det, df_uv) do funkcji
            # zamiast ładować je 300 razy w pętli.

            with st.spinner("Generowanie Sali Chwał..."):
                players_to_check = df_uv['imię i nazwisko'].tolist()

                categories = {
                    "Klub 100": [],
                    "Strzelcy": [],
                    "Specjalne": [],
                    "Awans": []
                }

                # Używamy zoptymalizowanej funkcji z parametrami df_w, df_p
                for p_name in players_to_check:
                    # Przekazujemy df_det i df_uv, żeby funkcja nie czytała plików z dysku
                    badges = get_player_record_badges(p_name, df_w=df_det, df_p=df_uv)
                    if not badges: continue

                    # Pobierz flagę (bezpiecznie)
                    flaga_series = df_uv[df_uv['imię i nazwisko'] == p_name]['Flaga']
                    flaga = flaga_series.iloc[0] if not flaga_series.empty else None

                    for b in badges:
                        entry = {'name': p_name, 'flag': flaga, 'desc': b['text']}

                        if "Klub 100" in b['text']:
                            categories["Klub 100"].append(entry)
                        elif "strzelec" in b['text'] or "Hat-trick" in b['text']:
                            categories["Strzelcy"].append(entry)
                        elif "Awans" in b['text']:
                            categories["Awans"].append(entry)
                        else:
                            categories["Specjalne"].append(entry)

            # --- RENDEROWANIE KATEGORIAMI ---

            # 1. AWANS DO EKSTRAKLASY (ZŁOTA SEKCJA)
            if categories["Awans"]:
                st.markdown("### 🚀 Bohaterowie Awansów (Ekstraklasa)")
                st.markdown("Zawodnicy, którzy wywalczyli historyczne awanse.")

                cols = st.columns(3)
                for i, item in enumerate(categories["Awans"]):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div style="border: 2px solid #FFD700; border-radius: 8px; padding: 10px; margin-bottom: 10px; background-color: rgba(255, 215, 0, 0.1);">
                            <div style="display: flex; align-items: center;">
                                <img src="{item['flag']}" width="30" style="margin-right: 10px;">
                                <strong>{item['name']}</strong>
                            </div>
                            <div style="font-size: 0.8em; color: #FFD700; margin-top: 5px;">{item['desc']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                st.divider()

            # 2. KLUB 100 (CZERWONA SEKCJA)
            if categories["Klub 100"]:
                st.markdown("### 💯 Elitarny Klub 100")
                with st.expander(f"Zobacz wszystkich ({len(categories['Klub 100'])})", expanded=False):
                    df_k100_display = pd.DataFrame(categories["Klub 100"])
                    st.dataframe(
                        df_k100_display,
                        column_config={
                            "flag": st.column_config.ImageColumn("Kraj", width="small"),
                            "name": "Zawodnik",
                            "desc": "Osiągnięcie"
                        },
                        use_container_width=True, hide_index=True
                    )

            # 3. STRZELCY I WYCZYNY (ZIELONA SEKCJA)
            if categories["Strzelcy"]:
                st.markdown("### ⚽ Snajperzy i Hat-tricki")
                top_scorers = [x for x in categories["Strzelcy"] if "strzelec wszech czasów" in x['desc']]
                others = [x for x in categories["Strzelcy"] if x not in top_scorers]

                if top_scorers:
                    cols_s = st.columns(3)
                    for i, item in enumerate(top_scorers):
                        with cols_s[i % 3]:
                            st.markdown(f"""
                            <div style="border: 1px solid #28a745; border-radius: 8px; padding: 8px; margin-bottom: 8px;">
                                <strong>👑 {item['name']}</strong><br>
                                <span style="font-size: 0.8em; color: #28a745;">{item['desc']}</span>
                            </div>
                            """, unsafe_allow_html=True)

                if others:
                    with st.expander("Pozostałe wyczyny strzeleckie (Hat-tricki, Jokery)"):
                        st.dataframe(pd.DataFrame(others), use_container_width=True, hide_index=True,
                                     column_config={"flag": st.column_config.ImageColumn(""), "name": "Kto",
                                                    "desc": "Co"})

            # 4. SPECJALNE (NIEBIESKA SEKCJA)
            if categories["Specjalne"]:
                st.markdown("### 🌟 Wyróżnienia Specjalne")
                st.caption("Debiutanci, Weterani, Żelazne Płuca i... Bad Boys.")

                df_spec = pd.DataFrame(categories["Specjalne"])
                st.dataframe(
                    df_spec,
                    column_config={
                        "flag": st.column_config.ImageColumn("", width="small"),
                        "name": st.column_config.TextColumn("Zawodnik", width="medium"),
                        "desc": st.column_config.TextColumn("Odznaka", width="large")
                    },
                    use_container_width=True, hide_index=True
                )
# =========================================================
# MODUŁ 6: CENTRUM MECZOWE (POPRAWIONY)
# =========================================================
elif opcja == "Centrum Meczowe":
    st.header("⚽ Centrum Meczowe")

    df_m = load_data("mecze.csv")

    if df_m is not None:
        # --- 1. GLOBALNE PRZETWARZANIE DANYCH ---
        # A. Normalizacja wyniku
        def standardize_score(s):
            if pd.isna(s): return None
            s = str(s).strip()
            if '(' in s: s = s.split('(')[0].strip()
            return s


        if 'wynik' in df_m.columns:
            df_m['wynik_std'] = df_m['wynik'].apply(standardize_score)


        # B. Określenie rezultatu
        def get_result_type(row):
            if pd.isna(row.get('wynik')): return None
            try:
                parts = str(row['wynik']).split('-')
                if len(parts) < 2: return None
                g_tsp = int(parts[0])
                g_opp = int(parts[1])
                if g_tsp > g_opp:
                    return "Zwycięstwo"
                elif g_tsp == g_opp:
                    return "Remis"
                else:
                    return "Porażka"
            except:
                return None


        df_m['rezultat_calc'] = df_m.apply(get_result_type, axis=1)

        # C. Konwersja daty
        col_date = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
        if col_date:
            df_m['dt_obj'] = pd.to_datetime(df_m[col_date], dayfirst=True, errors='coerce')

        # --- TABS ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["🔍 Analiza Rywala", "📊 Statystyki Ogólne", "🗄️ Archiwum Spotkań", "📢 Frekwencja",
             "👥 Składy i Raporty"])

        # =========================================================
        # ZAKŁADKA 1: ANALIZA RYWALA
        # =========================================================
        with tab1:
            st.subheader("🆚 Analiza Przeciwników")
            if df_m is not None and 'rywal' in df_m.columns:
                rival_stats = {}
                for _, row in df_m.iterrows():
                    r_name = row.get('rywal', 'Nieznany')
                    if pd.isna(r_name) or str(r_name).strip() == '': continue
                    if r_name not in rival_stats:
                        rival_stats[r_name] = {'Mecze': 0, 'W': 0, 'R': 0, 'P': 0, 'GF': 0, 'GA': 0, 'Pkt': 0}
                    stats = rival_stats[r_name]
                    stats['Mecze'] += 1
                    res = parse_result(row.get('wynik'))
                    if res:
                        t, o = res
                        stats['GF'] += t;
                        stats['GA'] += o
                        if t > o:
                            stats['W'] += 1; stats['Pkt'] += 3
                        elif t == o:
                            stats['R'] += 1; stats['Pkt'] += 1
                        else:
                            stats['P'] += 1

                df_h2h = pd.DataFrame.from_dict(rival_stats, orient='index').reset_index()
                df_h2h.rename(columns={'index': 'Rywal'}, inplace=True)
                df_h2h['Bilans'] = df_h2h['GF'] - df_h2h['GA']
                df_h2h['Śr. Pkt'] = df_h2h['Pkt'] / df_h2h['Mecze']
                df_h2h['% Wygranych'] = (df_h2h['W'] / df_h2h['Mecze']) * 100

                mode = st.radio("Widok:", ["🏆 Rankingi H2H (Bilans)", "🔍 Szczegóły konkretnego rywala"],
                                horizontal=True)
                st.divider()

                if mode == "🏆 Rankingi H2H (Bilans)":
                    min_matches = st.slider("Minimalna liczba rozegranych meczów:", 1, 10, 2)
                    df_rank = df_h2h[df_h2h['Mecze'] >= min_matches].copy()
                    col_best, col_worst = st.columns(2)
                    df_best = df_rank.sort_values(['Śr. Pkt', 'Bilans', 'Mecze'], ascending=[False, False, False]).head(
                        10)
                    with col_best:
                        st.markdown("### 🟢 Ulubieni Rywale")
                        st.dataframe(df_best[['Rywal', 'Mecze', 'W', 'R', 'P', 'Bilans', 'Śr. Pkt']], hide_index=True,
                                     use_container_width=True,
                                     column_config={"Śr. Pkt": st.column_config.ProgressColumn("Śr. Pkt", format="%.2f",
                                                                                               min_value=0,
                                                                                               max_value=3)})

                    df_worst = df_rank.sort_values(['Śr. Pkt', 'Bilans'], ascending=[True, True]).head(10)
                    with col_worst:
                        st.markdown("### 🔴 Niewygodni Rywale")
                        st.dataframe(df_worst[['Rywal', 'Mecze', 'W', 'R', 'P', 'Bilans', 'Śr. Pkt']], hide_index=True,
                                     use_container_width=True,
                                     column_config={"Śr. Pkt": st.column_config.ProgressColumn("Śr. Pkt", format="%.2f",
                                                                                               min_value=0,
                                                                                               max_value=3)})
                else:
                    rivals_list = sorted(df_m['rywal'].dropna().unique())
                    selected_rival = st.selectbox("Wybierz przeciwnika:", rivals_list)
                    if selected_rival:
                        stats_row = df_h2h[df_h2h['Rywal'] == selected_rival]
                        if not stats_row.empty:
                            r = stats_row.iloc[0]
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Mecze", int(r['Mecze']))
                            c2.metric("Bilans", f"{int(r['W'])}-{int(r['R'])}-{int(r['P'])}")
                            c3.metric("Bramki", f"{int(r['GF'])}:{int(r['GA'])}")
                            c4.metric("Śr. Pkt", f"{r['Śr. Pkt']:.2f}")

                        matches_with_score = df_m[df_m['rywal'] == selected_rival].copy()
                        if 'dt_obj' in matches_with_score.columns:
                            matches_with_score = matches_with_score.sort_values('dt_obj', ascending=False)

                        st.subheader("📜 Historia Spotkań")
                        cols_to_show = ['data meczu', 'rozgrywki', 'wynik', 'dom']
                        if 'widzów' in matches_with_score.columns: cols_to_show.append('widzów')
                        final_cols = [c for c in cols_to_show if c in matches_with_score.columns]
                        st.dataframe(matches_with_score[final_cols].style.map(color_results_logic, subset=[
                            'wynik'] if 'wynik' in final_cols else None),
                                     use_container_width=True, hide_index=True)
            else:
                st.error("Brak danych w pliku mecze.csv")

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
                        color_map = {"Zwycięstwo": "green", "Remis": "gray", "Porażka": "red"}
                        fig = px.pie(res_counts, values='Liczba', names='Rezultat', color='Rezultat',
                                     color_discrete_map=color_map, hole=0.4)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.bar_chart(res_counts.set_index('Rezultat'))
                with c2:
                    st.write("Sumarycznie:")
                    st.dataframe(res_counts, hide_index=True, use_container_width=True)

        # =========================================================
        # ZAKŁADKA 3: ARCHIWUM SPOTKAŃ
        # =========================================================
        with tab3:
            st.subheader("🗄️ Pełne Archiwum Spotkań")
            if df_m is not None:
                df_arch = df_m.copy()
                if 'dt_obj' in df_arch.columns: df_arch = df_arch.sort_values('dt_obj', ascending=False)
                c_f1, c_f2, c_f3 = st.columns(3)
                with c_f1:
                    seasons = sorted(df_arch['sezon'].astype(str).unique(),
                                     reverse=True) if 'sezon' in df_arch.columns else []
                    sel_seas = st.multiselect("Sezon:", seasons)
                with c_f2:
                    rivals = sorted(df_arch['rywal'].astype(str).unique()) if 'rywal' in df_arch.columns else []
                    sel_riv = st.multiselect("Rywal:", rivals)
                with c_f3:
                    sel_dom = st.selectbox("Miejsce:", ["Wszystkie", "Dom", "Wyjazd"])

                if sel_seas: df_arch = df_arch[df_arch['sezon'].isin(sel_seas)]
                if sel_riv: df_arch = df_arch[df_arch['rywal'].isin(sel_riv)]
                if sel_dom != "Wszystkie":
                    def check_is_home_arch(val):
                        s = str(val).lower()
                        return any(
                            k in s for k in ['1', 'true', 'tak', 'dom', 'bielsko', 'czechowice', 'rekord', 'u siebie'])


                    if sel_dom == "Dom":
                        df_arch = df_arch[df_arch['dom'].apply(check_is_home_arch)]
                    else:
                        df_arch = df_arch[~df_arch['dom'].apply(check_is_home_arch)]

                cols_show = ['data meczu', 'sezon', 'rywal', 'wynik', 'rozgrywki', 'strzelcy', 'widzów']
                final_cols = [c for c in cols_show if c in df_arch.columns]
                st.dataframe(df_arch[final_cols].style.map(color_results_logic,
                                                           subset=['wynik'] if 'wynik' in df_arch.columns else None),
                             use_container_width=True, hide_index=True, height=500,
                             column_config={"data meczu": st.column_config.TextColumn("Data"),
                                            "widzów": st.column_config.NumberColumn("Frekwencja")})
            else:
                st.error("Brak danych.")

        # =========================================================
        # ZAKŁADKA 4: FREKWENCJA
        # =========================================================
        with tab4:
            st.subheader("📢 Statystyki Frekwencji")
            col_att = next((c for c in df_m.columns if c.lower() in ['widzów', 'frekwencja', 'kibiców']), None)
            col_dom = next((c for c in df_m.columns if c.lower() in ['dom', 'gospodarz', 'u siebie']), None)
            col_miejsce = next((c for c in df_m.columns if c.lower() in ['miejsce rozgrywania', 'miejsce', 'stadion']),
                               None)

            if col_att and 'sezon' in df_m.columns:
                def check_is_home(row):
                    if col_dom and str(row[col_dom]).lower().strip() in ['1', '1.0', 'true', 'tak', 't',
                                                                         'dom']: return True
                    if col_miejsce and pd.notna(row[col_miejsce]):
                        if any(x in str(row[col_miejsce]).lower() for x in
                               ['bielsko', 'rekord', 'bks', 'rychlińskiego', 'czechowice']): return True
                    return False


                df_m['is_home_calc'] = df_m.apply(check_is_home, axis=1)
                df_home = df_m[df_m['is_home_calc']].copy()
                df_home['att_clean'] = pd.to_numeric(df_home[col_att], errors='coerce').fillna(0).astype(int)
                df_home_valid = df_home[df_home['att_clean'] > 0].copy()

                if not df_home_valid.empty:
                    stats = df_home_valid.groupby('sezon')['att_clean'].agg(
                        ['count', 'sum', 'mean', 'max']).reset_index()
                    stats.columns = ['Sezon', 'Mecze', 'Suma', 'Średnia', 'Max']
                    for c in ['Suma', 'Średnia', 'Max']: stats[c] = stats[c].astype(int)
                    stats = stats.sort_values('Sezon')

                    chart_mode = st.radio("Wykres:", ["Średnia", "Suma", "Rekord"], horizontal=True)
                    if HAS_PLOTLY:
                        if chart_mode == "Średnia":
                            fig = px.bar(stats, x='Sezon', y='Średnia', text='Średnia', title="Średnia na mecz",
                                         color='Średnia', color_continuous_scale='Greens')
                            fig.update_traces(textposition='outside')
                        elif chart_mode == "Suma":
                            fig = px.area(stats, x='Sezon', y='Suma', text='Suma', title="Suma kibiców", markers=True)
                            fig.update_traces(textposition="top center")
                        else:
                            fig = px.line(stats, x='Sezon', y='Max', text='Max', title="Rekord sezonu", markers=True)
                            fig.update_traces(textposition="top center")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.bar_chart(stats.set_index('Sezon')['Średnia'])

                    with st.expander("🔢 Szczegóły"):
                        st.dataframe(stats.sort_values('Sezon', ascending=False), use_container_width=True,
                                     hide_index=True)
                else:
                    st.warning("Brak danych o frekwencji domowej.")
            else:
                st.error("Brak kolumny 'widzów' lub 'sezon'.")

        # =========================================================
        # ZAKŁADKA 5: SKŁADY I RAPORTY (NAPRAWIONA LOGIKA ZMIAN)
        # =========================================================
        with tab5:
            if 'cm_selected_player' not in st.session_state: st.session_state['cm_selected_player'] = None
            if st.session_state['cm_selected_player']:
                if st.button("⬅️ Wróć do Raportu"):
                    st.session_state['cm_selected_player'] = None
                    st.rerun()
                st.divider()
                render_player_profile(st.session_state['cm_selected_player'])
            else:
                st.subheader("📝 Raporty Meczowe i Składy")
                df_det = load_details("wystepy.csv")
                if df_det is not None:
                    c_sel1, c_sel2 = st.columns([1, 2])
                    seasons = sorted(df_det['Sezon'].unique(), reverse=True)
                    sel_season = c_sel1.selectbox("Wybierz sezon:", seasons, key="sq_s_v4")

                    matches_in_season = df_det[df_det['Sezon'] == sel_season]
                    unique_matches = matches_in_season[['Mecz_Label', 'Data_Sort']].drop_duplicates().sort_values(
                        'Data_Sort', ascending=False)
                    sel_match_lbl = c_sel2.selectbox("Wybierz mecz:", unique_matches['Mecz_Label'], key="sq_m_v4")

                    if sel_match_lbl:
                        match_squad = df_det[df_det['Mecz_Label'] == sel_match_lbl].copy()
                        # Sortowanie po File_Order zapewnia kolejność z pliku (bramkarz 1.)
                        match_squad = match_squad.sort_values('File_Order')

                        match_date_str = sel_match_lbl.split('|')[0].strip()
                        cols_match_info = sel_match_lbl.split('|')[1].strip()

                        st.markdown(
                            f"""<div style="text-align: center; padding: 10px; background-color: rgba(40, 167, 69, 0.1); border-radius: 10px; margin-bottom: 20px;"><h2 style="margin:0;">{cols_match_info}</h2><p style="color: gray;">{match_date_str}</p></div>""",
                            unsafe_allow_html=True)

                        raw_scorers = ""
                        if df_m is not None and 'dt_obj' in df_m.columns:
                            try:
                                d_lbl = pd.to_datetime(match_date_str, dayfirst=True)
                                found = df_m[(df_m['dt_obj'] >= d_lbl - pd.Timedelta(days=2)) & (
                                            df_m['dt_obj'] <= d_lbl + pd.Timedelta(days=2))]
                                if not found.empty and 'strzelcy' in found.columns:
                                    raw_scorers = found.iloc[0]['strzelcy']
                            except:
                                pass

                        if raw_scorers and raw_scorers != '-':
                            st.markdown(
                                f"<div style='text-align: center; margin-bottom: 20px;'>{format_scorers_html(raw_scorers)}</div>",
                                unsafe_allow_html=True)

                        minutes_map = get_minutes_map(raw_scorers)

                        # --- NAPRAWIONA LOGIKA ZMIAN (BUFOR CZASOWY +/- 1 min) ---
                        subs_out_list = []
                        subs_out_df = match_squad[match_squad['Status'].isin(['Zszedł', 'Czerwona kartka'])]
                        for _, row in subs_out_df.iterrows():
                            subs_out_list.append({
                                'minuta': int(row.get('Minuta_Zmiany_Calc', 0)),
                                'nazwisko': row['Zawodnik_Clean'],
                                'uzyty': False
                            })


                        def get_sub_out_name(minuta_wejscia):
                            # Szukamy idealnego dopasowania
                            for item in subs_out_list:
                                if not item['uzyty'] and item['minuta'] == minuta_wejscia:
                                    item['uzyty'] = True;
                                    return item['nazwisko']
                            # Szukamy +/- 1 minuta (błąd zapisu)
                            for item in subs_out_list:
                                if not item['uzyty'] and abs(item['minuta'] - minuta_wejscia) <= 1:
                                    item['uzyty'] = True;
                                    return item['nazwisko']
                            return None


                        def render_player_row(row, is_bench=False):
                            try:
                                c_num, c_name, c_info = st.columns([1, 3, 3])
                                mins_played = int(row.get('Minuty', 0))
                                minute_event = int(row.get('Minuta_Zmiany_Calc', 0))

                                with c_num:
                                    if is_bench:
                                        st.caption(f"{minute_event}'")
                                    else:
                                        st.write(f"⏱️ {mins_played}'")

                                name = row['Zawodnik_Clean']
                                with c_name:
                                    if st.button(f"{name}",
                                                 key=f"btn_{sel_match_lbl}_{name}_{is_bench}_{st.session_state['uploader_key']}_{row.name}",
                                                 use_container_width=True):
                                        st.session_state['cm_selected_player'] = name
                                        st.rerun()

                                events = []
                                clean_name = str(name).lower().strip()
                                txt_details = next(
                                    (v for k, v in minutes_map.items() if k in clean_name or clean_name in k), "")
                                db_goals = int(pd.to_numeric(row.get('Gole'), errors='coerce') or 0)

                                if txt_details:
                                    icon = "⚽"
                                    if "(k)" in txt_details: icon = "⚽🥅"
                                    if "(sam.)" in txt_details: icon = "🔴 (sam.)"
                                    events.append(
                                        f"<span style='color:green; font-weight:bold;'>{icon} {txt_details}</span>")
                                elif db_goals > 0:
                                    icon_str = "⚽" * db_goals if db_goals < 4 else f"{db_goals}x⚽"
                                    events.append(f"<span style='color:green; font-weight:bold;'>{icon_str}</span>")

                                yellow = int(pd.to_numeric(row.get('Żółte'), errors='coerce') or 0)
                                red = int(pd.to_numeric(row.get('Czerwone'), errors='coerce') or 0)
                                if yellow > 0: events.append(f"🟨{'x' + str(yellow) if yellow > 1 else ''}")
                                if red > 0: events.append("🟥 CZERWONA")

                                status = row.get('Status', '')
                                if status == 'Wszedł':
                                    out_player = get_sub_out_name(minute_event)
                                    if out_player:
                                        events.append(
                                            f"<span style='background-color:#007bff; color:white; padding: 2px 6px; border-radius:4px; font-size:0.8em;'>⬅️ za: {out_player}</span>")
                                    else:
                                        events.append("⬆️ Wejście")
                                elif status == 'Zszedł':
                                    events.append("⬇️ Zejście")

                                with c_info:
                                    if events: st.markdown(" ".join(events), unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Błąd wiersza: {e}")


                        starters = match_squad[
                            match_squad['Status'].isin(['Cały mecz', 'Zszedł', 'Czerwona kartka', 'Grał'])]
                        subs = match_squad[match_squad['Status'] == 'Wszedł'].sort_values('Minuta_Zmiany_Calc')

                        c_l, c_r = st.columns(2)
                        with c_l:
                            st.markdown("### 🏟️ Wyjściowa XI")
                            if not starters.empty:
                                for _, r in starters.iterrows(): render_player_row(r, False)
                            else:
                                st.info("Brak danych.")
                        with c_r:
                            st.markdown("### 🔄 Rezerwowi (Zmiany)")
                            if not subs.empty:
                                for _, r in subs.iterrows(): render_player_row(r, True)
                            else:
                                st.caption("Brak zmian.")
                else:
                    st.error("Brak pliku wystepy.csv")

elif opcja == "🏆 Rekordy & TOP":
    st.header("🏆 Sala Chwały i Rekordy TSP")

    # Ładowanie danych
    df_p = load_data("pilkarze.csv")
    # Upewnij się, że używasz poprawionej funkcji load_details z poprzedniego kroku!
    df_w = load_details("wystepy.csv")
    df_s = load_data("strzelcy.csv")
    df_m = load_data("mecze.csv")


    # Funkcja pomocnicza: Numeracja i Medale
    def add_rank_medals(df_in):
        if df_in.empty: return df_in
        df_out = df_in.copy().reset_index(drop=True)
        df_out.index = df_out.index + 1  # Numeracja od 1

        def get_rank_label(idx):
            if idx == 1: return "🥇 1."
            if idx == 2: return "🥈 2."
            if idx == 3: return "🥉 3."
            return f"{idx}."

        df_out.insert(0, 'Miejsce', df_out.index.map(get_rank_label))
        return df_out


    if df_p is None or df_w is None:
        st.error("Brak plików danych (pilkarze.csv lub wystepy.csv).")
    else:
        # --- PRZYGOTOWANIE DANYCH ---

        # 1. PIŁKARZE (SUMA MECZÓW)
        col_s = 'SUMA'
        if 'SUMA' not in df_p.columns:
            if 'mecze' in df_p.columns:
                col_s = 'mecze'
            elif 'liczba' in df_p.columns:
                col_s = 'liczba'

        if col_s in df_p.columns:
            if isinstance(df_p[col_s], pd.DataFrame): df_p[col_s] = df_p[col_s].iloc[:, 0]
            df_p[col_s] = pd.to_numeric(df_p[col_s], errors='coerce').fillna(0).astype(int)

            # Liczymy mecze z detali, żeby uzupełnić braki
            if 'Zawodnik_Clean' in df_w.columns:
                matches_real_dict = df_w['Zawodnik_Clean'].value_counts().to_dict()
                df_p['Mecze_Calc'] = df_p['imię i nazwisko'].map(matches_real_dict).fillna(0).astype(int)
                df_p['Total_Matches'] = df_p[[col_s, 'Mecze_Calc']].max(axis=1)
            else:
                df_p['Total_Matches'] = df_p[col_s]
        else:
            df_p['Total_Matches'] = 0

        # Unikalna lista z flagami
        df_p_uniq = df_p.sort_values('Total_Matches', ascending=False).drop_duplicates(subset=['imię i nazwisko'],
                                                                                       keep='first')
        df_p_uniq = prepare_flags(df_p_uniq)

        # 2. STRZELCY (SUMA GOLI)
        top_scorers = pd.DataFrame()
        if df_s is not None:
            top_scorers = df_s.groupby(['imię i nazwisko', 'kraj'], as_index=False)['gole'].sum()
            top_scorers = top_scorers.sort_values('gole', ascending=False).head(10)
            top_scorers = prepare_flags(top_scorers, 'kraj')
            top_scorers = add_rank_medals(top_scorers)

        # --- ZAKŁADKI ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["👤 Legendy", "🏟️ Rekordy Meczowe", "📅 Rekordy Sezonowe", "🤝 Duety", "🟥 Kartki"])

        # ==========================================
        # TAB 1: PIŁKARZE (WYSTĘPY, GOLE, WIEK)
        # ==========================================
        with tab1:
            st.subheader("Legendy Indywidualne")
            col_apps, col_goals = st.columns(2)

            with col_apps:
                st.markdown("#### 👕 Najwięcej Występów")
                top_apps = df_p_uniq.head(10)
                top_apps = add_rank_medals(top_apps)
                st.dataframe(top_apps[['Miejsce', 'Flaga', 'imię i nazwisko', 'Total_Matches']], hide_index=True,
                             use_container_width=True,
                             column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                            "Total_Matches": st.column_config.NumberColumn("Mecze")})

            with col_goals:
                st.markdown("#### ⚽ Najlepsi Strzelcy")
                if not top_scorers.empty:
                    st.dataframe(top_scorers[['Miejsce', 'Flaga', 'imię i nazwisko', 'gole']], hide_index=True,
                                 use_container_width=True,
                                 column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                                "gole": st.column_config.NumberColumn("Gole")})

            st.divider()

            # Rekordy Wiekowe
            if 'Data_Sort' in df_w.columns:
                def calc_age_days(row, date_col, dob_col):
                    try:
                        born = pd.to_datetime(row[dob_col], dayfirst=True)
                        event = row[date_col]
                        if pd.isna(born) or pd.isna(event): return 99999
                        return (event - born).days
                    except:
                        return 99999


                # Merge występy + data urodzenia
                df_w_dates = df_w.copy()
                df_p_dates = df_p_uniq[['imię i nazwisko', 'data urodzenia', 'Flaga']].copy()
                df_p_dates['join_key'] = df_p_dates['imię i nazwisko'].astype(str).str.strip()

                merged_age = pd.merge(df_w_dates, df_p_dates, left_on='Zawodnik_Clean', right_on='join_key')

                # Obliczanie wieku
                merged_age['Age_Days'] = merged_age.apply(lambda x: calc_age_days(x, 'Data_Sort', 'data urodzenia'),
                                                          axis=1)
                merged_age['Wiek_Txt'] = merged_age['Age_Days'].apply(
                    lambda x: f"{x // 365} lat, {x % 365} dni" if 3650 < x < 25000 else "-")

                c_young, c_old = st.columns(2)

                # Najmłodsi
                min_idx = merged_age.groupby('Zawodnik_Clean')['Age_Days'].idxmin()
                debuts = merged_age.loc[min_idx].sort_values('Age_Days')
                top_young = debuts[debuts['Age_Days'] > 3650].head(10)  # Filtr błędów (<10 lat)
                top_young = add_rank_medals(top_young)

                # Najstarsi
                max_idx = merged_age.groupby('Zawodnik_Clean')['Age_Days'].idxmax()
                veterans = merged_age.loc[max_idx].sort_values('Age_Days', ascending=False)
                top_old = veterans[veterans['Age_Days'] < 25000].head(10)  # Filtr błędów (>68 lat)
                top_old = add_rank_medals(top_old)

                with c_young:
                    st.markdown("#### 👶 Najmłodsi Debiutanci")
                    st.dataframe(top_young[['Miejsce', 'Flaga', 'Zawodnik_Clean', 'Wiek_Txt', 'Data_Sort']],
                                 hide_index=True, use_container_width=True,
                                 column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                                "Data_Sort": st.column_config.DateColumn("Data")})

                with c_old:
                    st.markdown("#### 👴 Najstarsi Zawodnicy")
                    st.dataframe(top_old[['Miejsce', 'Flaga', 'Zawodnik_Clean', 'Wiek_Txt', 'Data_Sort']],
                                 hide_index=True, use_container_width=True,
                                 column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                                "Data_Sort": st.column_config.DateColumn("Data")})

        # ==========================================
        # TAB 2: HAT-TRICKI I MECZOWE
        # ==========================================
        with tab2:
            c_win, c_high = st.columns(2)

            # A. Najwyższe zwycięstwa
            with c_win:
                st.subheader("🚀 Najwyższe Zwycięstwa")
                if df_m is not None and 'wynik' in df_m.columns:
                    def calc_goal_diff(res_str):
                        parsed = parse_result(res_str)
                        if parsed: return parsed[0] - parsed[1]
                        return -99


                    df_m['Różnica'] = df_m['wynik'].apply(calc_goal_diff)
                    top_wins = df_m.sort_values('Różnica', ascending=False).head(10)
                    top_wins = add_rank_medals(top_wins)
                    st.dataframe(top_wins[['Miejsce', 'data meczu', 'rywal', 'wynik', 'rozgrywki']], hide_index=True,
                                 use_container_width=True)

            # B. Hat-tricki
            with c_high:
                st.subheader("🎩 Najlepsze Występy (Gole)")
                if 'Gole' in df_w.columns:
                    df_w['Gole_Num'] = pd.to_numeric(df_w['Gole'], errors='coerce').fillna(0).astype(int)

                    # Sortowanie bezpieczne dla dat (stare mecze bez daty nie znikają)
                    if 'Data_Sort' in df_w.columns:
                        df_w['Data_Safe'] = df_w['Data_Sort'].fillna(pd.Timestamp('1900-01-01'))
                        best_perfs = df_w[df_w['Gole_Num'] >= 3].sort_values(['Gole_Num', 'Data_Safe'],
                                                                             ascending=[False, False]).head(10)
                    else:
                        best_perfs = df_w[df_w['Gole_Num'] >= 3].sort_values('Gole_Num', ascending=False).head(10)

                    if not best_perfs.empty:
                        best_perfs['Info'] = best_perfs['Przeciwnik'].fillna('?') + " (" + best_perfs['Wynik'].fillna(
                            '?') + ")"
                        st.dataframe(best_perfs[['Sezon', 'Data_Sort', 'Zawodnik_Clean', 'Gole_Num', 'Info']],
                                     hide_index=True, use_container_width=True,
                                     column_config={
                                         "Gole_Num": st.column_config.NumberColumn("Gole", format="%d ⚽"),
                                         "Data_Sort": st.column_config.DateColumn("Data")
                                     })
                    else:
                        st.info("Brak hat-tricków w bazie.")

            st.divider()

            # C. Frekwencja
            st.subheader("📢 Rekordy Frekwencji")
            col_att = next((c for c in df_m.columns if c in ['widzów', 'frekwencja']), None)
            if col_att:
                df_m['Att_Num'] = pd.to_numeric(df_m[col_att], errors='coerce').fillna(0).astype(int)
                top_att = df_m[df_m['Att_Num'] > 0].sort_values('Att_Num', ascending=False).head(10)
                top_att = add_rank_medals(top_att)
                st.dataframe(top_att[['Miejsce', 'data meczu', 'rywal', 'wynik', 'Att_Num']], hide_index=True,
                             use_container_width=True,
                             column_config={
                                 "Att_Num": st.column_config.ProgressColumn("Widzów", format="%d", min_value=0,
                                                                            max_value=int(top_att['Att_Num'].max()))})

        # ==========================================
        # TAB 3: SEZONY (STRZELCY, PUNKTY)
        # ==========================================
        with tab3:
            c_king, c_stat = st.columns(2)
            with c_king:
                st.subheader("👑 Królowie Strzelców (Klubowi)")
                if df_s is not None:
                    max_g = df_s.groupby('sezon')['gole'].transform('max')
                    kings = df_s[df_s['gole'] == max_g].sort_values('sezon', ascending=False)
                    kings = prepare_flags(kings)
                    st.dataframe(kings[['sezon', 'Flaga', 'imię i nazwisko', 'gole']], hide_index=True,
                                 use_container_width=True,
                                 column_config={"Flaga": st.column_config.ImageColumn("", width="small")})

            with c_stat:
                st.subheader("📈 Najlepsze Sezony (Punkty)")
                if df_m is not None:
                    season_stats = []
                    for season, group in df_m.groupby('sezon'):
                        pts, matches = 0, 0
                        for _, row in group.iterrows():
                            res = parse_result(row.get('wynik'))
                            if res:
                                matches += 1
                                if res[0] > res[1]:
                                    pts += 3
                                elif res[0] == res[1]:
                                    pts += 1
                        if matches > 0:
                            season_stats.append(
                                {'Sezon': season, 'Pkt': pts, 'Mecze': matches, 'Śr. Pkt': pts / matches})

                    df_season = pd.DataFrame(season_stats).sort_values('Śr. Pkt', ascending=False)
                    st.dataframe(df_season, hide_index=True, use_container_width=True, column_config={
                        "Śr. Pkt": st.column_config.ProgressColumn("Śr. Pkt", min_value=0, max_value=3, format="%.2f")})

        # ==========================================
        # TAB 4: DUETY
        # ==========================================
        with tab4:
            st.subheader("🤝 Najlepsze Duety")
            if df_w is not None and 'Mecz_Label' in df_w.columns:
                from itertools import combinations
                from collections import Counter

                match_groups = df_w.groupby('Mecz_Label')['Zawodnik_Clean'].apply(list)
                pair_counter = Counter()

                for players in match_groups:
                    players = sorted(players)
                    for pair in combinations(players, 2):
                        pair_counter[pair] += 1

                if pair_counter:
                    top_pairs = pair_counter.most_common(20)
                    data_pairs = [{'Zawodnik 1': p1, 'Zawodnik 2': p2, 'Wspólne Mecze': count} for (p1, p2), count in
                                  top_pairs]
                    df_pairs = pd.DataFrame(data_pairs)
                    df_pairs = add_rank_medals(df_pairs)

                    # Dodanie flag
                    flag_map = df_p_uniq.set_index('imię i nazwisko')['Flaga'].to_dict()
                    df_pairs['F1'] = df_pairs['Zawodnik 1'].map(flag_map)
                    df_pairs['F2'] = df_pairs['Zawodnik 2'].map(flag_map)

                    st.dataframe(df_pairs[['Miejsce', 'F1', 'Zawodnik 1', 'F2', 'Zawodnik 2', 'Wspólne Mecze']],
                                 hide_index=True, use_container_width=True,
                                 column_config={
                                     "F1": st.column_config.ImageColumn("", width="small"),
                                     "F2": st.column_config.ImageColumn("", width="small"),
                                     "Wspólne Mecze": st.column_config.ProgressColumn(format="%d", min_value=0,
                                                                                      max_value=int(df_pairs[
                                                                                                        'Wspólne Mecze'].max()))
                                 })
                else:
                    st.warning("Za mało danych, by obliczyć duety.")

        # ==========================================
        # TAB 5: KARTKI (Z LOGIEM)
        # ==========================================
        with tab5:
            st.subheader("🟥 Kartki i Kary")
            if df_w is not None:
                df_w['Żółte'] = pd.to_numeric(df_w['Żółte'], errors='coerce').fillna(0).astype(int)
                df_w['Czerwone'] = pd.to_numeric(df_w['Czerwone'], errors='coerce').fillna(0).astype(int)

                cards_agg = df_w.groupby('Zawodnik_Clean').agg(
                    {'Żółte': 'sum', 'Czerwone': 'sum', 'Mecz_Label': 'count'}).reset_index()

                # Merge flagi
                df_p_flags = df_p_uniq[['imię i nazwisko', 'Flaga']].copy()
                df_p_flags['join_key'] = df_p_flags['imię i nazwisko'].astype(str).str.strip()
                cards_agg = pd.merge(cards_agg, df_p_flags, left_on='Zawodnik_Clean', right_on='join_key', how='left')

                col_y, col_r = st.columns(2)
                with col_y:
                    st.markdown("#### 🟨 Najwięcej Żółtych")
                    top_y = cards_agg.sort_values('Żółte', ascending=False).head(10)
                    top_y = add_rank_medals(top_y)
                    st.dataframe(top_y[['Miejsce', 'Flaga', 'Zawodnik_Clean', 'Żółte']], hide_index=True,
                                 use_container_width=True,
                                 column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                                "Żółte": st.column_config.NumberColumn("Żółte", format="%d 🟨")})

                with col_r:
                    st.markdown("#### 🟥 Najwięcej Czerwonych")
                    top_r = cards_agg[cards_agg['Czerwone'] > 0].sort_values(['Czerwone', 'Żółte'],
                                                                             ascending=[False, False]).head(10)
                    top_r = add_rank_medals(top_r)
                    st.dataframe(top_r[['Miejsce', 'Flaga', 'Zawodnik_Clean', 'Czerwone']], hide_index=True,
                                 use_container_width=True,
                                 column_config={"Flaga": st.column_config.ImageColumn("", width="small"),
                                                "Czerwone": st.column_config.NumberColumn("Czerwone", format="%d 🟥")})

                st.divider()

                # --- 2. LOG HISTORII CZERWONYCH KARTEK (TO PRZYWRÓCONE) ---
                st.markdown("### 📜 Kronika Czerwonych Kartek")
                red_log = df_w[df_w['Czerwone'] > 0].copy()

                if not red_log.empty:
                    if 'Data_Sort' in red_log.columns:
                        red_log = red_log.sort_values('Data_Sort', ascending=False)

                    # Merge z flagami dla ładnego wyglądu
                    red_log = pd.merge(red_log, df_p_flags, left_on='Zawodnik_Clean', right_on='join_key', how='left')

                    st.dataframe(
                        red_log[['Flaga', 'Zawodnik_Clean', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Sezon']],
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Flaga": st.column_config.ImageColumn("", width="small"),
                            "Data_Sort": st.column_config.DateColumn("Data"),
                            "Zawodnik_Clean": st.column_config.TextColumn("Ukarany Zawodnik")
                        }
                    )
                else:
                    st.info("Wspaniale! Brak czerwonych kartek w historii występów.")

            else:
                st.error("Brak pliku wystepy.csv do analizy kartek.")

        # ==========================================
        # TAB 5: KARTKI I KARY (NOWOŚĆ - BRUTALE)
        # ==========================================
        with tab5:
            st.subheader("🟥 Kartki i Kary")

            if df_w is not None:
                # Konwersja na liczby
                df_w['Żółte'] = pd.to_numeric(df_w['Żółte'], errors='coerce').fillna(0).astype(int)
                df_w['Czerwone'] = pd.to_numeric(df_w['Czerwone'], errors='coerce').fillna(0).astype(int)

                # --- 1. NAJWIĘKSI BRUTALE (RANKING) ---
                col_y_rank, col_r_rank = st.columns(2)

                # Agregacja per zawodnik
                cards_agg = df_w.groupby('Zawodnik_Clean').agg({
                    'Żółte': 'sum',
                    'Czerwone': 'sum',
                    'Mecz_Label': 'count'  # Liczba meczów
                }).reset_index()

                # Merge z flagami
                df_p_flags = df_p_uniq[['imię i nazwisko', 'Flaga']].copy()
                df_p_flags['join_key'] = df_p_flags['imię i nazwisko'].astype(str).str.strip()
                cards_agg = pd.merge(cards_agg, df_p_flags, left_on='Zawodnik_Clean', right_on='join_key', how='left')

                with col_y_rank:
                    st.markdown("#### 🟨 Najwięcej Żółtych Kartek")
                    top_yellow = cards_agg.sort_values('Żółte', ascending=False).head(10)
                    st.dataframe(
                        top_yellow[['Flaga', 'Zawodnik_Clean', 'Żółte', 'Mecz_Label']],
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Flaga": st.column_config.ImageColumn("", width="small"),
                            "Żółte": st.column_config.NumberColumn("Żółte", format="%d 🟨"),
                            "Mecz_Label": st.column_config.NumberColumn("Mecze", help="Liczba rozegranych meczów")
                        }
                    )

                with col_r_rank:
                    st.markdown("#### 🟥 Najwięcej Czerwonych Kartek")
                    top_red = cards_agg.sort_values(['Czerwone', 'Żółte'], ascending=[False, False]).head(10)
                    # Filtrujemy, żeby pokazać tylko tych co mają > 0 czerwonych
                    top_red = top_red[top_red['Czerwone'] > 0]

                    if not top_red.empty:
                        st.dataframe(
                            top_red[['Flaga', 'Zawodnik_Clean', 'Czerwone', 'Mecz_Label']],
                            hide_index=True, use_container_width=True,
                            column_config={
                                "Flaga": st.column_config.ImageColumn("", width="small"),
                                "Czerwone": st.column_config.NumberColumn("Czerwone", format="%d 🟥"),
                                "Mecz_Label": st.column_config.NumberColumn("Mecze")
                            }
                        )
                    else:
                        st.info("Brak czerwonych kartek w bazie.")

                st.divider()

                # --- 2. LOG HISTORII CZERWONYCH KARTEK ---
                st.markdown("### 📜 Kronika Czerwonych Kartek")
                red_log = df_w[df_w['Czerwone'] > 0].copy()

                if not red_log.empty:
                    if 'Data_Sort' in red_log.columns:
                        red_log = red_log.sort_values('Data_Sort', ascending=False)

                    # Merge z flagami dla ładnego wyglądu
                    red_log = pd.merge(red_log, df_p_flags, left_on='Zawodnik_Clean', right_on='join_key', how='left')

                    st.dataframe(
                        red_log[['Flaga', 'Zawodnik_Clean', 'Data_Sort', 'Przeciwnik', 'Wynik', 'Sezon']],
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Flaga": st.column_config.ImageColumn("", width="small"),
                            "Data_Sort": st.column_config.DateColumn("Data"),
                            "Zawodnik_Clean": st.column_config.TextColumn("Ukarany Zawodnik")
                        }
                    )
                else:
                    st.info("Wspaniale! Brak czerwonych kartek w historii występów.")

            else:
                st.error("Brak pliku wystepy.csv do analizy kartek.")
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
                                            gf += res[0]; ga += res[1]
                                            if res[0] > res[1]: w += 1; pts_sum += 3
                                            elif res[0] == res[1]: d += 1; pts_sum += 1
                                            else: l += 1

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
                                    fig.add_trace(go.Bar(x=res_df.index, y=res_df['Średnia Pkt'], name='Średnia Pkt', marker_color='#2ecc71'))
                                    fig.add_trace(go.Bar(x=res_df.index, y=res_df['% Zwycięstw'] / 33, name='Index Wygranych', marker_color='#3498db', opacity=0.5))
                                    fig.update_layout(title="Porównanie efektywności", barmode='group')
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("Nie znaleziono meczów.")
                        else:
                            st.error("Brak kolumny z datą w mecze.csv")