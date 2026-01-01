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
    "guest": "123456789"
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
                        admin_save_csv("pilkarze.csv", {"imię i nazwisko": a_imie, "kraj": a_kraj, "pozycja": a_poz, "data urodzenia": str(a_data), "suma": 0})
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

# --- MODUŁ KALENDARZ ---
elif opcja == "Kalendarz":
    st.header("📅 Kalendarz Klubowy")
    
    # Dane wejściowe
    today = datetime.date.today()
    
    # 1. Ładowanie danych
    df_m = load_data("mecze.csv")
    df_p = load_data("pilkarze.csv")
    df_curr = load_data("25_26.csv")
    
    # Listy zawodników
    current_squad_names = []
    if df_curr is not None:
        current_squad_names = [str(x).lower().strip() for x in df_curr['imię i nazwisko'].unique()]
    
    club_100_names = []
    if df_p is not None and 'suma' in df_p.columns:
        club_100_names = [str(r['imię i nazwisko']).lower().strip() for i, r in df_p.iterrows() if r['suma'] >= 100]

    # 2. Przygotowanie zdarzeń (Events)
    events_map = {} # Key: (Month, Day), Value: List of events

    # a) Mecze
    if df_m is not None:
        col_d = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
        if col_d:
            df_m['dt_obj'] = pd.to_datetime(df_m[col_d], dayfirst=True, errors='coerce')
            for _, row in df_m.dropna(subset=['dt_obj']).iterrows():
                d = row['dt_obj'].date()
                if d.year == today.year or d.year == today.year + 1: # Pokaż tylko aktualne mecze
                    k = (d.month, d.day)
                    entry = {
                        'type': 'match',
                        'text': f"⚽ {row.get('rywal', 'Mecz')} ({row.get('wynik', '-')})",
                        'color': '#343a40', # Ciemny szary
                        'date': d
                    }
                    events_map.setdefault(d, []).append(entry)

   # b) Urodziny
    if df_p is not None:
        col_b = next((c for c in df_p.columns if c in ['data urodzenia', 'urodzony', 'data_ur']), None)
        if col_b:
            # --- ZMIANA TUTAJ: Usuwamy duplikaty ---
            # Tworzymy kopię bazy tylko z unikalnymi nazwiskami, żeby nie powielać urodzin
            df_unique = df_p.drop_duplicates(subset=['imię i nazwisko'])
            
            for _, row in df_unique.iterrows():
                try:
                    # Sprawdzamy czy data istnieje i jest poprawna
                    if pd.isna(row[col_b]) or str(row[col_b]) in ['-', '']: continue
                    
                    bdate = pd.to_datetime(row[col_b]).date()
                    name = row['imię i nazwisko']
                    name_clean = str(name).lower().strip()
                    
                    # Domyślny kolor (Byli piłkarze - Niebieski)
                    color = "#17a2b8" 
                    prefix = "🎂"
                    
                    # Sprawdzanie warunków kolorów
                    if name_clean in current_squad_names:
                        color = "#28a745" # Aktualny sezon (Zielony)
                        prefix = "🟢🎂"
                    elif name_clean in club_100_names:
                        color = "#ffc107" # Klub 100 (Złoty)
                        prefix = "🟡🎂"
                    
                    # Generujemy urodziny na bieżący i przyszły rok
                    for y in [today.year, today.year+1]:
                        try:
                            evt_date = datetime.date(y, bdate.month, bdate.day)
                            events_map.setdefault(evt_date, []).append({
                                'type': 'birthday',
                                'text': f"{prefix} {name} ({y - bdate.year})",
                                'color': color,
                                'date': evt_date
                            })
                        except ValueError: pass # Obsługa 29 lutego
                except: pass
   # --- LEGENDA ---
    st.markdown("### 📝 Legenda")
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: #28a745; border-radius: 4px; margin-right: 8px;"></div>
            <span><b>Kadra 25/26</b> (Obecni piłkarze)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: #ffc107; border-radius: 4px; margin-right: 8px;"></div>
            <span><b>Klub 100</b> (Legendy / >100 meczów)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: #17a2b8; border-radius: 4px; margin-right: 8px;"></div>
            <span><b>Byli piłkarze</b> (Pozostali)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: #343a40; border-radius: 4px; margin-right: 8px;"></div>
            <span><b>Mecze</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    # --- WIDOK TYGODNIOWY ---
    st.subheader("Ten tydzień")

    # Znajdź początek tygodnia (Poniedziałek)
    start_of_week = today - datetime.timedelta(days=today.weekday())
    cols = st.columns(7)
    days_pl = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]
    
    for i, col in enumerate(cols):
        curr_day = start_of_week + datetime.timedelta(days=i)
        is_today = (curr_day == today)
        
        with col:
            # Nagłówek dnia
            bg = "#e9ecef" if not is_today else "#ffeeba"
            st.markdown(f"""
            <div style="background-color: {bg}; padding: 5px; border-radius: 5px; text-align: center; margin-bottom: 5px;">
                <strong>{days_pl[i]}</strong><br>{curr_day.strftime('%d.%m')}
            </div>
            """, unsafe_allow_html=True)
            
            # Zdarzenia
            day_events = events_map.get(curr_day, [])
            for ev in day_events:
                txt_col = "black" if ev['color'] == "#ffc107" else "white"
                st.markdown(f"""
                <div style="background-color: {ev['color']}; color: {txt_col}; padding: 4px; border-radius: 4px; font-size: 12px; margin-bottom: 2px;">
                    {ev['text']}
                </div>
                """, unsafe_allow_html=True)
            
            if not day_events:
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    st.divider()

    # --- WIDOK MIESIĘCZNY (EXPANDER) ---
    with st.expander("📅 Pełny Kalendarz (Widok Miesięczny)", expanded=False):
        c_m1, c_m2 = st.columns(2)
        sel_year = c_m1.number_input("Rok", value=today.year, min_value=1990, max_value=2030)
        sel_month = c_m2.selectbox("Miesiąc", range(1, 13), index=today.month-1)
        
        cal = calendar.monthcalendar(sel_year, sel_month)
        
        # Grid 7 kolumn
        cols_h = st.columns(7)
        for i, d in enumerate(days_pl):
            cols_h[i].markdown(f"**{d}**")
            
        for week in cal:
            cols_w = st.columns(7)
            for i, day_num in enumerate(week):
                with cols_w[i]:
                    if day_num == 0:
                        st.write(" ")
                    else:
                        date_obj = datetime.date(sel_year, sel_month, day_num)
                        is_t = (date_obj == today)
                        border = "2px solid #0d6efd" if is_t else "1px solid #dee2e6"
                        
                        st.markdown(f"**{day_num}**")
                        evs = events_map.get(date_obj, [])
                        for ev in evs:
                            txt_col = "black" if ev['color'] == "#ffc107" else "white"
                            st.markdown(f"""
                            <div style="background-color: {ev['color']}; color: {txt_col}; padding: 2px; border-radius: 3px; font-size: 10px; margin-bottom: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                {ev['text']}
                            </div>
                            """, unsafe_allow_html=True)
                        st.divider()

    st.caption("Legenda: 🟢 Aktualny Skład | 🟡 Klub 100 | 🔵 Byli piłkarze | ⚫ Mecz")

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
                
                with c_p1: 
                    if 'Flaga' in row and pd.notna(row['Flaga']) and str(row['Flaga']) != 'nan' and str(row['Flaga']).strip() != '':
                        st.image(row['Flaga'], width=100) 
                    else: 
                        st.markdown("## 👤")

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
                k100 = df.drop_duplicates('imię i nazwisko'); k100 = k100[k100[col_s] >= 100].sort_values(col_s, ascending=False); k100 = prepare_flags(k100)
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
    
    df_matches = load_data("mecze.csv")
    df_coaches = load_data("trenerzy.csv")

    if df_matches is not None:
        col_date_m = next((c for c in df_matches.columns if 'data' in c and 'sort' not in c), None)
        if col_date_m:
            df_matches['dt_obj'] = pd.to_datetime(df_matches[col_date_m], dayfirst=True, errors='coerce')
        
        if df_coaches is not None:
            def smart_date(s):
                d = pd.to_datetime(s, format='%d.%m.%Y', errors='coerce')
                if d.isna().mean() > 0.5: d = pd.to_datetime(s, errors='coerce')
                return d

            if 'początek' in df_coaches.columns: df_coaches['start'] = smart_date(df_coaches['początek'])
            if 'koniec' in df_coaches.columns: 
                df_coaches['end'] = smart_date(df_coaches['koniec'])
                df_coaches['end'] = df_coaches['end'].fillna(pd.Timestamp.today())

            if 'dt_obj' in df_matches.columns and 'start' in df_coaches.columns:
                def find_coach(match_date):
                    if pd.isna(match_date): return "-"
                    found = df_coaches[(df_coaches['start'] <= match_date) & (df_coaches['end'] >= match_date)]
                    if not found.empty: return found.iloc[0]['imię i nazwisko']
                    return "-"
                df_matches['Trener'] = df_matches['dt_obj'].apply(find_coach)
        
        col_dom = next((c for c in df_matches.columns if c in ['dom', 'gospodarz', 'u siebie', 'gdzie']), None)
        if col_dom:
            df_matches['Gdzie'] = df_matches[col_dom].apply(get_match_icon)

        def get_outcome(res_str):
            r = parse_result(res_str)
            if not r: return "Nieznany"
            if r[0] > r[1]: return "Zwycięstwo"
            if r[0] < r[1]: return "Porażka"
            return "Remis"
        
        if 'wynik' in df_matches.columns:
            df_matches['Rezultat'] = df_matches['wynik'].apply(get_outcome)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🗂️ Archiwum", "⚔️ H2H (Rywale)", "📢 Frekwencja", "🎲 Wyniki"])

    with tab1:
        if df_matches is not None:
            st.markdown("### 📈 Podsumowanie Statystyczne")
            c_f1, c_f2 = st.columns(2)
            d_sezony = sorted([str(s) for s in df_matches['sezon'].unique() if len(str(s))>4], reverse=True) if 'sezon' in df_matches.columns else []
            sel_d_sez = c_f1.multiselect("Filtruj Sezon:", d_sezony)
            
            df_dash = df_matches.copy()
            if sel_d_sez: df_dash = df_dash[df_dash['sezon'].isin(sel_d_sez)]

            wins = len(df_dash[df_dash['Rezultat'] == "Zwycięstwo"])
            draws = len(df_dash[df_dash['Rezultat'] == "Remis"])
            losses = len(df_dash[df_dash['Rezultat'] == "Porażka"])
            total = wins + draws + losses
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mecze", total)
            m2.metric("Zwycięstwa", wins, delta=f"{wins/total*100:.1f}%" if total else None)
            m3.metric("Remisy", draws)
            m4.metric("Porażki", losses, delta_color="inverse")

            st.divider()

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                if HAS_PLOTLY:
                    fig_pie = px.pie(
                        names=["Zwycięstwo", "Remis", "Porażka"], 
                        values=[wins, draws, losses],
                        title="Bilans Meczy",
                        color_discrete_map={"Zwycięstwo": "#2ecc71", "Remis": "#95a5a6", "Porażka": "#e74c3c"},
                        hole=0.4
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

            with col_chart2:
                gf_tot = 0
                ga_tot = 0
                for r in df_dash['wynik']:
                    res = parse_result(r)
                    if res: gf_tot+=res[0]; ga_tot+=res[1]
                
                if HAS_PLOTLY:
                    df_goals = pd.DataFrame({
                        "Typ": ["Strzelone", "Stracone"],
                        "Ilość": [gf_tot, ga_tot]
                    })
                    fig_bar = px.bar(
                        df_goals, x="Typ", y="Ilość", color="Typ",
                        title="Bilans Bramkowy",
                        color_discrete_map={"Strzelone": "#3498db", "Stracone": "#e74c3c"}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("🗂️ Pełne Archiwum")
        if df_matches is not None:
            df = df_matches.copy()
            c1, c2 = st.columns([1, 2])
            sezony = sorted([s for s in df['sezon'].astype(str).unique() if len(s)>4], reverse=True) if 'sezon' in df.columns else []
            sel_sez = c1.selectbox("Sezon:", ["Wszystkie"] + sezony, key="arch_sez")
            if sel_sez != "Wszystkie": df = df[df['sezon'] == sel_sez]
            
            filt = c2.text_input("Szukaj (Rywal/Trener):", key="arch_filt")
            if filt: df = df[df.astype(str).apply(lambda x: x.str.contains(filt, case=False)).any(axis=1)]

            col_liga = next((c for c in df.columns if c in ['rozgrywki', 'liga', 'turniej']), None)
            if col_liga:
                ligues = sorted(df[col_liga].astype(str).unique())
                if not ligues: st.warning("Brak meczów.")
                else:
                    tabs_liga = st.tabs(ligues)
                    for t, liga_name in zip(tabs_liga, ligues):
                        with t:
                            sub = df[df[col_liga] == liga_name].copy()
                            if 'dt_obj' in sub.columns: sub = sub.sort_values('dt_obj', ascending=False)
                            def style_row(row):
                                res = parse_result(row['wynik'])
                                if not res: return [''] * len(row)
                                if res[0] > res[1]: return ['background-color: #d1fae5; color: black'] * len(row)
                                if res[0] < res[1]: return ['background-color: #fee2e2; color: black'] * len(row)
                                return ['background-color: #f3f4f6; color: black'] * len(row)

                            cols_order = ['Gdzie', 'data meczu', 'rywal', 'wynik', 'Trener', 'strzelcy']
                            final_cols = [c for c in cols_order if c in sub.columns]
                            
                            st.dataframe(
                                sub[final_cols].style.apply(style_row, axis=1), 
                                use_container_width=True,
                                hide_index=True
                            )
            else: st.dataframe(df, use_container_width=True)

    with tab3:
        st.subheader("⚔️ Bilans z Rywalami")
        if df_matches is not None:
            col_r = next((c for c in df_matches.columns if c in ['rywal', 'przeciwnik']), None)
            
            if col_r:
                def calc_h2h(s):
                    m=len(s); w=r=p=0; gs=ga=0
                    for x in s['wynik']:
                        res = parse_result(x)
                        if res:
                            gs+=res[0]; ga+=res[1]
                            if res[0]>res[1]: w+=1
                            elif res[0]<res[1]: p+=1
                            else: r+=1
                    return pd.Series({'Mecze': m, 'Z': w, 'R': r, 'P': p, 'Bramki': f"{gs}:{ga}", 'Pkt': w*3+r})

                all_rivals = sorted(df_matches[col_r].unique())
                sel_rival = st.selectbox("Wybierz rywala:", all_rivals)
                
                if sel_rival:
                    sub = df_matches[df_matches[col_r] == sel_rival].copy()
                    if 'dt_obj' in sub.columns: sub = sub.sort_values('dt_obj', ascending=False)
                    stats = calc_h2h(sub)
                    badges = []
                    for _, row in sub.head(5).iterrows():
                        res = parse_result(row['wynik'])
                        if res:
                            if res[0] > res[1]: badges.append("✅")
                            elif res[0] < res[1]: badges.append("❌")
                            else: badges.append("➖")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Mecze", int(stats['Mecze']))
                    c2.metric("Bilans", f"{int(stats['Z'])}-{int(stats['R'])}-{int(stats['P'])}")
                    c3.metric("Bramki", stats['Bramki'])
                    c4.write(f"**Forma (Ost. 5):** {' '.join(badges)}")
                    
                    st.dataframe(sub[['data meczu', 'rozgrywki', 'wynik', 'Trener']].style.map(color_results_logic, subset=['wynik']), use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("📢 Statystyki Frekwencji")
        
        if df_matches is not None:
            col_att = next((c for c in df_matches.columns if c in ['widzów', 'frekwencja', 'kibiców', 'widzow']), None)
            col_dom = next((c for c in df_matches.columns if c in ['dom', 'gospodarz', 'u siebie']), None)
            col_liga = next((c for c in df_matches.columns if c in ['rozgrywki', 'liga', 'turniej']), None)
            
            if col_att and col_dom and 'sezon' in df_matches.columns:
                # 1. Filtrowanie domowe (z poprawioną logiką dla Rekordu/BKS)
                # Sprawdź też miejsce rozgrywania
                col_miejsce = next((c for c in df_matches.columns if c in ['miejsce rozgrywania', 'miejsce']), None)
                
                def check_is_home(row):
                    # Warunek 1: Kolumna Dom == 1
                    if str(row[col_dom]) in ['1', 'true', 'tak']: return True
                    # Warunek 2: Miejsce zawiera Bielsko, Rekord lub BKS
                    if col_miejsce:
                        s = str(row[col_miejsce]).lower()
                        if any(x in s for x in ['bielsko', 'rekord', 'bks', 'rychlińskiego']): return True
                    return False

                df_matches['is_home_calc'] = df_matches.apply(check_is_home, axis=1)
                df_home = df_matches[df_matches['is_home_calc']].copy()
                
                # 2. Czyszczenie frekwencji (Bardziej pancerne)
                # Usuwamy wszystko co nie jest cyfrą, upewniamy się że to int
                df_home['att_clean'] = pd.to_numeric(df_home[col_att], errors='coerce').fillna(0).astype(int)
                
                df_home_valid = df_home[df_home['att_clean'] > 0].copy()

                c1, c2 = st.columns([1, 1])
                with c1:
                    if col_liga:
                        all_comps = sorted(df_home_valid[col_liga].astype(str).unique())
                        sel_comps = st.multiselect("Rozgrywki:", all_comps, default=all_comps)
                        if sel_comps: df_home_valid = df_home_valid[df_home_valid[col_liga].isin(sel_comps)]
                
                with c2:
                    metric_map = {"Średnia": "mean", "Mediana": "median", "Rekord (Max)": "max", "Minimum": "min", "Suma": "sum"}
                    sel_metric = st.selectbox("Wskaźnik:", list(metric_map.keys()), index=0)

                if not df_home_valid.empty:
                    stats = df_home_valid.groupby('sezon')['att_clean'].agg(['count', 'sum', 'mean', 'median', 'min', 'max']).reset_index()
                    stats.columns = ['Sezon', 'Mecze', 'Suma', 'Średnia', 'Mediana', 'Min', 'Max']
                    for c in ['Suma', 'Średnia', 'Mediana', 'Min', 'Max']: stats[c] = stats[c].astype(int)
                    stats = stats.sort_values('Sezon', ascending=True)

                    if HAS_PLOTLY:
                        y_col = {"Rekord (Max)": "Max", "Minimum": "Min", "Suma": "Suma", "Średnia": "Średnia", "Mediana": "Mediana"}.get(sel_metric, "Średnia")
                        fig = px.bar(stats, x='Sezon', y=y_col, text=y_col, title=f"Frekwencja: {sel_metric}", color=y_col, color_continuous_scale='Blues')
                        fig.update_traces(textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.bar_chart(stats.set_index('Sezon'))
                    
                    with st.expander("Pokaż tabelę"):
                        st.dataframe(stats.sort_values('Sezon', ascending=False), use_container_width=True)
                else: st.warning("Brak danych po filtracji (sprawdź czy są wpisani widzowie).")
            else: st.info("Brak kolumn (widzów/dom) w pliku.")

    with tab5:
        st.subheader("🎲 Statystyki Wyników")
        if df_matches is not None and 'wynik' in df_matches.columns:
            df_scores = df_matches.copy()
            df_scores['wynik_std'] = df_scores['wynik'].astype(str).str.replace(" ", "").str.strip()
            score_counts = df_scores['wynik_std'].value_counts().reset_index()
            score_counts.columns = ['Wynik', 'Liczba']
            score_counts = score_counts.sort_values('Liczba', ascending=False)

            c1, c2 = st.columns([1.5, 1])
            with c1:
                if HAS_PLOTLY:
                    fig = px.bar(score_counts.head(15), x='Wynik', y='Liczba', text='Liczba', title="Najczęstsze wyniki", color='Liczba', color_continuous_scale='Viridis')
                    st.plotly_chart(fig, use_container_width=True)
                else: st.bar_chart(score_counts.set_index('Wynik').head(15))
            with c2:
                score_options = score_counts['Wynik'].tolist()
                def format_func(opt): return f"{opt} ({score_counts[score_counts['Wynik'] == opt]['Liczba'].values[0]} x)"
                selected_score = st.selectbox("Wybierz wynik:", score_options, format_func=format_func)
                if selected_score:
                    matches_with_score = df_scores[df_scores['wynik_std'] == selected_score].copy()
                    if 'dt_obj' in matches_with_score.columns: matches_with_score = matches_with_score.sort_values('dt_obj', ascending=False)
                    st.dataframe(matches_with_score[['data meczu', 'rywal', 'rozgrywki']].style.map(color_results_logic, subset=['wynik'] if 'wynik' in matches_with_score else None), use_container_width=True, hide_index=True, height=400)

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

