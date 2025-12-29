import streamlit as st
import pandas as pd
import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# Próba importu plotly
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 2. MAPOWANIE KRAJÓW (ROZSZERZONE) ---
# Klucze małymi literami dla pewności dopasowania
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
    'austria': 'at', 'brazylia': 'br', 'szkocja': 'gb-sct',
    'walia': 'gb-wls', 'irlandia': 'ie', 'irlandia północna': 'gb-nir',
    'rosja': 'ru', 'dania': 'dk', 'norwegia': 'no', 'szwajcaria': 'ch',
    'rumunia': 'ro', 'cypr': 'cy', 'macedonia': 'mk', 'czarnogóra': 'me',
    'ghana': 'gh', 'estonia': 'ee', 'haiti': 'ht', 'kanada': 'ca', 
    'wybrzeże kości słoniowej': 'ci', 'maroko': 'ma', 'tunezja': 'tn',
    'algieria': 'dz', 'egipt': 'eg', 'islandia': 'is', 'korea południowa': 'kr',
    'australia': 'au', 'urugwaj': 'uy', 'chile': 'cl', 'paragwaj': 'py'
}

# --- 3. FUNKCJE POMOCNICZE ---

def get_flag_url(country_name):
    """Generuje URL do flagi z Flagpedii na podstawie nazwy kraju."""
    if not isinstance(country_name, str):
        return None
    # Pobieramy pierwszy człon (np. "Haiti" z "Haiti/Dania") i czyścimy
    first_country = country_name.split('/')[0].strip().lower()
    
    # Próba bezpośrednia
    iso_code = COUNTRY_TO_ISO.get(first_country)
    
    # Jeśli nie znaleziono, można spróbować szukać częściowo (opcjonalne)
    if not iso_code:
        for name, code in COUNTRY_TO_ISO.items():
            if name in first_country:
                iso_code = code
                break
    
    if iso_code:
        return f"https://flagcdn.com/w40/{iso_code}.png"
    return None

@st.cache_data
def load_data(filename):
    """
    Pancerna funkcja ładowania danych.
    Obsługuje kodowanie, normalizuje kolumny (małe litery, bez spacji), usuwa LP.
    """
    try:
        df = pd.read_csv(filename, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(filename, encoding='windows-1250')
        except:
            try:
                df = pd.read_csv(filename, encoding='latin-1')
            except:
                st.error(f"❌ Nie udało się otworzyć pliku: {filename}. Sprawdź kodowanie.")
                return None
    except FileNotFoundError:
        st.error(f"❌ Nie znaleziono pliku: {filename}")
        return None
    
    # Normalizacja
    df = df.fillna("-")
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Usuwanie kolumny LP
    cols_to_drop = [c for c in df.columns if c.replace('.', '') == 'lp']
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    return df

def prepare_dataframe_with_flags(df, country_col='narodowość'):
    """Dodaje kolumnę z flagą (URL obrazka) obok kolumny z nazwą kraju."""
    # Szukamy kolumny, jeśli podana nazwa nie istnieje (np. może być 'kraj' zamiast 'narodowość')
    if country_col not in df.columns:
        if 'kraj' in df.columns: country_col = 'kraj'
        elif 'narodowosc' in df.columns: country_col = 'narodowosc'
    
    if country_col in df.columns:
        df['flaga'] = df[country_col].apply(get_flag_url)
        df = df.rename(columns={country_col: 'Narodowość', 'flaga': 'Flaga'})
        
        # Przesunięcie kolumny Flaga
        cols = list(df.columns)
        if 'Narodowość' in cols and 'Flaga' in cols:
            cols.remove('Flaga')
            idx = cols.index('Narodowość')
            cols.insert(idx + 1, 'Flaga')
            df = df[cols]
    return df

def parse_result(val):
    """Analizuje wynik meczu (np. '1-0', '2 : 2'). Zwraca (gole_tsp, gole_rywal)."""
    if not isinstance(val, str): return None
    val = val.replace('-', ':').replace(' ', '')
    if ':' in val:
        try:
            p = val.split(':')
            return int(p[0]), int(p[1])
        except: return None
    return None

def color_results_logic(val):
    """Funkcja kolorująca wynik w tabeli (Pandas Styler)."""
    res = parse_result(val)
    if res:
        t, o = res
        if t > o: return 'color: #28a745; font-weight: bold' # Zielony
        elif t < o: return 'color: #dc3545; font-weight: bold' # Czerwony
        else: return 'color: #fd7e14; font-weight: bold' # Pomarańczowy
    return ''

# --- 4. MENU GŁÓWNE ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Wybierz moduł:", [
    "Aktualny Sezon (25/26)",
    "Wyszukiwarka Piłkarzy", 
    "Historia Meczów", 
    "⚽ Klasyfikacja Strzelców",
    "Klub 100",
    "Frekwencja",
    "Rywale (H2H)",
    "Trenerzy",
    "Transfery",
    "Statystyki Wyników",
    "Młoda Ekstraklasa"
])

