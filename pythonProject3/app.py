import streamlit as st
import pandas as pd
import datetime
import re

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")

# --- 2. LOGOWANIE ---
USERS = {"Djero": "TSP1995", "KKowalski": "Tsp2025", "PPorebski": "TSP2025", "MCzerniak": "TSP2025", "SJaszczurowski": "TSP2025", "guest": "123456789"}

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

# --- MAPOWANIE KRAJÓW (PEŁNE + LIBERIA) ---
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
    cols_drop = [c for c in df.columns if 'lp' in c]
    if cols_drop: df = df.drop(columns=cols_drop)
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

def color_res(val):
    r = parse_result(val)
    if r:
        if r[0] > r[1]: return 'color: #28a745; font-weight: bold'
        elif r[0] < r[1]: return 'color: #dc3545; font-weight: bold'
        else: return 'color: #fd7e14; font-weight: bold'
    return ''

def parse_scorers(scorers_str):
    if not isinstance(scorers_str, str) or pd.isna(scorers_str) or scorers_str == '-':
        return {}
    parts = scorers_str.split(',')
    stats = {}
    current_scorer = None
    for part in parts:
        part = part.strip()
        if not part: continue
        if re.search(r'[a-zA-Z]', part):
            name = re.sub(r'\d+', '', part).strip()
            if name:
                current_scorer = name
                stats[current_scorer] = stats.get(current_scorer, 0) + 1
        else:
            if current_scorer: stats[current_scorer] += 1
    return stats

# --- MENU ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Moduł:", [
    "Aktualny Sezon (25/26)", "Wyszukiwarka Piłkarzy", "Historia Meczów", 
    "⚽ Klasyfikacja Strzelców", "Klub 100", "Frekwencja", "Rywale (H2H)", 
    "Trenerzy", "Transfery", "Statystyki Wyników", "Młoda Ekstraklasa"
])
st.sidebar.divider()
if st.sidebar.button("Wyloguj"): logout()

# --- MODUŁY ---

if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Statystyki 2025/2026")
    df = load_data("25_26.csv")
    if df is not None:
        filt = st.text_input("Szukaj:")
        if filt: df = df[df.astype(str).apply(lambda x: x.str.contains(filt, case=False)).any(axis=1)]
        df = prepare_flags(df)
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

elif opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Baza Zawodników")
    df = load_data("pilkarze.csv")
    if df is not None:
        c1, c2 = st.columns([3,1])
        s = c1.text_input("Szukaj:")
        obcy = c2.checkbox("Tylko obcokrajowcy")
        df = prepare_flags(df)
        if obcy and 'Narodowość' in df.columns: df = df[~df['Narodowość'].str.contains("Polska", na=False)]
        if s: df = df[df.astype(str).apply(lambda x: x.str.contains(s, case=False)).any(axis=1)]
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

elif opcja == "Historia Meczów":
    st.header("🏟️ Archiwum Meczów")
    df = load_data("mecze.csv")
    if df is not None:
        if 'wynik' not in df.columns: st.error("Brak kolumny 'wynik'")
        else:
            sezony = sorted([s for s in df['sezon'].astype(str).unique() if len(s)>4], reverse=True) if 'sezon' in df.columns else []
            c1, c2 = st.columns(2)
            sel_sez = c1.selectbox("Sezon:", sezony) if sezony else None
            filt = c2.text_input("Rywal:")
            m = df.copy()
            if sel_sez: m = m[m['sezon'] == sel_sez]
            if filt: m = m[m.astype(str).apply(lambda x: x.str.contains(filt, case=False)).any(axis=1)]
            roz = next((c for c in m.columns if c in ['rozgrywki', 'liga']), None)
            tabs = st.tabs([str(r) for r in m[roz].unique()]) if roz else [st]
            datasets = [(r, m[m[roz]==r]) for r in m[roz].unique()] if roz else [("All", m)]
            for tab, (n, sub) in zip(tabs, datasets):
                with tab:
                    col_d = next((c for c in sub.columns if 'data' in c and 'sort' not in c), None)
                    if col_d: sub = sub.sort_values(col_d, ascending=False)
                    w, r, p = 0, 0, 0
                    for x in sub['wynik']:
                        res = parse_result(x)
                        if res:
                            if res[0]>res[1]: w+=1
                            elif res[0]<res[1]: p+=1
                            else: r+=1
                    st.caption(f"Bilans: ✅ {w} | ➖ {r} | ❌ {p}")
                    st.dataframe(sub.style.map(color_res, subset=['wynik']), use_container_width=True, hide_index=True)

