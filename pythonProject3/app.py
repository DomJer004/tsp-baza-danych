import streamlit as st
import pandas as pd
import datetime
import re

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")

# --- 2. LOGOWANIE ---
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

def login():
    st.title("🔒 Panel Logowania TSP")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Użytkownik")
        p = st.text_input("Hasło", type="password")
        if st.button("Zaloguj", use_container_width=True):
            if u in USERS and USERS[u] == p:
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("Błąd logowania")

def logout():
    st.session_state['logged_in'] = False
    st.rerun()

if not st.session_state['logged_in']:
    login()
    st.stop()

# --- GŁÓWNA APLIKACJA ---
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

try:
    import plotly.express as px
    HAS_PLOTLY = True
except: HAS_PLOTLY = False

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
    try: df = pd.read_csv(filename, encoding='utf-8')
    except: 
        try: df = pd.read_csv(filename, encoding='windows-1250')
        except: return None
    df = df.fillna("-")
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Usuwanie kolumn technicznych
    cols_drop = [c for c in df.columns if 'lp' in c]
    if cols_drop: df = df.drop(columns=cols_drop)

    # Formatowanie kolejki (usuwanie wiodących zer: 01 -> 1)
    if 'kolejka' in df.columns:
        df['kolejka'] = df['kolejka'].apply(lambda x: str(int(x)) if str(x).isdigit() else x)
        
    # FIX: Mapowanie literówki 1999/20 na 1999/00 w strzelcach
    if '1999/20' in df.columns:
        df.rename(columns={'1999/20': '1999/00'}, inplace=True)

    return df

def prepare_flags(df, col='narodowość'):
    if col not in df.columns:
        poss = [c for c in df.columns if c in ['kraj', 'narodowosc']]
        if poss: col = poss[0]
    if col in df.columns:
        df['flaga'] = df[col].apply(get_flag_url)
        df = df.rename(columns={col: 'Narodowość', 'flaga': 'Flaga'})
        cols = list(df.columns)
        if 'Narodowość' in cols and 'Flaga' in cols:
            cols.remove('Flaga')
            df.insert(cols.index('Narodowość')+1, 'Flaga', df.pop('Flaga'))
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

# --- MENU ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Moduł:", [
    "Aktualny Sezon (25/26)", 
    "Centrum Zawodników", 
    "Centrum Meczowe", 
    "Trenerzy"
])
st.sidebar.divider()
if st.sidebar.button("Wyloguj"): logout()

# --- MODUŁY ---

