import streamlit as st
import pandas as pd
import datetime
import re
import os

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="TSP Baza Danych", 
    layout="wide", 
    page_icon="⚽"
)

# --- 2. LOGOWANIE I SESJA ---
USERS = {
    "Djero": "TSP1995", 
    "KKowalski": "Tsp2025", 
    "PPorebski": "TSP2025", 
    "MCzerniak": "TSP2025", 
    "SJaszczurowski": "TSP2025", 
    "guest": "123456789"
}

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

def login():
    st.title("🔒 Panel Logowania TSP")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Użytkownik")
        p = st.text_input("Hasło", type="password")
        if st.button("Zaloguj", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state['logged_in'] = True
                st.session_state['username'] = u  # ZAPAMIĘTUJEMY UŻYTKOWNIKA
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

# --- MAPOWANIE KRAJÓW ---
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

# --- FUNKCJE POMOCNICZE I ADMINA ---

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
    if not os.path.exists(filename):
        return None
    try: df = pd.read_csv(filename, encoding='utf-8')
    except: 
        try: df = pd.read_csv(filename, encoding='windows-1250')
        except: return None
    
    df = df.fillna("-")
    df.columns = [c.strip().lower() for c in df.columns]
    
    cols_drop = [c for c in df.columns if 'lp' in c]
    if cols_drop: df = df.drop(columns=cols_drop)

    if 'kolejka' in df.columns:
        def format_kolejka(x):
            s = str(x).strip()
            if s.replace('.','',1).isdigit():
                try:
                    val = int(float(s))
                    return f"{val:02d}"
                except: return s
            return s
        df['kolejka'] = df['kolejka'].apply(format_kolejka)
        
    if '1999/20' in df.columns:
        df.rename(columns={'1999/20': '1999/00'}, inplace=True)

    season_cols = [c for c in df.columns if re.match(r'^\d{4}/\d{2}$', c)]
    for col in season_cols:
        if df[col].dtype == object and not df[col].astype(str).str.contains('/').any(): 
             pass 
        else:
             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    int_candidates = [
        'wiek', 'suma', 'liczba', 'mecze', 'gole', 'punkty', 'minuty', 'numer', 
        'asysty', 'żółte kartki', 'czerwone kartki', 'gole samobójcze', 
        'asysta 2. stopnia', 'sprokurowany karny', 'wywalczony karny', 
        'karny', 'niestrzelony karny', 'główka', 'lewa', 'prawa', 
        'czyste konta', 'obronione karne', 'kanadyjka'
    ]
    for col in df.columns:
        if col in int_candidates:
            try:
                temp = df[col].replace('-', 0)
                temp = pd.to_numeric(temp, errors='coerce').fillna(0)
                df[col] = temp.astype(int)
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
            cols.remove('Flaga')
            cols.insert(cols.index('Narodowość') + 1, 'Flaga')
            df = df[cols]
    return df

def parse_result(val):
    if not isinstance(val, str): return None
    val = val.replace('-', ':').replace(' ', '')
    if ':' in val:
        try:
            p = val.split(':')
            return int(p[0]), int(p[1])
        except: return None
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
    if not isinstance(scorers_str, str) or pd.isna(scorers_str) or scorers_str == '-':
        return {}
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

# --- NOWE FUNKCJE: WIEK I URODZINY ---
def get_age_and_birthday(birth_date_val):
    """Oblicza wiek i sprawdza czy są urodziny."""
    if pd.isna(birth_date_val) or str(birth_date_val) in ['-', '', 'nan']:
        return None, False
    
    formats = ['%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d']
    dt = None
    for f in formats:
        try:
            dt = pd.to_datetime(birth_date_val, format=f)
            break
        except: continue
        
    if dt is None: # Fallback
        try: dt = pd.to_datetime(birth_date_val)
        except: return None, False

    today = datetime.date.today()
    born = dt.date()
    
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    is_birthday = (today.month == born.month) and (today.day == born.day)
    
    return age, is_birthday

# --- ADMIN ACTIONS (Tylko dla Djero) ---
def admin_save_csv(filename, new_data_dict):
    """Prosta funkcja do dopisywania wiersza do CSV"""
    try:
        df = pd.read_csv(filename)
        new_row = pd.DataFrame([new_data_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(filename, index=False)
        st.cache_data.clear() # Czyścimy cache żeby widzieć zmiany
        return True
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")
        return False

# --- MENU ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Moduł:", [
    "Aktualny Sezon (25/26)", 
    "Centrum Zawodników", 
    "Centrum Meczowe", 
    "Trenerzy"
])
st.sidebar.divider()

# --- PANEL ADMINISTRATORA (TYLKO DLA DJERO) ---
if st.session_state.get('username') == 'Djero':
    st.sidebar.markdown("### 🛠️ Panel Admina (Djero)")
    
    with st.sidebar.expander("➕ Dodaj Piłkarza"):
        with st.form("add_player_form"):
            a_imie = st.text_input("Imię i Nazwisko")
            a_kraj = st.text_input("Kraj", value="Polska")
            a_poz = st.selectbox("Pozycja", ["Bramkarz", "Obrońca", "Pomocnik", "Napastnik"])
            a_data = st.date_input("Data urodzenia", min_value=datetime.date(1970,1,1))
            if st.form_submit_button("Zapisz w bazie"):
                if a_imie:
                    # Zakładamy strukturę pliku pilkarze.csv
                    success = admin_save_csv("pilkarze.csv", {
                        "imię i nazwisko": a_imie,
                        "kraj": a_kraj,
                        "pozycja": a_poz,
                        "data urodzenia": str(a_data),
                        "suma": 0
                    })
                    if success: st.success(f"Dodano: {a_imie}")
                else:
                    st.warning("Podaj nazwisko")

    with st.sidebar.expander("⚽ Dodaj Wynik"):
        with st.form("add_result_form"):
            a_sezon = st.text_input("Sezon", value="2025/26")
            a_rywal = st.text_input("Rywal")
            a_wynik = st.text_input("Wynik (np. 2:1)")
            a_data_m = st.date_input("Data meczu")
            if st.form_submit_button("Zapisz mecz"):
                success = admin_save_csv("mecze.csv", {
                    "sezon": a_sezon,
                    "rywal": a_rywal,
                    "wynik": a_wynik,
                    "data meczu": str(a_data_m)
                })
                if success: st.success("Dodano mecz!")

    with st.sidebar.expander("🔄 Aktualizuj Sezon"):
        st.info("Tutaj możesz dodać funkcję edycji tabeli 25_26.csv (wymagałoby edytora tabeli).")

    st.sidebar.divider()

if st.sidebar.button("Wyloguj"): logout()

# --- MODUŁY ---

if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Kadra 2025/2026")
    df = load_data("25_26.csv")
    
    if df is not None:
        # --- 1. OBLICZANIE KPI ---
        
        # Logika Młodzieżowca
        df['is_youth'] = False
        if 'status' in df.columns:
            df['is_youth'] = df['status'].astype(str).str.contains(r'\(M\)', case=False, regex=True)
            df.loc[df['is_youth'], 'imię i nazwisko'] = "Ⓜ️ " + df.loc[df['is_youth'], 'imię i nazwisko']

        # Logika Kanadyjska (Gole + Asysty)
        if 'gole' in df.columns and 'asysty' in df.columns:
            df['kanadyjka'] = df['gole'] + df['asysty']

        # Statystyki ogólne
        total_players = len(df)
        avg_age = f"{df['wiek'].mean():.1f}" if 'wiek' in df.columns else "-"
        youth_count = df['is_youth'].sum()
        
        # Obcokrajowcy (liczymy na danych surowych przed zmianą nagłówka na Narodowość)
        foreigners = 0
        nat_col_raw = 'narodowość' if 'narodowość' in df.columns else ('kraj' if 'kraj' in df.columns else None)
        if nat_col_raw:
            foreigners = df[~df[nat_col_raw].str.contains('Polska', case=False, na=False)].shape[0]

        top_scorer = "-"
        if 'gole' in df.columns:
            max_g = df['gole'].max()
            if max_g > 0:
                best = df[df['gole'] == max_g].iloc[0]
                clean_name = best['imię i nazwisko'].replace('Ⓜ️ ', '')
                top_scorer = f"{clean_name} ({max_g})"

        # --- 2. PRZYGOTOWANIE WIDOKU ---
        df = prepare_flags(df)

        # Wyświetlanie metryk
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Liczba Zawodników", total_players)
        k2.metric("Średnia Wieku", avg_age)
        k3.metric("Obcokrajowcy", foreigners)
        k4.metric("Młodzieżowcy", youth_count)
        k5.metric("Najlepszy Strzelec", top_scorer)
        
        st.divider()

        # --- 3. Filtry i Sterowanie Widokiem ---
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            search_q = st.text_input("🔍 Szukaj (Nazwisko/Pozycja):", placeholder="np. Kowalski")
        with c2:
            view_mode = st.selectbox("Tryb Widoku:", ["Tabela Szczegółowa", "Podział na Formacje"])
        with c3:
            sort_by = st.selectbox("Sortuj wg:", ["Nr", "Wiek", "Mecze", "Gole", "Kanadyjka"], index=0)
        with c4:
            show_only_youth = st.checkbox("Tylko Młodzieżowcy", value=False)

        # Filtrowanie danych
        df_view = df.copy()
        
        if show_only_youth:
            df_view = df_view[df_view['is_youth']]
            
        if search_q:
            df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]
        
        # Sortowanie główne
        sort_map = {
            'Nr': 'numer', 'Wiek': 'wiek', 'Mecze': 'mecze', 
            'Gole': 'gole', 'Kanadyjka': 'kanadyjka'
        }
        col_sort = sort_map.get(sort_by)
        if col_sort and col_sort in df_view.columns:
            ascending = True if col_sort in ['numer', 'wiek'] else False
            df_view = df_view.sort_values(col_sort, ascending=ascending)

        # --- 4. Prezentacja Danych (Column Config) ---
        col_config = {
            "Flaga": st.column_config.ImageColumn("Kraj", width="small"),
            "imię i nazwisko": st.column_config.TextColumn("Zawodnik", width="medium"),
            "pozycja": st.column_config.TextColumn("Poz.", width="small"),
            "wiek": st.column_config.NumberColumn("Wiek", format="%d"),
            "numer": st.column_config.TextColumn("Nr", width="small"),
            
            # Główne
            "mecze": st.column_config.ProgressColumn("Mecze", format="%d", min_value=0, max_value=int(df['mecze'].max()) if 'mecze' in df.columns else 35),
            "minuty": st.column_config.NumberColumn("Minuty", format="%d'"),
            "gole": st.column_config.ProgressColumn("Gole", format="%d ⚽", min_value=0, max_value=int(df['gole'].max()) if 'gole' in df.columns else 20),
            "asysty": st.column_config.ProgressColumn("Asysty", format="%d 🅰️", min_value=0, max_value=15),
            "kanadyjka": st.column_config.NumberColumn("Kanadyjka", format="%d 🍁", help="Gole + Asysty"),
            
            # Kartki
            "żółte kartki": st.column_config.NumberColumn("ŻK", format="%d 🟨"),
            "czerwone kartki": st.column_config.NumberColumn("CK", format="%d 🟥"),
            
            # Szczegółowe - Atak
            "gole samobójcze": st.column_config.NumberColumn("Samobój.", format="%d"),
            "asysta 2. stopnia": st.column_config.NumberColumn("As. 2 st.", format="%d"),
            "wywalczony karny": st.column_config.NumberColumn("Wyw. K", format="%d"),
            
            # Szczegółowe - Obrona
            "sprokurowany karny": st.column_config.NumberColumn("Sprok. K", format="%d"),
            "czyste konta": st.column_config.NumberColumn("Czyste K.", format="%d 🧤"),
            "obronione karne": st.column_config.NumberColumn("Obr. K", format="%d 🧤"),
            
            # Karne
            "karny": st.column_config.NumberColumn("Karne (G)", format="%d"),
            "niestrzelony karny": st.column_config.NumberColumn("Karne (X)", format="%d"),
            
            # Sposób strzelenia
            "główka": st.column_config.NumberColumn("Głową", format="%d"),
            "lewa": st.column_config.NumberColumn("Lewą", format="%d"),
            "prawa": st.column_config.NumberColumn("Prawą", format="%d"),
        }

        preferred_order = [
            'numer', 'imię i nazwisko', 'Flaga', 'pozycja', 'wiek',
            'mecze', 'minuty', 'gole', 'asysty', 'kanadyjka',
            'żółte kartki', 'czerwone kartki',
            'gole samobójcze', 'asysta 2. stopnia', 'wywalczony karny', 'sprokurowany karny',
            'karny', 'niestrzelony karny',
            'główka', 'lewa', 'prawa',
            'czyste konta', 'obronione karne'
        ]
        
        final_cols = [c for c in preferred_order if c in df_view.columns]
        hidden_cols = ['narodowość', 'flaga', 'is_youth', 'status'] 
        remaining = [c for c in df_view.columns if c not in final_cols and c not in hidden_cols]
        final_cols.extend(remaining)

        if view_mode == "Tabela Szczegółowa":
            df_view.index = range(1, len(df_view)+1)
            st.dataframe(
                df_view[final_cols], 
                use_container_width=True, 
                column_config=col_config,
                height=(len(df_view) + 1) * 35 + 3 
            )
            
        else: # Podział na Formacje
            if 'pozycja' in df_view.columns:
                formacje = sorted(df_view['pozycja'].astype(str).unique())
                
                # Inteligentne sortowanie formacji (szukanie po fragmencie słowa)
                def get_priority(pos):
                    pos_lower = str(pos).lower()
                    if 'bramkarz' in pos_lower: return 0
                    if 'obroń' in pos_lower or 'obron' in pos_lower: return 1
                    if 'pomoc' in pos_lower: return 2
                    if 'napast' in pos_lower: return 3
                    return 10
                
                formacje.sort(key=get_priority)

                for formacja in formacje:
                    sub_df = df_view[df_view['pozycja'] == formacja]
                    if not sub_df.empty:
                        with st.expander(f"🟢 {formacja} ({len(sub_df)})", expanded=True):
                            sub_df.index = range(1, len(sub_df)+1)
                            # Pokaż minuty, ukryj status
                            cols_f_pref = ['numer', 'imię i nazwisko', 'Flaga', 'wiek', 'mecze', 'minuty', 'gole', 'asysty', 'kanadyjka', 'żółte kartki']
                            cols_f = [c for c in cols_f_pref if c in sub_df.columns]
                            
                            st.dataframe(
                                sub_df[cols_f],
                                use_container_width=True,
                                hide_index=True,
                                column_config=col_config
                            )
            else:
                st.info("Brak kolumny 'pozycja' w pliku - wyświetlam tabelę główną.")
                st.dataframe(df_view[final_cols], use_container_width=True, column_config=col_config)

    else:
        st.error("⚠️ Brak pliku '25_26.csv'. Wgraj plik z kadrą, aby zobaczyć statystyki.")