# =========================================================
# MODUŁ 1: AKTUALNY SEZON
# =========================================================
if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Statystyki sezonu 2025/2026")
    df = load_data("25_26.csv")
    
    if df is not None:
        filter_text = st.text_input("Szukaj w kadrze:")
        if filter_text:
            df = df[df.astype(str).apply(lambda x: x.str.contains(filter_text, case=False)).any(axis=1)]

        df = prepare_dataframe_with_flags(df, 'narodowość')

        col_config = {
            "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
            "gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
            "asysty": st.column_config.NumberColumn("Asysty", format="%d 🅰️"),
            "mecze": st.column_config.NumberColumn("Mecze", format="%d"),
            "minuty": st.column_config.NumberColumn("Minuty", format="%d")
        }
        
        st.dataframe(df, use_container_width=True, column_config=col_config, hide_index=True)

# =========================================================
# MODUŁ 2: WYSZUKIWARKA PIŁKARZY
# =========================================================
elif opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Baza Zawodników")
    df = load_data("pilkarze.csv")
    
    if df is not None:
        c1, c2 = st.columns([3, 1])
        search = c1.text_input("🔍 Wpisz nazwisko:")
        only_foreigners = c2.checkbox("🌍 Tylko obcokrajowcy")
        
        df = prepare_dataframe_with_flags(df, 'narodowość')
        
        if only_foreigners and 'Narodowość' in df.columns:
            df = df[~df['Narodowość'].astype(str).str.contains("Polska", case=False, na=False)]

        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                "wzrost": st.column_config.NumberColumn("Wzrost", format="%d cm"),
                "waga": st.column_config.NumberColumn("Waga", format="%d kg")
            }
        )