elif opcja == "⚽ Klasyfikacja Strzelców":
    st.header("⚽ Klasyfikacja Strzelców")
    df = load_data("strzelcy.csv")
    if df is not None:
        if 'gole' in df.columns:
            sez = ["Wszystkie"] + sorted(df['sezon'].unique(), reverse=True) if 'sezon' in df.columns else ["Wszystkie"]
            c1, c2 = st.columns([2,1])
            sel = c1.selectbox("Okres:", sez)
            obcy = c2.checkbox("Obcokrajowcy")
            df = prepare_flags(df)
            if obcy and 'Narodowość' in df.columns: df = df[~df['Narodowość'].str.contains("Polska", na=False)]
            grp = ['imię i nazwisko', 'Narodowość', 'Flaga'] if 'Narodowość' in df.columns else ['imię i nazwisko']
            if sel != "Wszystkie" and 'sezon' in df.columns: df = df[df['sezon'] == sel]
            show = df.groupby([c for c in grp if c in df.columns], as_index=False)['gole'].sum()
            show = show.sort_values('gole', ascending=False)
            show.index = range(1, len(show)+1)
            st.dataframe(show, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
        else: st.error("Brak kolumny 'gole'")

elif opcja == "Klub 100":
    st.header("💯 Klub 100")
    df = load_data("pilkarze.csv")
    if df is not None:
        target = next((c for c in df.columns if any(x in c for x in ['suma', 'mecze', 'występy'])), None)
        if target:
            df[target] = pd.to_numeric(df[target].astype(str).str.replace(" ", ""), errors='coerce').fillna(0).astype(int)
            df = df[df[target] >= 100].sort_values(target, ascending=False)
            st.bar_chart(df.head(30).set_index('imię i nazwisko')[target])
            df = prepare_flags(df)
            df = df.rename(columns={target: 'Mecze'})
            df.index = range(1, len(df)+1)
            st.dataframe(df[['imię i nazwisko', 'Flaga', 'Narodowość', 'Mecze']], use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
        else: st.error("Brak kolumny z liczbą meczów")

elif opcja == "Frekwencja":
    st.header("📢 Frekwencja")
    df = load_data("frekwencja.csv")
    if df is not None:
        col = next((c for c in df.columns if 'średnia' in c), None)
        if col and 'sezon' in df.columns:
            df['n'] = pd.to_numeric(df[col].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0).astype(int)
            
            # --- NOWY WYKRES I STATYSTYKI ---
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
                
            st.dataframe(df.drop(columns=['n'], errors='ignore'), use_container_width=True, hide_index=True)

elif opcja == "Rywale (H2H)":
    st.header("⚔️ Bilans z Rywalami")
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

            t1, t2 = st.tabs(["🔎 Analiza", "📊 Tabela"])
            with t1:
                sel = st.selectbox("Rywal:", sorted(df[col_r].unique()))
                if sel:
                    sub = df[df[col_r] == sel].copy()
                    stats = calc(sub)
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("Mecze", int(stats['Mecze']))
                    c2.metric("Bilans", f"{int(stats['Z'])}-{int(stats['R'])}-{int(stats['P'])}")
                    c3.metric("Bramki", stats['Bramki'])
                    
                    # FORMA
                    cd = next((c for c in sub.columns if 'data' in c and 'sort' not in c), None) or next((c for c in sub.columns if 'data' in c), None)
                    if cd:
                        sub['dt'] = pd.to_datetime(sub[cd], dayfirst=True, errors='coerce')
                        sub = sub.sort_values('dt', ascending=False)
                        last_5 = sub.head(5)['wynik']
                        form_icons = []
                        for res in last_5:
                            r = parse_result(res)
                            if r: form_icons.append("✅" if r[0]>r[1] else ("❌" if r[0]<r[1] else "➖"))
                        c4.metric("Forma (ost. 5)", " ".join(form_icons))
                        sub = sub.drop(columns=['dt'])

                    st.divider()
                    st.write("Lista meczów:")
                    st.dataframe(sub.style.map(color_res, subset=['wynik']), use_container_width=True, hide_index=True)
            with t2:
                all_stats = df.groupby(col_r).apply(calc).reset_index().sort_values(['Pkt'], ascending=False)
                all_stats.index = range(1, len(all_stats)+1)
                st.dataframe(all_stats, use_container_width=True)

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

        t1, t2, t3 = st.tabs(["Lista", "Rankingi", "Oś Czasu & Mecze"])
        with t1:
            v = df.sort_values('początek_dt', ascending=False)
            cols = [c for c in ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'początek', 'koniec', 'mecze', 'punkty'] if c in v.columns]
            st.dataframe(v[cols], use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
        with t2:
            agg = df.groupby(['imię i nazwisko', 'Narodowość', 'Flaga'], as_index=False)[['mecze', 'punkty']].sum()
            agg = agg.sort_values('punkty', ascending=False)
            agg.index = range(1, len(agg)+1)
            st.dataframe(agg, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
        with t3:
            st.subheader("📈 Analiza Szczegółowa")
            trenerzy_list = sorted(df['imię i nazwisko'].unique())
            wybrany_trener = st.selectbox("Wybierz trenera:", trenerzy_list)
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
                            total_pts, match_count, avg_hist = 0, 0, []
                            all_scorers = {}
                            for _, m in coach_matches.iterrows():
                                match_count += 1
                                r = parse_result(m['wynik'])
                                pts = 3 if r and r[0]>r[1] else (1 if r and r[0]==r[1] else 0)
                                total_pts += pts
                                avg_hist.append(total_pts / match_count)
                                if 'strzelcy' in m and pd.notnull(m['strzelcy']):
                                    for s, c in parse_scorers(m['strzelcy']).items(): all_scorers[s] = all_scorers.get(s, 0) + c
                            
                            if HAS_PLOTLY:
                                st.plotly_chart(px.line(x=coach_matches['dt'], y=avg_hist, markers=True, title=f"Średnia punktów (narastająco): {wybrany_trener}", labels={'y': 'Śr. pkt'}), use_container_width=True)
                            
                            if all_scorers:
                                st.write("⚽ Najlepsi strzelcy:")
                                st.dataframe(pd.DataFrame(list(all_scorers.items()), columns=['Zawodnik', 'Gole']).sort_values('Gole', ascending=False).reset_index(drop=True), use_container_width=True)
                            
                            st.write(f"Lista meczów ({len(coach_matches)}):")
                            view_c = [c for c in coach_matches.columns if c not in ['dt', 'data sortowania', 'mecz_id']]
                            st.dataframe(coach_matches[view_c].style.map(color_res, subset=['wynik']), use_container_width=True, hide_index=True)
                        else: st.warning("Brak meczów.")
                    else: st.error("Brak kolumny z datą.")

elif opcja == "Transfery":
    st.header("💸 Transfery")
    df = load_data("transfery.csv")
    if df is not None:
        # Czyszczenie i wykres
        if 'kwota PLN' in df.columns:
            df['val'] = df['kwota PLN'].astype(str).str.replace(' zł', '').str.replace(' ', '').str.replace(',', '.')
            df['val'] = pd.to_numeric(df['val'], errors='coerce').fillna(0).astype(int)
            top10 = df.sort_values('val', ascending=False).head(10)
            if HAS_PLOTLY:
                fig = px.bar(top10, x='imię i nazwisko', y='val', text='val', title="Top 10 Najdroższych Transferów (PLN)")
                st.plotly_chart(fig, use_container_width=True)
        
        df = prepare_flags(df, 'narodowość')
        st.dataframe(df.drop(columns=['val'], errors='ignore'), use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

elif opcja == "Statystyki Wyników":
    st.header("🎲 Wyniki")
    df = load_data("wyniki.csv")
    if df is not None: st.bar_chart(df.set_index('wynik')['częstotliwość']); st.dataframe(df, use_container_width=True)

elif opcja == "Młoda Ekstraklasa":
    st.header("🎓 Młoda Ekstraklasa")
    df = load_data("me.csv")
    df = prepare_flags(df, 'narodowość')
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