elif opcja == "Centrum Zawodników":
    st.header("🏃 Centrum Zawodników TSP")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Baza Zawodników", "Strzelcy", "Klub 100", "Transfery", "Młoda Ekstraklasa"])

    # --- TAB 1: BAZA ZAWODNIKÓW ---
    with tab1:
        st.subheader("Baza Zawodników")
        df_long = load_data("pilkarze.csv")
        df_strzelcy = load_data("strzelcy.csv")
        df_mecze = load_data("mecze.csv") 
        
        if df_long is not None:
            if 'suma' in df_long.columns:
                df_long['suma'] = pd.to_numeric(df_long['suma'], errors='coerce').fillna(0).astype(int)
                df_unique_view = df_long.sort_values('suma', ascending=False).drop_duplicates(subset=['imię i nazwisko'])
            else:
                df_unique_view = df_long.drop_duplicates(subset=['imię i nazwisko'])

            c1, c2 = st.columns([2, 1])
            with c1: search = st.text_input("Szukaj zawodnika:")
            with c2: obcy = st.checkbox("Tylko obcokrajowcy", key="obcy_search_base")
            
            if search:
                df_unique_view = df_unique_view[df_unique_view['imię i nazwisko'].astype(str).str.contains(search, case=False)]
            if obcy and 'narodowość' in df_unique_view.columns:
                 df_unique_view = df_unique_view[~df_unique_view['narodowość'].str.contains("Polska", na=False)]

            df_unique_view = prepare_flags(df_unique_view)

            st.markdown("### 📋 Lista Zawodników")
            cols_base = ['imię i nazwisko', 'Flaga', 'Narodowość', 'pozycja', 'suma']
            cols_base = [c for c in cols_base if c in df_unique_view.columns]
            
            st.dataframe(
                df_unique_view[cols_base], 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                    "suma": st.column_config.NumberColumn("Suma Meczów", format="%d")
                }
            )

            st.divider()
            st.subheader("📈 Profil i Analiza")
            
            dostepni_do_wykresu = df_unique_view['imię i nazwisko'].tolist()
            wybrany_analiza = st.selectbox("Wybierz zawodnika do analizy:", [""] + dostepni_do_wykresu)

            if wybrany_analiza:
                # --- NOWA SEKCJA: KARTA ZAWODNIKA I URODZINY ---
                player_row = df_unique_view[df_unique_view['imię i nazwisko'] == wybrany_analiza].iloc[0]
                
                # Szukamy kolumny z datą urodzenia
                col_birth = next((c for c in player_row.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
                
                age_info = "-"
                is_bday = False
                
                if col_birth:
                    age, is_bday = get_age_and_birthday(player_row[col_birth])
                    if age: age_info = f"{age} lat"
                
                # Stylizacja Karty
                st.markdown("---")
                if is_bday:
                    st.balloons()
                    st.success(f"🎉🎂 WSZYSTKIEGO NAJLEPSZEGO! {player_row['imię i nazwisko']} kończy dzisiaj {age} lat! 🎂🎉")

                c_prof1, c_prof2 = st.columns([1, 3])
                
                with c_prof1:
                    if 'Flaga' in player_row and player_row['Flaga']:
                        st.image(player_row['Flaga'], width=100)
                    else:
                        st.markdown("👤")
                
                with c_prof2:
                    st.markdown(f"## {player_row['imię i nazwisko']}")
                    st.markdown(f"**Kraj:** {player_row.get('Narodowość', '-')}")
                    st.markdown(f"**Pozycja:** {player_row.get('pozycja', '-')}")
                    st.markdown(f"**Wiek:** {age_info}")
                    if col_birth:
                        st.caption(f"Data ur.: {player_row[col_birth]}")

                st.markdown("---")
                # ---------------------------------------------------

                player_stats = df_long[df_long['imię i nazwisko'] == wybrany_analiza].copy()
                
                gole_lista = []
                if df_strzelcy is not None and 'sezon' in df_strzelcy.columns and 'gole' in df_strzelcy.columns:
                    goals_map = df_strzelcy.set_index(['imię i nazwisko', 'sezon'])['gole'].to_dict()
                    for _, row in player_stats.iterrows():
                        sez = row['sezon']
                        g = goals_map.get((wybrany_analiza, sez), 0)
                        gole_lista.append(g)
                else:
                    gole_lista = [0] * len(player_stats)
                
                player_stats['Gole'] = gole_lista
                player_stats = player_stats.sort_values('sezon')

                if HAS_PLOTLY:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=player_stats['sezon'], y=player_stats['liczba'],
                        name='Mecze', marker_color='#3498db',
                        text=player_stats['liczba'], textposition='auto'
                    ))
                    fig.add_trace(go.Bar(
                        x=player_stats['sezon'], y=player_stats['Gole'],
                        name='Gole', marker_color='#2ecc71',
                        text=player_stats['Gole'], textposition='auto'
                    ))
                    fig.update_layout(title=f"Statystyki: {wybrany_analiza}", xaxis_title="Sezon", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)

                st.write("Tabela szczegółowa:")
                view_cols = ['sezon', 'liczba', 'Gole']
                st.dataframe(player_stats[view_cols], use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown(f"**Szczegóły goli (Lista meczów)**")
                if df_mecze is not None and 'strzelcy' in df_mecze.columns:
                    found_matches = []
                    mecze_z_golami = df_mecze[df_mecze['strzelcy'].notna() & (df_mecze['strzelcy'] != '')]
                    for idx, row in mecze_z_golami.iterrows():
                        sm = parse_scorers(row['strzelcy'])
                        if wybrany_analiza in sm:
                            found_matches.append({
                                'Sezon': row.get('sezon', '-'),
                                'Data': row.get('data meczu', '-'),
                                'Rywal': row.get('rywal', '-'),
                                'Wynik': row.get('wynik', '-'),
                                'Gole': sm[wybrany_analiza]
                            })
                    if found_matches:
                        df_g = pd.DataFrame(found_matches)
                        df_g.index = range(1, len(df_g)+1)
                        st.dataframe(df_g, use_container_width=True)
                    else:
                        st.caption("Brak szczegółowych danych o golach w bazie meczowej.")
        else:
            st.error("BŁĄD: Nie udało się wczytać pliku 'pilkarze.csv'.")

    # --- TAB 2: STRZELCY (LONG FORMAT) ---
    with tab2:
        st.subheader("⚽ Klasyfikacja Strzelców")
        df = load_data("strzelcy.csv")
        
        if df is not None and 'sezon' in df.columns and 'gole' in df.columns:
            all_seasons = sorted(df['sezon'].unique(), reverse=True)
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1: search_s = st.text_input("Szukaj strzelca:", key="search_strzelcy_tab")
            with c2: wybrane_sezony_s = st.multiselect("Filtruj wg sezonu:", all_seasons, key="multi_sezon_strzelcy")
            with c3: obcy_s = st.checkbox("Tylko obcokrajowcy", key="obcy_strzelcy_tab")

            df_view = df.copy()
            if wybrane_sezony_s: df_view = df_view[df_view['sezon'].isin(wybrane_sezony_s)]
            if search_s: df_view = df_view[df_view['imię i nazwisko'].astype(str).str.contains(search_s, case=False)]
            nat_col = 'kraj' if 'kraj' in df_view.columns else 'narodowość'
            if obcy_s and nat_col in df_view.columns:
                 df_view = df_view[~df_view[nat_col].str.contains("Polska", na=False)]

            group_cols = ['imię i nazwisko']
            if nat_col in df_view.columns: group_cols.append(nat_col)
            
            df_grouped = df_view.groupby(group_cols, as_index=False)['gole'].sum()
            df_grouped = df_grouped.rename(columns={'gole': 'Suma Goli'})
            df_grouped = df_grouped[df_grouped['Suma Goli'] > 0].sort_values('Suma Goli', ascending=False)
            df_grouped = prepare_flags(df_grouped, col=nat_col)
            df_grouped.index = range(1, len(df_grouped)+1)

            cols_show = ['imię i nazwisko', 'Flaga', 'Narodowość', 'Suma Goli']
            cols_show = [c for c in cols_show if c in df_grouped.columns]

            st.dataframe(
                df_grouped[cols_show], 
                use_container_width=True, 
                column_config={
                    "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                    "Suma Goli": st.column_config.NumberColumn("Liczba Goli", format="%d"),
                }
            )

            st.divider()
            st.subheader("📈 Historia Strzelca")
            dostepni_strzelcy = df_grouped['imię i nazwisko'].unique().tolist()
            wybrany_strzelec = st.selectbox("Wybierz strzelca:", [""] + dostepni_strzelcy)
            
            if wybrany_strzelec:
                player_history = df[df['imię i nazwisko'] == wybrany_strzelec].copy()
                player_history = player_history.sort_values('sezon')
                if not player_history.empty:
                    if HAS_PLOTLY:
                        fig = px.bar(
                            player_history, x='sezon', y='gole', text='gole',
                            title=f"Gole w sezonach: {wybrany_strzelec}",
                            color='gole', color_continuous_scale='Greens'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.bar_chart(player_history.set_index('sezon')['gole'])
                else: st.info("Brak danych.")
        else:
            st.error("Brak pliku 'strzelcy.csv' lub zła struktura pliku (wymagane kolumny: imię i nazwisko, kraj, sezon, gole).")

    # --- TAB 3: KLUB 100 ---
    with tab3:
        st.subheader("Klub 100 (Najwięcej występów)")
        df = load_data("pilkarze.csv")
        if df is not None:
            target = 'suma' if 'suma' in df.columns else next((c for c in df.columns if 'suma' in c.lower()), None)
            if target:
                df[target] = pd.to_numeric(df[target], errors='coerce').fillna(0).astype(int)
                df_uniq = df.drop_duplicates(subset=['imię i nazwisko'])
                df_uniq = df_uniq[df_uniq[target] >= 100].sort_values(target, ascending=False)
                
                if HAS_PLOTLY:
                    fig = px.bar(df_uniq.head(20), x='imię i nazwisko', y=target, text=target, title="Top 20 - Występy")
                    st.plotly_chart(fig, use_container_width=True)
                
                df_uniq = prepare_flags(df_uniq)
                df_uniq = df_uniq.rename(columns={target: 'Mecze'})
                df_uniq.index = range(1, len(df_uniq)+1)
                st.dataframe(
                    df_uniq[['imię i nazwisko', 'Flaga', 'Narodowość', 'Mecze']], 
                    use_container_width=True, 
                    column_config={
                        "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                        "Mecze": st.column_config.NumberColumn("Mecze", format="%d")
                    }
                )

    # --- TAB 4: TRANSFERY ---
    with tab4:
        st.subheader("Historia Transferów")
        df = load_data("transfery.csv")
        if df is not None:
            if 'kwota pln' in df.columns:
                df['val'] = df['kwota pln'].astype(str).str.replace(' zł', '').str.replace(' ', '').str.replace(',', '.')
                df['val'] = pd.to_numeric(df['val'], errors='coerce').fillna(0).astype(int)
                top10 = df.sort_values('val', ascending=False).head(10)
                if HAS_PLOTLY:
                    fig = px.bar(top10, x='imię i nazwisko', y='val', text='val', title="Top 10 Najdroższych Transferów (PLN)")
                    st.plotly_chart(fig, use_container_width=True)
            df = prepare_flags(df, 'narodowość')
            df.index = range(1, len(df)+1)
            st.dataframe(df.drop(columns=['val'], errors='ignore'), use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

    # --- TAB 5: ME ---
    with tab5:
        st.subheader("Młoda Ekstraklasa")
        df = load_data("me.csv")
        if df is not None:
            df = prepare_flags(df, 'narodowość')
            df.index = range(1, len(df)+1)
            st.dataframe(df, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

elif opcja == "Centrum Meczowe":
    st.header("🏟️ Centrum Meczowe")
    tab1, tab2, tab3, tab4 = st.tabs(["Historia Meczów", "Rywale (H2H)", "Frekwencja", "Statystyki Wyników"])

    with tab1:
        st.subheader("Archiwum Meczów")
        df = load_data("mecze.csv")
        if df is not None:
            if 'wynik' not in df.columns: st.error("Brak kolumny 'wynik'")
            else:
                sezony = sorted([s for s in df['sezon'].astype(str).unique() if len(s)>4], reverse=True) if 'sezon' in df.columns else []
                c1, c2 = st.columns(2)
                sel_sez = c1.selectbox("Sezon:", sezony, key="hist_sez") if sezony else None
                filt = c2.text_input("Szukaj rywala:", key="hist_rywal")
                m = df.copy()
                if sel_sez: m = m[m['sezon'] == sel_sez]
                if filt: m = m[m.astype(str).apply(lambda x: x.str.contains(filt, case=False)).any(axis=1)]
                roz = next((c for c in m.columns if c in ['rozgrywki', 'liga']), None)
                sub_tabs = st.tabs([str(r) for r in m[roz].unique()]) if roz else [st]
                datasets = [(r, m[m[roz]==r]) for r in m[roz].unique()] if roz else [("All", m)]
                for tab, (n, sub) in zip(sub_tabs, datasets):
                    with tab:
                        col_d = next((c for c in sub.columns if 'data' in c and 'sort' not in c), None)
                        if col_d: sub = sub.sort_values(col_d, ascending=False)
                        w, r_res, p = 0, 0, 0
                        for x in sub['wynik']:
                            res = parse_result(x)
                            if res:
                                if res[0]>res[1]: w+=1
                                elif res[0]<res[1]: p+=1
                                else: r_res+=1
                        st.caption(f"Bilans: ✅ {w} | ➖ {r_res} | ❌ {p}")
                        sub.index = range(1, len(sub)+1)
                        st.dataframe(sub.style.map(color_results_logic, subset=['wynik']), use_container_width=True)

    with tab2:
        st.subheader("Bilans z Rywalami")
        df = load_data("mecze.csv")
        if df is not None:
            col_r = next((c for c in df.columns if c in ['rywal', 'przeciwnik']), None)
            if col_r and 'wynik' in df.columns:
                def calc(s):
                    m = len(s); w=r=p=0; gs=ga=0
                    for x in s['wynik']:
                        res = parse_result(x)
                        if res:
                            ts, op = res
                            gs+=ts; ga+=op
                            if ts>op: w+=1
                            elif ts<op: p+=1
                            else: r+=1
                    return pd.Series({'Mecze': m, 'Z': w, 'R': r, 'P': p, 'Bramki': f"{gs}:{ga}", 'Pkt': w*3+r})

                t_h2h_1, t_h2h_2 = st.tabs(["🔎 Analiza Rywala", "📊 Tabela Wszystkich"])
                with t_h2h_1:
                    sel = st.selectbox("Wybierz rywala:", sorted(df[col_r].unique()), key="sel_h2h")
                    if sel:
                        sub = df[df[col_r] == sel].copy()
                        stats = calc(sub)
                        c1,c2,c3,c4 = st.columns(4)
                        c1.metric("Mecze", int(stats['Mecze']))
                        c2.metric("Bilans", f"{int(stats['Z'])}-{int(stats['R'])}-{int(stats['P'])}")
                        c3.metric("Bramki", stats['Bramki'])
                        st.divider()
                        st.write("Lista meczów:")
                        sub.index = range(1, len(sub)+1)
                        st.dataframe(sub.style.map(color_results_logic, subset=['wynik']), use_container_width=True)
                with t_h2h_2:
                    all_stats = df.groupby(col_r).apply(calc).reset_index().sort_values(['Pkt'], ascending=False)
                    all_stats.index = range(1, len(all_stats)+1)
                    st.dataframe(all_stats, use_container_width=True)

    with tab3:
        st.subheader("Frekwencja na stadionie")
        df = load_data("frekwencja.csv")
        if df is not None:
            col = next((c for c in df.columns if 'średnia' in c), None)
            if col and 'sezon' in df.columns:
                df['n'] = df[col].astype(str).str.replace(r'\D', '', regex=True)
                df['n'] = pd.to_numeric(df['n'], errors='coerce').fillna(0).astype(int)
                df = df.sort_values('sezon')
                c1, c2, c3 = st.columns(3)
                c1.metric("Najwyższa średnia", f"{df['n'].max():,} widzów")
                c2.metric("Najniższa średnia", f"{df['n'].min():,} widzów")
                c3.metric("Średnia ogólna", f"{int(df['n'].mean()):,} widzów")
                if HAS_PLOTLY:
                    fig = px.bar(df, x='sezon', y='n', text='n', title="Średnia frekwencja w sezonach",
                                 color='n', color_continuous_scale='Blues')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(df.set_index('sezon')['n'])
                df.index = range(1, len(df)+1)
                st.dataframe(df.drop(columns=['n'], errors='ignore'), use_container_width=True)

    with tab4:
        st.subheader("Najczęstsze wyniki")
        df = load_data("wyniki.csv")
        if df is not None: 
            st.bar_chart(df.set_index('wynik')['częstotliwość'])
            df.index = range(1, len(df)+1)
            st.dataframe(df, use_container_width=True)

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
        for c in ['mecze', 'punkty']: 
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

        t1, t2, t3 = st.tabs(["Lista Trenerów", "Rankingi", "Analiza Szczegółowa"])
        with t1:
            v = df.sort_values('początek_dt', ascending=False)
            cols = [c for c in ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'początek', 'koniec', 'mecze', 'punkty'] if c in v.columns]
            v.index = range(1, len(v)+1)
            st.dataframe(v[cols], use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
        with t2:
            agg = df.groupby(['imię i nazwisko', 'Narodowość', 'Flaga'], as_index=False)[['mecze', 'punkty']].sum()
            agg = agg.sort_values('punkty', ascending=False)
            agg.index = range(1, len(agg)+1)
            st.dataframe(agg, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
        with t3:
            trenerzy_list = sorted(df['imię i nazwisko'].unique())
            wybrany_trener = st.selectbox("Wybierz trenera:", trenerzy_list, key="sel_trener")
            if wybrany_trener:
                coach_data = df[df['imię i nazwisko'] == wybrany_trener]
                mecze_df = load_data("mecze.csv")
                if mecze_df is not None:
                    col_data = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None) or next((c for c in mecze_df.columns if 'data' in c), None)
                    if col_data:
                        mecze_df['dt'] = pd.to_datetime(mecze_df[col_data], dayfirst=True, errors='coerce')
                        mask = pd.Series([False]*len(mecze_df))
                        for _, row in coach_data.iterrows():
                            if pd.notnull(row['początek_dt']):
                                mask |= (mecze_df['dt'] >= row['początek_dt']) & (mecze_df['dt'] <= row['koniec_dt'])
                        coach_matches = mecze_df[mask].sort_values('dt')
                        if not coach_matches.empty:
                            points_list = []
                            all_scorers = {}
                            for _, m in coach_matches.iterrows():
                                r = parse_result(m['wynik'])
                                pts = 3 if r and r[0]>r[1] else (1 if r and r[0]==r[1] else 0)
                                points_list.append(pts)
                                if 'strzelcy' in m and pd.notnull(m['strzelcy']):
                                    for s, c in parse_scorers(m['strzelcy']).items(): 
                                        all_scorers[s] = all_scorers.get(s, 0) + c
                            
                            coach_matches['pts'] = points_list
                            coach_matches['rolling_avg'] = coach_matches['pts'].rolling(window=5, min_periods=1).mean()
                            
                            if HAS_PLOTLY:
                                st.plotly_chart(px.line(x=coach_matches['dt'], y=coach_matches['rolling_avg'], markers=True, title=f"Forma (śr. pkt z 5 meczów): {wybrany_trener}", labels={'y': 'Śr. pkt'}), use_container_width=True)
                            
                            if all_scorers:
                                st.write("⚽ Najlepsi strzelcy (wraz z samobójami):")
                                df_s = pd.DataFrame(list(all_scorers.items()), columns=['Zawodnik', 'Gole']).sort_values('Gole', ascending=False).reset_index(drop=True)
                                df_s.index = range(1, len(df_s)+1)
                                
                                def highlight_red(val):
                                    return 'color: #dc3545; font-weight: bold;' if val == 'Bramka samobójcza' else ''
                                
                                st.dataframe(df_s.style.map(highlight_red, subset=['Zawodnik']), use_container_width=True)
                            
                            st.write(f"Lista meczów ({len(coach_matches)}):")
                            view_c = [c for c in coach_matches.columns if c not in ['dt', 'data sortowania', 'mecz_id', 'pts', 'rolling_avg']]
                            coach_matches.index = range(1, len(coach_matches)+1)
                            st.dataframe(coach_matches[view_c].style.map(color_results_logic, subset=['wynik']), use_container_width=True)
                        else: st.warning("Brak meczów.")
                    else: st.error("Brak kolumny z datą w pliku mecze.csv.")