# =========================================================
# MODUŁ 3: HISTORIA MECZÓW
# =========================================================
elif opcja == "Historia Meczów":
    st.header("🏟️ Archiwum Meczów")
    df = load_data("mecze.csv")
    
    if df is not None:
        if 'wynik' not in df.columns:
            st.error("Brak kolumny 'wynik'.")
            st.stop()

        sezony = []
        if 'sezon' in df.columns:
            # Filtrujemy, żeby brać tylko sensowne sezony (np. 2023/24)
            raw_sezony = sorted(df['sezon'].astype(str).unique(), reverse=True)
            sezony = [s for s in raw_sezony if len(s) > 4]

        c1, c2 = st.columns(2)
        wybrany_sezon = c1.selectbox("Wybierz sezon:", sezony) if sezony else None
        rywal_filter = c2.text_input("Filtruj po rywalu:")
        
        matches = df.copy()
        if wybrany_sezon:
            matches = matches[matches['sezon'] == wybrany_sezon]
        if rywal_filter:
            matches = matches[matches.astype(str).apply(lambda x: x.str.contains(rywal_filter, case=False)).any(axis=1)]

        # Szukanie kolumny podziału (liga/puchar)
        col_roz = next((c for c in matches.columns if c in ['rozgrywki', 'liga', 'rodzaj', 'typ']), None)

        if matches.empty:
            st.warning("Brak meczów.")
        else:
            datasets = []
            if col_roz:
                for r in matches[col_roz].unique():
                    datasets.append((r, matches[matches[col_roz] == r].copy()))
            else:
                datasets.append(("Wszystkie", matches))

            # Tworzenie zakładek
            tabs = st.tabs([d[0] for d in datasets]) if col_roz else [st]

            for container, (name, subset) in zip(tabs, datasets):
                with container:
                    # Sortowanie chronologiczne
                    if 'data sortowania' in subset.columns:
                        subset = subset.sort_values('data sortowania', ascending=False)
                    elif 'data meczu' in subset.columns:
                        subset = subset.sort_values('data meczu', ascending=False)
                    
                    # Szybki bilans
                    w, r, p = 0, 0, 0
                    for res in subset['wynik']:
                        parsed = parse_result(res)
                        if parsed:
                            if parsed[0] > parsed[1]: w += 1
                            elif parsed[0] < parsed[1]: p += 1
                            else: r += 1
                    
                    st.caption(f"📊 Bilans: ✅ {w} W | ➖ {r} R | ❌ {p} P")
                    
                    # Ukrywanie technicznych kolumn
                    view = subset.drop(columns=['mecz', 'data sortowania'], errors='ignore')
                    st.dataframe(view.style.map(color_results_logic, subset=['wynik']), use_container_width=True, hide_index=True)

# =========================================================
# MODUŁ 4: STRZELCY
# =========================================================
elif opcja == "⚽ Klasyfikacja Strzelców":
    st.header("⚽ Klasyfikacja Strzelców")
    df = load_data("strzelcy.csv")
    
    if df is not None:
        if 'gole' not in df.columns:
            st.error("Błąd: Brak kolumny 'gole'.")
            st.stop()

        sezony = ["Wszystkie sezony"] + sorted(df['sezon'].unique(), reverse=True) if 'sezon' in df.columns else ["Wszystkie"]
        
        c1, c2 = st.columns([2, 1])
        wyb_sezon = c1.selectbox("Wybierz okres:", sezony)
        tylko_obcy = c2.checkbox("🌍 Tylko obcokrajowcy")

        df_fil = df.copy()
        
        # Filtrowanie obcokrajowców
        kraj_col = next((c for c in df_fil.columns if c in ['kraj', 'narodowość']), None)
        if tylko_obcy and kraj_col:
            df_fil = df_fil[~df_fil[kraj_col].astype(str).str.contains("Polska", case=False)]

        # Grupowanie
        cols_grp = ['imię i nazwisko']
        if kraj_col: cols_grp.append(kraj_col)
        
        if wyb_sezon == "Wszystkie sezony":
            df_show = df_fil.groupby(cols_grp, as_index=False)['gole'].sum()
        elif 'sezon' in df_fil.columns:
            df_show = df_fil[df_fil['sezon'] == wyb_sezon].copy()
        else:
            df_show = df_fil

        if not df_show.empty:
            df_show = df_show.sort_values('gole', ascending=False)
            if kraj_col:
                df_show = prepare_dataframe_with_flags(df_show, kraj_col)
            
            # Wymuszenie int i nazwy
            df_show['gole'] = pd.to_numeric(df_show['gole'], errors='coerce').fillna(0).astype(int)
            df_show = df_show.rename(columns={'imię i nazwisko': 'Zawodnik', 'gole': 'Bramki'})
            df_show.index = range(1, len(df_show) + 1)
            
            st.dataframe(
                df_show, 
                use_container_width=True,
                column_config={
                    "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                    "Bramki": st.column_config.NumberColumn("Bramki", format="%d ⚽")
                }
            )
            st.caption(f"Suma goli w tabeli: {df_show['Bramki'].sum()}")
        else:
            st.warning("Brak danych.")