if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Statystyki 2025/2026")
    df = load_data("25_26.csv")
    if df is not None:
        filt = st.text_input("Szukaj w kadrze:")
        if filt: df = df[df.astype(str).apply(lambda x: x.str.contains(filt, case=False)).any(axis=1)]
        df = prepare_flags(df)
        df.index = range(1, len(df)+1)
        st.dataframe(df, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

elif opcja == "Centrum Zawodników":
    st.header("🏃 Centrum Zawodników TSP")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Wyszukiwarka (Statystyki)", "Strzelcy", "Klub 100", "Transfery", "Młoda Ekstraklasa"])

    with tab1:
        st.subheader("Baza Zawodników - Występy i Gole")
        st.caption("Legenda: **Mecze (Gole ➕)**. Kliknij '➕' (wybierz zawodnika poniżej), aby zobaczyć szczegóły bramek.")
        
        df_p = load_data("pilkarze.csv")
        df_s = load_data("strzelcy.csv")
        df_mecze = load_data("mecze.csv")
        
        if df_p is not None:
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: search = st.text_input("Szukaj zawodnika:")
            with c2:
                # Pobieranie sezonów z kolumn
                sezony = sorted([c for c in df_p.columns if re.match(r'\d{4}/\d{2}', c)], reverse=True)
                wyb_sezony = st.multiselect("Filtruj wg sezonu:", sezony)
            with c3:
                obcy = st.checkbox("Tylko obcokrajowcy", key="obcy_search")
            
            # Kopia do wyświetlania
            df_disp = df_p.copy()
            
            # Filtrowanie wierszy
            if search:
                df_disp = df_disp[df_disp['imię i nazwisko'].astype(str).str.contains(search, case=False)]
            if obcy and 'narodowość' in df_disp.columns:
                df_disp = df_disp[~df_disp['narodowość'].str.contains("Polska", na=False)]
            
            # --- ŁĄCZENIE DANYCH (MECZE + GOLE) ---
            if df_s is not None:
                # Indeksujemy po nazwisku dla szybkiego dostępu
                df_s_idx = df_s.set_index('imię i nazwisko')
                
                # Funkcja formatująca komórkę
                def format_cell(row, col_name):
                    val_p = row[col_name]
                    name = row['imię i nazwisko']
                    
                    # Pobierz gole
                    val_s = 0
                    if name in df_s_idx.index and col_name in df_s_idx.columns:
                        g = df_s_idx.at[name, col_name]
                        val_s = int(pd.to_numeric(g, errors='coerce')) if pd.notnull(g) else 0
                    
                    # Logika wyświetlania
                    # Jeśli brak występów (NaN/-) i brak goli -> "-"
                    if (pd.isna(val_p) or str(val_p) == '-') and val_s == 0:
                        return "-"
                    
                    # Formatuj występy
                    apps = str(int(float(val_p))) if (pd.notnull(val_p) and str(val_p) != '-') else "0"
                    
                    if val_s > 0:
                        return f"{apps} ({val_s} ➕)"
                    else:
                        return f"{apps} (0)"

                # Aplikujemy formatowanie dla wybranych sezonów
                cols_to_process = wyb_sezony if wyb_sezony else sezony
                for col in cols_to_process:
                    if col in df_disp.columns:
                        df_disp[col] = df_disp.apply(lambda row: format_cell(row, col), axis=1)
            
            # Ograniczenie kolumn do wyświetlenia
            base_cols = ['imię i nazwisko', 'narodowość', 'pozycja', 'wiek']
            final_cols = base_cols + cols_to_process + ['suma']
            # Filtrujemy tylko te co istnieją
            final_cols = [c for c in final_cols if c in df_disp.columns]
            
            df_show = prepare_flags(df_disp[final_cols])
            df_show.index = range(1, len(df_show)+1)
            
            st.dataframe(df_show, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
            
            # --- INTERAKCJA: SZCZEGÓŁY BRAMEK ---
            st.divider()
            st.subheader("🔍 Sprawdź szczegóły bramek")
            
            # Lista zawodników z tabeli
            dostepni_gracze = sorted(df_show['imię i nazwisko'].unique())
            wybrany_gracz = st.selectbox("Wybierz zawodnika, aby zobaczyć listę meczów z golami:", [""] + dostepni_gracze)
            
            if wybrany_gracz and df_mecze is not None:
                st.markdown(f"**Gole zawodnika: {wybrany_gracz}**")
                found_matches = []
                
                # Szukamy w meczach
                if 'strzelcy' in df_mecze.columns:
                    # Filtrujemy mecze gdzie w ogóle są strzelcy
                    mecze_z_golami = df_mecze[df_mecze['strzelcy'].notna() & (df_mecze['strzelcy'] != '')]
                    
                    for idx, row in mecze_z_golami.iterrows():
                        strzelcy_map = parse_scorers(row['strzelcy'])
                        # Sprawdzamy czy wybrany gracz strzelił (klucze w mapie to nazwiska)
                        # Uwaga: parse_scorers zwraca nazwisko. Trzeba porównać flexybilnie.
                        # Proste porównanie 'in'
                        if wybrany_gracz in strzelcy_map:
                            gole = strzelcy_map[wybrany_gracz]
                            found_matches.append({
                                'Sezon': row.get('sezon', '-'),
                                'Data': row.get('data meczu', '-'),
                                'Rywal': row.get('rywal', '-'),
                                'Wynik': row.get('wynik', '-'),
                                'Gole': gole,
                                'Strzelcy (pełna lista)': row['strzelcy']
                            })
                
                if found_matches:
                    df_goals = pd.DataFrame(found_matches)
                    st.dataframe(df_goals, use_container_width=True)
                else:
                    st.info("Ten zawodnik nie strzelił żadnej bramki w dostępnej bazie meczów (lub nazwisko w bazie meczów różni się pisownią).")

    with tab2:
        st.subheader("Klasyfikacja Strzelców")
        df = load_data("strzelcy.csv")
        if df is not None:
            if 'gole' in df.columns or 'SUMA' in df.columns: # Strzelcy maja SUMA jako total
                target_col = 'SUMA' if 'SUMA' in df.columns else 'gole'
                sez = ["Wszystkie"] + sorted([c for c in df.columns if re.match(r'\d{4}/\d{2}', c)], reverse=True)
                c1, c2 = st.columns([2,1])
                sel = c1.selectbox("Okres:", sez, key="sel_strzelcy")
                obcy = c2.checkbox("Obcokrajowcy", key="obcy_strzelcy")
                df = prepare_flags(df)
                if obcy and 'Narodowość' in df.columns: df = df[~df['Narodowość'].str.contains("Polska", na=False)]
                
                # Grupowanie
                cols_grp = ['imię i nazwisko', 'Narodowość', 'Flaga'] if 'Narodowość' in df.columns else ['imię i nazwisko']
                
                if sel == "Wszystkie":
                    # Suma z kolumny SUMA
                    show = df[cols_grp + [target_col]].rename(columns={target_col: 'Gole'})
                else:
                    # Suma z konkretnego sezonu
                    if sel in df.columns:
                        show = df[cols_grp + [sel]].rename(columns={sel: 'Gole'})
                        show = show[show['Gole'].notna()] # Tylko ci co strzelili
                    else:
                        show = pd.DataFrame()

                if not show.empty:
                    show['Gole'] = pd.to_numeric(show['Gole'], errors='coerce').fillna(0).astype(int)
                    show = show.sort_values('Gole', ascending=False)
                    show.index = range(1, len(show)+1)
                    st.dataframe(show, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
            else: st.error("Brak kolumny z golami")

    with tab3:
        st.subheader("Klub 100 (Najwięcej występów)")
        df = load_data("pilkarze.csv")
        if df is not None:
            # Szukamy kolumny SUMA (w nowym pliku jest SUMA)
            target = 'SUMA' if 'SUMA' in df.columns else next((c for c in df.columns if 'suma' in c.lower()), None)
            
            if target:
                df[target] = pd.to_numeric(df[target], errors='coerce').fillna(0).astype(int)
                df = df[df[target] >= 100].sort_values(target, ascending=False)
                st.bar_chart(df.head(30).set_index('imię i nazwisko')[target])
                df = prepare_flags(df)
                df = df.rename(columns={target: 'Mecze'})
                df.index = range(1, len(df)+1)
                st.dataframe(df[['imię i nazwisko', 'Flaga', 'Narodowość', 'Mecze']], use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
            else: st.error("Brak kolumny z liczbą meczów (SUMA)")

    with tab4:
        st.subheader("Historia Transferów")
        df = load_data("transfery.csv")
        if df is not None:
            if 'kwota PLN' in df.columns:
                df['val'] = df['kwota PLN'].astype(str).str.replace(' zł', '').str.replace(' ', '').str.replace(',', '.')
                df['val'] = pd.to_numeric(df['val'], errors='coerce').fillna(0).astype(int)
                top10 = df.sort_values('val', ascending=False).head(10)
                if HAS_PLOTLY:
                    fig = px.bar(top10, x='imię i nazwisko', y='val', text='val', title="Top 10 Najdroższych Transferów (PLN)")
                    st.plotly_chart(fig, use_container_width=True)
            
            df = prepare_flags(df, 'narodowość')
            df.index = range(1, len(df)+1)
            st.dataframe(df.drop(columns=['val'], errors='ignore'), use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

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
                        
                        cd = next((c for c in sub.columns if 'data' in c and 'sort' not in c), None) or next((c for c in sub.columns if 'data' in c), None)
                        if cd:
                            sub['dt'] = pd.to_datetime(sub[cd], dayfirst=True, errors='coerce')
                            sub = sub.sort_values('dt', ascending=False)
                            last_5 = sub.head(5)['wynik']
                            form = []
                            for res in last_5:
                                r = parse_result(res)
                                if r: form.append("✅" if r[0]>r[1] else ("❌" if r[0]<r[1] else "➖"))
                            c4.metric("Forma (ost. 5)", " ".join(form))
                            sub = sub.drop(columns=['dt'])

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
                    fig.update_layout(xaxis_title="Sezon", yaxis_title="Średnia widzów")
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
                                    for s, c in parse_scorers(m['strzelcy']).items(): all_scorers[s] = all_scorers.get(s, 0) + c
                            
                            coach_matches['pts'] = points_list
                            coach_matches['rolling_avg'] = coach_matches['pts'].rolling(window=5, min_periods=1).mean()
                            
                            if HAS_PLOTLY:
                                st.plotly_chart(px.line(x=coach_matches['dt'], y=coach_matches['rolling_avg'], markers=True, title=f"Forma (śr. pkt z 5 meczów): {wybrany_trener}", labels={'y': 'Śr. pkt'}), use_container_width=True)
                            
                            if all_scorers:
                                st.write("⚽ Najlepsi strzelcy (z samobójami):")
                                df_s = pd.DataFrame(list(all_scorers.items()), columns=['Zawodnik', 'Gole']).sort_values('Gole', ascending=False).reset_index(drop=True)
                                df_s.index = range(1, len(df_s)+1)
                                st.dataframe(df_s, use_container_width=True)
                            
                            st.write(f"Lista meczów ({len(coach_matches)}):")
                            view_c = [c for c in coach_matches.columns if c not in ['dt', 'data sortowania', 'mecz_id', 'pts', 'rolling_avg']]
                            coach_matches.index = range(1, len(coach_matches)+1)
                            st.dataframe(coach_matches[view_c].style.map(color_results_logic, subset=['wynik']), use_container_width=True)
                        else: st.warning("Brak meczów.")
                    else: st.error("Brak kolumny z datą w pliku mecze.csv.")

