import streamlit as st
import pandas as pd
import datetime
import re
import os
import time

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

# --- FUNKCJE POMOCNICZE ---

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
    # Normalizacja nazw kolumn
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Usuwanie zduplikowanych kolumn
    df = df.loc[:, ~df.columns.duplicated()]

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

def get_age_and_birthday(birth_date_val):
    if pd.isna(birth_date_val) or str(birth_date_val) in ['-', '', 'nan']:
        return None, False
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

# --- ADMIN ACTIONS (Djero) ---
def admin_save_csv(filename, new_data_dict):
    try:
        df = pd.read_csv(filename)
        new_row = pd.DataFrame([new_data_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(filename, index=False)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")
        return False

# --- LOGIKA IKON DOM/WYJAZD ---
def get_match_icon(val):
    """Zwraca ikonkę na podstawie wartości w kolumnie Dom/Gospodarz."""
    if pd.isna(val): return "🚌"
    s = str(val).lower().strip()
    if s in ['1', 'true', 'tak', 'dom', 'gospodarz', 'd', 'u siebie']:
        return "🏠"
    return "🚌"

# --- MENU ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Moduł:", [
    "Aktualny Sezon (25/26)", 
    "Centrum Zawodników", 
    "Centrum Meczowe", 
    "Trenerzy"
])
st.sidebar.divider()

# --- PANEL ADMINA ---
if st.session_state.get('username') == 'Djero':
    st.sidebar.markdown("### 🛠️ Panel Admina (Djero)")
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    with st.sidebar.expander("📝 UNIWERSALNY EDYTOR CSV", expanded=False):
        st.caption("Wybierz plik (np. mecze.csv) i edytuj dane.")
        selected_file = st.selectbox("Wybierz plik:", all_files)
        if selected_file:
            try:
                try: df_editor = pd.read_csv(selected_file, encoding='utf-8')
                except: df_editor = pd.read_csv(selected_file, encoding='windows-1250')
                
                edited_df = st.data_editor(
                    df_editor,
                    num_rows="dynamic",
                    key=f"editor_{selected_file}",
                    height=300
                )
                if st.button(f"💾 Zapisz zmiany w {selected_file}", use_container_width=True):
                    edited_df.to_csv(selected_file, index=False)
                    st.success("✅ Edycja udana! Odświeżam stronę...")
                    st.cache_data.clear()
                    time.sleep(1.5)
                    st.rerun()
            except Exception as e:
                st.error(f"Błąd odczytu pliku: {e}")
    st.sidebar.divider()
    
    # Szybkie dodawanie
    with st.sidebar.expander("➕ Szybkie dodawanie (Piłkarz)"):
        with st.form("add_player_form"):
            a_imie = st.text_input("Imię i Nazwisko")
            a_kraj = st.text_input("Kraj", value="Polska")
            a_poz = st.selectbox("Pozycja", ["Bramkarz", "Obrońca", "Pomocnik", "Napastnik"])
            a_data = st.date_input("Data urodzenia", min_value=datetime.date(1970,1,1))
            if st.form_submit_button("Zapisz w bazie"):
                if a_imie and os.path.exists("pilkarze.csv"):
                    admin_save_csv("pilkarze.csv", {
                        "imię i nazwisko": a_imie, "kraj": a_kraj, 
                        "pozycja": a_poz, "data urodzenia": str(a_data), "suma": 0
                    })
                    st.success(f"Dodano: {a_imie}"); time.sleep(1); st.rerun()
                else: st.warning("Brak pliku pilkarze.csv")
    
    with st.sidebar.expander("⚽ Szybkie dodawanie (Mecz)"):
        with st.form("add_result_form"):
            a_sezon = st.text_input("Sezon", value="2025/26")
            a_rywal = st.text_input("Rywal")
            a_wynik = st.text_input("Wynik (np. 2:1)")
            a_data_m = st.date_input("Data meczu")
            if st.form_submit_button("Zapisz mecz"):
                if os.path.exists("mecze.csv"):
                    admin_save_csv("mecze.csv", {
                        "sezon": a_sezon, "rywal": a_rywal, 
                        "wynik": a_wynik, "data meczu": str(a_data_m)
                    })
                    st.success("Dodano mecz!"); time.sleep(1); st.rerun()
    st.sidebar.divider()