# =========================================================
# MODUŁ 5: KLUB 100 (Z PILKARZY)
# =========================================================
elif opcja == "Klub 100":
    st.header("💯 Klub 100 (Najwięcej Meczów)")
    df = load_data("pilkarze.csv")
    
    if df is not None:
        # Szukamy kolumny meczów (może nazywać się 'suma', 'mecze' itp.)
        target_col = next((c for c in df.columns if any(k in c for k in ['suma', 'mecze', 'występy'])), None)
        
        if target_col:
            # Konwersja na int
            df[target_col] = pd.to_numeric(
                df[target_col].astype(str).str.replace(" ", ""), 
                errors='coerce'
            ).fillna(0).astype(int)
            
            # FILTR: >= 100 meczów
            df_100 = df[df[target_col] >= 100].copy()
            
            if not df_100.empty:
                df_100 = df_100.sort_values(by=target_col, ascending=False)

                st.subheader(f"Członkowie Klubu 100 (Razem: {len(df_100)})")
                st.bar_chart(df_100.head(30).set_index('imię i nazwisko')[target_col])
                
                # Tabela
                df_100 = prepare_dataframe_with_flags(df_100, 'narodowość')
                df_100 = df_100.rename(columns={'imię i nazwisko': 'Zawodnik', target_col: 'Mecze'})
                df_100.index = range(1, len(df_100) + 1)
                
                # Wybieramy tylko istotne kolumny do wyświetlenia
                cols_to_show = ['Zawodnik', 'Flaga', 'Narodowość', 'Mecze']
                # Jeśli w pilkarze.csv są inne ciekawe kolumny (np. pozycja), można je dodać
                available_cols = [c for c in cols_to_show if c in df_100.columns]
                
                st.dataframe(
                    df_100[available_cols],
                    use_container_width=True,
                    column_config={
                        "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                        "Mecze": st.column_config.NumberColumn("Mecze", format="%d")
                    }
                )
            else:
                st.info("Brak zawodników z 100+ meczami.")
        else:
            st.error("W pliku 'pilkarze.csv' nie znaleziono kolumny 'suma' lub 'mecze'.")
            st.write("Dostępne kolumny:", list(df.columns))
    else:
        st.error("Brak pliku: pilkarze.csv")

# =========================================================
# MODUŁ 6: FREKWENCJA
# =========================================================
elif opcja == "Frekwencja":
    st.header("📢 Frekwencja na stadionie")
    df = load_data("frekwencja.csv")
    if df is not None:
        col_avg = next((c for c in df.columns if 'średnia' in c), None)
        if col_avg and 'sezon' in df.columns:
            df['num'] = pd.to_numeric(df[col_avg].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0)
            st.line_chart(df.set_index('sezon')['num'])
        
        st.dataframe(df.drop(columns=['num'], errors='ignore'), use_container_width=True, hide_index=True)