if st.sidebar.button("Wyloguj"): logout()

# --- MODUŁY ---

if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Kadra 2025/2026")
    df = load_data("25_26.csv")
    if df is not None:
        df['is_youth'] = False
        if 'status' in df.columns:
            df['is_youth'] = df['status'].astype(str).str.contains(r'\(M\)', case=False, regex=True)
            df.loc[df['is_youth'], 'imię i nazwisko'] = "Ⓜ️ " + df.loc[df['is_youth'], 'imię i nazwisko']
        if 'gole' in df.columns and 'asysty' in df.columns: df['kanadyjka'] = df['gole'] + df['asysty']

        total_players = len(df)
        avg_age = f"{df['wiek'].mean():.1f}" if 'wiek' in df.columns else "-"
        youth_count = df['is_youth'].sum()
        
        foreigners = 0
        nat_col_raw = 'narodowość' if 'narodowość' in df.columns else ('kraj' if 'kraj' in df.columns else None)
        if nat_col_raw: foreigners = df[~df[nat_col_raw].str.contains('Polska', case=False, na=False)].shape[0]

        top_scorer = "-"
        if 'gole' in df.columns:
            max_g = df['gole'].max()
            if max_g > 0:
                best = df[df['gole'] == max_g].iloc[0]
                top_scorer = f"{best['imię i nazwisko'].replace('Ⓜ️ ', '')} ({max_g})"

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
            "asysty": st.column_config.ProgressColumn("Asysty", format="%d 🅰️", min_value=0, max_value=15),
            "kanadyjka": st.column_config.NumberColumn("Kanadyjka", format="%d 🍁"),
            "czyste konta": st.column_config.NumberColumn("Czyste K.", format="%d 🧤"),
        }
        
        # Kolumny do wyświetlenia
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
            else:
                st.dataframe(df_view[final], use_container_width=True, column_config=col_config)
    else: st.error("⚠️ Brak pliku '25_26.csv'.")