# =========================================================
# MODUŁ 7: RYWALE (H2H Z MECZÓW)
# =========================================================
elif opcja == "Rywale (H2H)":
    st.header("⚔️ Bilans z Rywalami")
    df = load_data("mecze.csv")
    
    if df is not None:
        # Szukamy kolumny rywala
        col_rywal = next((c for c in df.columns if c in ['rywal', 'przeciwnik', 'klub']), None)
        
        if col_rywal and 'wynik' in df.columns:
            
            def calculate_stats(subset):
                mecze = len(subset)
                w, r, p, g_strz, g_stra = 0, 0, 0, 0, 0
                for res in subset['wynik']:
                    parsed = parse_result(res)
                    if parsed:
                        ts, op = parsed
                        g_strz += ts
                        g_stra += op
                        if ts > op: w += 1
                        elif ts < op: p += 1
                        else: r += 1
                return pd.Series({
                    'Mecze': mecze, 'Zwycięstwa': w, 'Remisy': r, 'Porażki': p,
                    'Bramki': f"{g_strz}:{g_stra}", 'Bilans': g_strz - g_stra,
                    'Punkty': (w*3 + r), 'Śr. pkt': (w*3 + r)/mecze if mecze else 0
                })

            tab1, tab2 = st.tabs(["🔎 Analiza Rywala", "📊 Tabela Wszech Czasów"])

            with tab1:
                rywale = sorted(df[col_rywal].astype(str).unique())
                wybrany = st.selectbox("Wybierz rywala:", rywale)
                
                if wybrany:
                    subset = df[df[col_rywal] == wybrany].copy()
                    stats = calculate_stats(subset)
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Mecze", int(stats['Mecze']))
                    c2.metric("Bilans (Z-R-P)", f"{int(stats['Zwycięstwa'])}-{int(stats['Remisy'])}-{int(stats['Porażki'])}")
                    c3.metric("Bramki", stats['Bramki'])
                    c4.metric("Średnia pkt", f"{stats['Śr. pkt']:.2f}")
                    
                    st.divider()
                    st.write("Historia spotkań:")
                    
                    # Sortowanie po dacie (jeśli jest)
                    col_data = next((c for c in subset.columns if 'data' in c and 'sort' not in c), None)
                    if col_data:
                        subset['_dt'] = pd.to_datetime(subset[col_data], dayfirst=True, errors='coerce')
                        subset = subset.sort_values('_dt', ascending=False).drop(columns=['_dt'])
                    
                    view = subset.drop(columns=['mecz', 'data sortowania'], errors='ignore')
                    st.dataframe(view.style.map(color_results_logic, subset=['wynik']), use_container_width=True, hide_index=True)

            with tab2:
                with st.spinner("Generowanie tabeli..."):
                    df_all = df.groupby(col_rywal).apply(calculate_stats).reset_index()
                    df_all = df_all.sort_values(['Punkty', 'Bilans'], ascending=False)
                    df_all.index = range(1, len(df_all)+1)
                    
                    st.dataframe(
                        df_all, use_container_width=True,
                        column_config={
                            "Mecze": st.column_config.NumberColumn("M", format="%d"),
                            "Zwycięstwa": st.column_config.NumberColumn("Z", format="%d"),
                            "Remisy": st.column_config.NumberColumn("R", format="%d"),
                            "Porażki": st.column_config.NumberColumn("P", format="%d"),
                            "Punkty": st.column_config.NumberColumn("Pkt", format="%d"),
                            "Śr. pkt": st.column_config.NumberColumn(format="%.2f")
                        }
                    )
        else:
            st.error("Brak kolumny z nazwą rywala lub wynikiem w mecze.csv")