elif opcja == "Centrum Zawodników":
    st.header("🏃 Centrum Zawodników TSP")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Baza Zawodników", "Strzelcy", "Klub 100", "Transfery", "Młoda Ekstraklasa"])

    with tab1:
        st.subheader("Baza Zawodników")
        df_long = load_data("pilkarze.csv")
        df_strzelcy = load_data("strzelcy.csv")
        df_mecze = load_data("mecze.csv") 
        if df_long is not None:
            if 'suma' in df_long.columns:
                if isinstance(df_long['suma'], pd.DataFrame): df_long['suma'] = df_long['suma'].iloc[:, 0]
                df_long['suma'] = pd.to_numeric(df_long['suma'], errors='coerce').fillna(0).astype(int)
                df_uv = df_long.sort_values('suma', ascending=False).drop_duplicates(subset=['imię i nazwisko'])
            else: df_uv = df_long.drop_duplicates(subset=['imię i nazwisko'])

            c1, c2 = st.columns([2, 1])
            with c1: search = st.text_input("Szukaj zawodnika:")
            with c2: obcy = st.checkbox("Tylko obcokrajowcy")
            if search: df_uv = df_uv[df_uv['imię i nazwisko'].astype(str).str.contains(search, case=False)]
            if obcy and 'narodowość' in df_uv.columns: df_uv = df_uv[~df_uv['narodowość'].str.contains("Polska", na=False)]
            
            df_uv = prepare_flags(df_uv)
            cols_b = [c for c in ['imię i nazwisko', 'Flaga', 'Narodowość', 'pozycja', 'suma'] if c in df_uv.columns]
            st.dataframe(df_uv[cols_b], use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
            
            st.divider()
            st.subheader("📈 Profil i Analiza")
            wyb = st.selectbox("Wybierz zawodnika:", [""] + df_uv['imię i nazwisko'].tolist())
            if wyb:
                row = df_uv[df_uv['imię i nazwisko'] == wyb].iloc[0]
                col_b = next((c for c in row.index if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
                age_info, is_bday = "-", False
                if col_b: 
                    a, is_bday = get_age_and_birthday(row[col_b])
                    if a: age_info = f"{a} lat"
                
                if is_bday: st.balloons(); st.success(f"🎉🎂 {wyb} kończy dzisiaj {age_info}! 🎂🎉")
                
                c_p1, c_p2 = st.columns([1, 3])
                with c_p1: st.image(row['Flaga'], width=100) if 'Flaga' in row and row['Flaga'] else st.markdown("👤")
                with c_p2:
                    st.markdown(f"## {wyb}")
                    st.markdown(f"**Kraj:** {row.get('Narodowość', '-')} | **Poz:** {row.get('pozycja', '-')} | **Wiek:** {age_info}")
                
                st.markdown("---")
                p_stats = df_long[df_long['imię i nazwisko'] == wyb].copy().sort_values('sezon')
                gole_l = []
                if df_strzelcy is not None:
                    gm = df_strzelcy.set_index(['imię i nazwisko', 'sezon'])['gole'].to_dict()
                    for _, r in p_stats.iterrows(): gole_l.append(gm.get((wyb, r['sezon']), 0))
                else: gole_l = [0]*len(p_stats)
                p_stats['Gole'] = gole_l

                if HAS_PLOTLY:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['liczba'], name='Mecze', marker_color='#3498db'))
                    fig.add_trace(go.Bar(x=p_stats['sezon'], y=p_stats['Gole'], name='Gole', marker_color='#2ecc71'))
                    fig.update_layout(title=f"Statystyki: {wyb}", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(p_stats[['sezon', 'liczba', 'Gole']], use_container_width=True, hide_index=True)
                
                if df_mecze is not None and 'strzelcy' in df_mecze.columns:
                    st.markdown("**Mecze z bramkami:**")
                    fm = []
                    mz = df_mecze[df_mecze['strzelcy'].notna()]
                    for _, r in mz.iterrows():
                        sm = parse_scorers(r['strzelcy'])
                        if wyb in sm:
                            fm.append({'Sezon': r.get('sezon'), 'Data': r.get('data meczu'), 'Rywal': r.get('rywal'), 'Wynik': r.get('wynik'), 'Gole': sm[wyb]})
                    if fm: st.dataframe(pd.DataFrame(fm), use_container_width=True)
                    else: st.caption("Brak danych o golach w bazie meczowej.")

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
            col_s = 'suma' if 'suma' in df.columns else None
            if col_s:
                if isinstance(df[col_s], pd.DataFrame): df[col_s] = df[col_s].iloc[:, 0]
                df[col_s] = pd.to_numeric(df[col_s], errors='coerce').fillna(0).astype(int)
                k100 = df.drop_duplicates('imię i nazwisko')
                k100 = k100[k100[col_s] >= 100].sort_values(col_s, ascending=False)
                k100 = prepare_flags(k100)
                st.dataframe(k100[['imię i nazwisko', 'Flaga', 'Narodowość', col_s]], use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

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

elif opcja == "Centrum Meczowe":
    st.header("🏟️ Centrum Meczowe")
    tab1, tab2, tab3, tab4 = st.tabs(["Historia Meczów", "Rywale (H2H)", "Frekwencja", "Statystyki Wyników"])

    with tab1:
        st.subheader("Archiwum Meczów")
        df = load_data("mecze.csv")
        if df is not None:
            # --- DODANIE IKON DOM/WYJAZD ---
            col_dom = next((c for c in df.columns if c in ['dom', 'gospodarz', 'u siebie', 'gdzie']), None)
            if col_dom:
                df['Gdzie'] = df[col_dom].apply(get_match_icon)
                # Przesuwamy ikonkę na początek
                cols = list(df.columns)
                cols.remove('Gdzie'); cols.insert(0, 'Gdzie')
                df = df[cols]

            sezony = sorted([s for s in df['sezon'].astype(str).unique() if len(s)>4], reverse=True) if 'sezon' in df.columns else []
            c1, c2 = st.columns(2)
            sel_sez = c1.selectbox("Sezon:", sezony) if sezony else None
            filt = c2.text_input("Szukaj rywala:")
            m = df.copy()
            if sel_sez: m = m[m['sezon'] == sel_sez]
            if filt: m = m[m.astype(str).apply(lambda x: x.str.contains(filt, case=False)).any(axis=1)]
            
            roz = next((c for c in m.columns if c in ['rozgrywki', 'liga']), None)
            datasets = [(r, m[m[roz]==r]) for r in m[roz].unique()] if roz else [("Wszystkie", m)]
            
            tabs_list = st.tabs([x[0] for x in datasets])
            for t, (n, sub) in zip(tabs_list, datasets):
                with t:
                    st.dataframe(sub.style.map(color_results_logic, subset=['wynik'] if 'wynik' in sub.columns else None), use_container_width=True)

    with tab2:
        st.subheader("Bilans z Rywalami")
        df = load_data("mecze.csv")
        if df is not None:
            col_r = next((c for c in df.columns if c in ['rywal', 'przeciwnik']), None)
            if col_r and 'wynik' in df.columns:
                def calc(s):
                    m=len(s); w=r=p=0; gs=ga=0
                    for x in s['wynik']:
                        res=parse_result(x)
                        if res:
                            gs+=res[0]; ga+=res[1]
                            if res[0]>res[1]: w+=1
                            elif res[0]<res[1]: p+=1
                            else: r+=1
                    return pd.Series({'Mecze': m, 'Z': w, 'R': r, 'P': p, 'Bramki': f"{gs}:{ga}", 'Pkt': w*3+r})
                
                t_h1, t_h2 = st.tabs(["Analiza Rywala", "Tabela"])
                with t_h1:
                    sel = st.selectbox("Rywal:", sorted(df[col_r].unique()))
                    if sel:
                        sub = df[df[col_r]==sel]
                        st.dataframe(sub.style.map(color_results_logic, subset=['wynik']), use_container_width=True)
                with t_h2:
                    st.dataframe(df.groupby(col_r).apply(calc).reset_index().sort_values('Pkt', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("Frekwencja")
        
        # 1. Statystyki dynamiczne z meczów (NOWOŚĆ)
        df_m = load_data("mecze.csv")
        stats_calculated = False
        if df_m is not None:
            col_dom = next((c for c in df_m.columns if c in ['dom', 'gospodarz', 'u siebie']), None)
            col_att = next((c for c in df_m.columns if c in ['widzów', 'frekwencja', 'kibiców']), None)
            
            if col_dom and col_att and 'sezon' in df_m.columns:
                st.info("📊 Poniższe statystyki są obliczane automatycznie na podstawie pliku mecze.csv (tylko mecze domowe).")
                
                # Filtrujemy tylko mecze domowe (gdzie col_dom == 1, 'tak', 'dom' itp)
                def is_home(x):
                    s = str(x).lower().strip()
                    return s in ['1', 'true', 'tak', 'dom', 'gospodarz', 'd', 'u siebie']
                
                df_home = df_m[df_m[col_dom].apply(is_home)].copy()
                df_home[col_att] = pd.to_numeric(df_home[col_att], errors='coerce')
                
                # Agregacja
                stats = df_home.groupby('sezon')[col_att].agg(['count', 'sum', 'mean', 'median', 'min', 'max']).reset_index()
                stats.columns = ['Sezon', 'Mecze', 'Suma', 'Średnia', 'Mediana', 'Min', 'Max']
                stats = stats.sort_values('Sezon', ascending=False)
                
                # Formatowanie
                for c in ['Suma', 'Średnia', 'Mediana', 'Min', 'Max']:
                    stats[c] = stats[c].fillna(0).astype(int)
                
                st.dataframe(stats, use_container_width=True)
                stats_calculated = True
        
        if not stats_calculated:
            st.caption("Aby zobaczyć automatyczne statystyki, dodaj w 'mecze.csv' kolumny: 'Dom' (1/0) oraz 'Frekwencja' (liczba).")

        st.divider()
        st.markdown("**Archiwalne dane (z pliku frekwencja.csv):**")
        df_f = load_data("frekwencja.csv")
        if df_f is not None:
            if HAS_PLOTLY:
                fig = px.bar(df_f, x='sezon', y=df_f.columns[-1], title="Frekwencja (Archiwum)")
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_f, use_container_width=True)

    with tab4:
        st.subheader("Statystyki Wyników")
        df = load_data("wyniki.csv")
        if df is not None:
            st.bar_chart(df.set_index('wynik')['częstotliwość'])
            st.dataframe(df, use_container_width=True)

elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP")
    df = load_data("trenerzy.csv")
    
    if df is not None:
        # --- 1. Przygotowanie danych (Daty) ---
        def smart_date(s):
            # Próba konwersji różnych formatów dat
            d = pd.to_datetime(s, format='%d.%m.%Y', errors='coerce')
            if d.isna().mean() > 0.5:  # Jeśli większość to błędy, spróbuj standardowego formatu
                d = pd.to_datetime(s, errors='coerce')
            return d

        if 'początek' in df.columns: 
            df['początek_dt'] = smart_date(df['początek'])
        
        if 'koniec' in df.columns: 
            df['koniec_dt'] = smart_date(df['koniec'])
            # Jeśli nie ma daty końca, zakładamy, że trener pracuje do dziś
            df['koniec_dt'] = df['koniec_dt'].fillna(pd.Timestamp.today())

        df = prepare_flags(df)
        
        # Konwersja statystyk na liczby (jeśli istnieją w pliku)
        for c in ['mecze', 'punkty', 'z', 'r', 'p']: 
            if c in df.columns: 
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

        # --- 2. Zakładki ---
        t1, t2, t3 = st.tabs(["Lista Trenerów", "Rankingi", "Analiza Szczegółowa"])

        # TAB 1: Lista
        with t1:
            # Sortowanie od najnowszego
            v = df.sort_values('początek_dt', ascending=False) if 'początek_dt' in df.columns else df
            
            cols_to_show = [c for c in ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'początek', 'koniec', 'mecze', 'punkty'] if c in v.columns]
            
            st.dataframe(
                v[cols_to_show], 
                use_container_width=True, 
                hide_index=True, 
                column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")}
            )

        # TAB 2: Rankingi (Agregacja)
        with t2:
            if 'punkty' in df.columns and 'mecze' in df.columns:
                st.markdown("### 🏆 Najlepsi punktujący (według pliku trenerzy.csv)")
                agg = df.groupby(['imię i nazwisko', 'Narodowość', 'Flaga'], as_index=False)[['mecze', 'punkty']].sum()
                agg['Śr. pkt'] = (agg['punkty'] / agg['mecze']).fillna(0).round(2)
                agg = agg.sort_values('punkty', ascending=False)
                
                st.dataframe(
                    agg, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                        "Śr. pkt": st.column_config.NumberColumn("Średnia Pkt", format="%.2f")
                    }
                )
            else:
                st.info("Brak kolumn 'mecze' lub 'punkty' w pliku trenerzy.csv.")

        # TAB 3: Analiza Szczegółowa (Łączenie z mecze.csv)
        with t3:
            st.markdown("### 📊 Analiza pracy trenera na podstawie wyników")
            trenerzy_list = sorted(df['imię i nazwisko'].unique())
            wybrany_trener = st.selectbox("Wybierz trenera:", trenerzy_list, key="sel_trener_adv")
            
            if wybrany_trener:
                coach_rows = df[df['imię i nazwisko'] == wybrany_trener]
                mecze_df = load_data("mecze.csv")
                
                if mecze_df is not None:
                    # Znajdź kolumnę z datą w meczach
                    col_data_m = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None)
                    
                    if col_data_m:
                        mecze_df['dt'] = pd.to_datetime(mecze_df[col_data_m], dayfirst=True, errors='coerce')
                        
                        # Filtrowanie meczów dla kadencji trenera
                        # (Trener mógł prowadzić klub kilka razy, więc iterujemy po wszystkich jego okresach)
                        mask = pd.Series([False] * len(mecze_df))
                        
                        found_periods = False
                        for _, row in coach_rows.iterrows():
                            if pd.notnull(row.get('początek_dt')):
                                start = row['początek_dt']
                                end = row['koniec_dt']
                                mask |= (mecze_df['dt'] >= start) & (mecze_df['dt'] <= end)
                                found_periods = True
                        
                        if not found_periods:
                            st.warning("Nie udało się ustalić dat kadencji trenera (sprawdź format dat w trenerzy.csv).")
                        else:
                            coach_matches = mecze_df[mask].sort_values('dt')
                            
                            if not coach_matches.empty:
                                # Obliczanie punktów
                                pts_list = []
                                matches_count = 0
                                wins = 0
                                draws = 0
                                losses = 0
                                goals_for = 0
                                goals_against = 0
                                scorers_dict = {}

                                for _, m in coach_matches.iterrows():
                                    res = parse_result(m['wynik'])
                                    if res:
                                        matches_count += 1
                                        g_f, g_a = res
                                        goals_for += g_f
                                        goals_against += g_a
                                        
                                        if g_f > g_a: 
                                            pts_list.append(3)
                                            wins += 1
                                        elif g_f == g_a: 
                                            pts_list.append(1)
                                            draws += 1
                                        else: 
                                            pts_list.append(0)
                                            losses += 1
                                    else:
                                        pts_list.append(0) # Brak wyniku = 0 pkt do wykresu
                                    
                                    # Zliczanie strzelców za kadencji
                                    if 'strzelcy' in m and pd.notnull(m['strzelcy']):
                                        s_map = parse_scorers(m['strzelcy'])
                                        for sc, val in s_map.items():
                                            scorers_dict[sc] = scorers_dict.get(sc, 0) + val

                                # Metryki
                                c1, c2, c3, c4 = st.columns(4)
                                c1.metric("Mecze", matches_count)
                                c2.metric("Bilans (Z-R-P)", f"{wins}-{draws}-{losses}")
                                c3.metric("Bramki", f"{goals_for} : {goals_against}")
                                avg_pts = sum(pts_list) / len(pts_list) if pts_list else 0
                                c4.metric("Średnia punktów", f"{avg_pts:.2f}")

                                st.divider()

                                # Wykres formy
                                coach_matches['Punkty'] = pts_list
                                coach_matches['Forma (Śr. 5 meczów)'] = coach_matches['Punkty'].rolling(window=5, min_periods=1).mean()
                                
                                if HAS_PLOTLY:
                                    fig = px.line(
                                        coach_matches, 
                                        x='dt', 
                                        y='Forma (Śr. 5 meczów)', 
                                        markers=True,
                                        title=f"Wykres formy: {wybrany_trener}",
                                        hover_data=['rywal', 'wynik']
                                    )
                                    # Dodanie linii średniej
                                    fig.add_hline(y=avg_pts, line_dash="dot", annotation_text="Średnia kadencji", annotation_position="bottom right")
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.line_chart(coach_matches.set_index('dt')['Forma (Śr. 5 meczów)'])

                                # Strzelcy za kadencji
                                if scorers_dict:
                                    st.markdown(f"**⚽ Kto strzelał dla trenera: {wybrany_trener}?**")
                                    df_s = pd.DataFrame(list(scorers_dict.items()), columns=['Zawodnik', 'Gole'])
                                    df_s = df_s.sort_values('Gole', ascending=False).reset_index(drop=True)
                                    df_s.index += 1
                                    
                                    # Kolorowanie samobójów
                                    def highlight_own_goal(val):
                                        return 'color: red;' if 'samobój' in str(val).lower() else ''
                                        
                                    st.dataframe(df_s.style.map(highlight_own_goal, subset=['Zawodnik']), use_container_width=True)

                                # Tabela meczów
                                with st.expander("Zobacz listę meczów"):
                                    cols_view = [c for c in coach_matches.columns if c not in ['dt', 'Punkty', 'Forma (Śr. 5 meczów)', 'mecz_id', 'data sortowania']]
                                    st.dataframe(
                                        coach_matches[cols_view].style.map(color_results_logic, subset=['wynik']), 
                                        use_container_width=True
                                    )

                            else:
                                st.info("Znaleziono daty kadencji, ale brak meczów w tym okresie w pliku mecze.csv.")
                    else:
                        st.error("Brak kolumny z datą w pliku mecze.csv. Nie można powiązać meczów z trenerem.")