# =========================================================
# MODUŁ 8: TRENERZY
# =========================================================
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP")
    df = load_data("trenerzy.csv")
    
    if df is not None:
        # Pancerne daty
        def smart_date(s):
            d = pd.to_datetime(s, format='%d.%m.%Y', errors='coerce')
            if d.isna().mean() > 0.5: d = pd.to_datetime(s, errors='coerce')
            return d

        if 'początek' in df.columns: df['początek_dt'] = smart_date(df['początek'])
        if 'koniec' in df.columns: 
            df['koniec_dt'] = smart_date(df['koniec'])
            df['koniec_dt'] = df['koniec_dt'].fillna(pd.Timestamp.today())

        df = prepare_dataframe_with_flags(df, 'narodowość')
        
        # Konwersja na int
        for c in ['mecze', 'punkty', 'wygrane', 'remisy', 'przegrane']:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

        tab1, tab2, tab3 = st.tabs(["📋 Lista Chronologiczna", "📊 Rankingi", "📈 Oś Czasu / Analiza"])

        with tab1:
            view = df.sort_values('początek_dt', ascending=False)
            cols = [c for c in ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'wiek', 'początek', 'koniec', 'mecze', 'punkty', 'śr. pkt /mecz'] if c in view.columns]
            st.dataframe(view[cols], use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small"), "śr. pkt /mecz": st.column_config.NumberColumn(format="%.2f")})

        with tab2:
            st.subheader("Podsumowanie zbiorcze")
            grp = ['imię i nazwisko', 'Narodowość', 'Flaga']
            agg = df.groupby([c for c in grp if c in df.columns], as_index=False)[['mecze', 'punkty', 'wygrane']].sum()
            agg['śr. pkt /mecz'] = agg.apply(lambda x: x['punkty']/x['mecze'] if x['mecze']>0 else 0, axis=1)
            agg = agg.sort_values('punkty', ascending=False).reset_index(drop=True)
            agg.index += 1
            st.dataframe(agg, use_container_width=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small"), "śr. pkt /mecz": st.column_config.NumberColumn(format="%.2f")})

        with tab3:
            st.subheader("📈 Analiza Trenera")
            
            # Główny scatter
            if HAS_PLOTLY:
                fig = px.scatter(df.sort_values('początek_dt'), x="początek_dt", y="śr. pkt /mecz", size="mecze", color="śr. pkt /mecz", hover_name="imię i nazwisko", title="Efektywność kadencji", color_continuous_scale="RdYlGn")
                st.plotly_chart(fig, use_container_width=True)

            # Analiza szczegółowa
            wybrany = st.selectbox("Wybierz trenera:", sorted(df['imię i nazwisko'].unique()))
            if wybrany:
                coach_rows = df[df['imię i nazwisko'] == wybrany]
                mecze_df = load_data("mecze.csv")
                
                if mecze_df is not None:
                    col_data = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None) or next((c for c in mecze_df.columns if 'data' in c), None)
                    
                    if col_data:
                        mecze_df['dt'] = pd.to_datetime(mecze_df[col_data], dayfirst=True, errors='coerce')
                        
                        # Filtracja
                        mask = pd.Series([False]*len(mecze_df))
                        for _, row in coach_rows.iterrows():
                            if pd.notnull(row['początek_dt']):
                                mask |= (mecze_df['dt'] >= row['początek_dt']) & (mecze_df['dt'] <= row['koniec_dt'])
                        
                        coach_matches = mecze_df[mask].sort_values('dt')
                        
                        if not coach_matches.empty:
                            # Wykres liniowy punktów
                            pts, acc = [], 0
                            for _, m in coach_matches.iterrows():
                                r = parse_result(m['wynik'])
                                if r: acc += (3 if r[0]>r[1] else (1 if r[0]==r[1] else 0))
                                pts.append(acc)
                            
                            if HAS_PLOTLY:
                                st.plotly_chart(px.line(x=coach_matches['dt'], y=pts, markers=True, title=f"Progres punktowy: {wybrany}"), use_container_width=True)
                            
                            st.write(f"Mecze ({len(coach_matches)}):")
                            view = coach_matches.drop(columns=['dt', 'data sortowania', 'mecz_id'], errors='ignore')
                            st.dataframe(view.style.map(color_results_logic, subset=['wynik']), use_container_width=True, hide_index=True)
                        else:
                            st.warning("Brak meczów w okresach pracy tego trenera (sprawdź daty w plikach).")
                    else:
                        st.error("Brak kolumny z datą w mecze.csv")

# =========================================================
# POZOSTAŁE
# =========================================================
elif opcja == "Transfery":
    st.header("💸 Transfery")
    df = load_data("transfery.csv")
    df = prepare_dataframe_with_flags(df, 'kraj' if df is not None and 'kraj' in df.columns else 'narodowość')
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

elif opcja == "Statystyki Wyników":
    st.header("🎲 Najczęstsze wyniki")
    df = load_data("wyniki.csv")
    if df is not None and 'wynik' in df.columns:
        st.bar_chart(df.set_index('wynik')['częstotliwość'])
        st.dataframe(df, use_container_width=True, hide_index=True)

elif opcja == "Młoda Ekstraklasa":
    st.header("🎓 Młoda Ekstraklasa")
    df = load_data("me.csv")
    df = prepare_dataframe_with_flags(df, 'kraj' if df is not None and 'kraj' in df.columns else 'narodowość')
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})
