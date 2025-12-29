import streamlit as st
import pandas as pd
import datetime

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# Próba importu plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 2. MAPOWANIE KRAJÓW (ROZSZERZONE) ---
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
    'algieria': 'dz', 'egipt': 'eg', 'islandia': 'is'
}

# --- 3. FUNKCJE POMOCNICZE ---

def get_flag_url(country_name):
    """Generuje URL do flagi z Flagpedii."""
    if not isinstance(country_name, str):
        return None
    # Pobieramy pierwszy człon (np. "Haiti" z "Haiti/Dania")
    first_country = country_name.split('/')[0].strip().lower()
    iso_code = COUNTRY_TO_ISO.get(first_country)
    if iso_code:
        return f"https://flagcdn.com/w40/{iso_code}.png"
    return None

@st.cache_data
def load_data(filename):
    """Pancerna funkcja ładowania danych."""
    try:
        df = pd.read_csv(filename, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(filename, encoding='windows-1250')
        except:
            try:
                df = pd.read_csv(filename, encoding='latin-1')
            except:
                st.error(f"❌ Nie udało się otworzyć pliku: {filename}.")
                return None
    except FileNotFoundError:
        st.error(f"❌ Nie znaleziono pliku: {filename}")
        return None
    
    df = df.fillna("-")
    df.columns = [c.strip().lower() for c in df.columns]
    
    cols_to_drop = [c for c in df.columns if c.replace('.', '') == 'lp']
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    return df

def prepare_dataframe_with_flags(df, country_col='narodowość'):
    """Dodaje kolumnę z flagą."""
    if country_col in df.columns:
        df['flaga'] = df[country_col].apply(get_flag_url)
        df = df.rename(columns={country_col: 'Narodowość', 'flaga': 'Flaga'})
        cols = list(df.columns)
        if 'Narodowość' in cols and 'Flaga' in cols:
            cols.remove('Flaga')
            idx = cols.index('Narodowość')
            cols.insert(idx + 1, 'Flaga')
            df = df[cols]
    return df

def parse_result(val):
    """Analizuje wynik meczu (zwraca: gole_nasze, gole_rywala)."""
    if not isinstance(val, str): return None
    val = val.replace('-', ':').replace(' ', '')
    if ':' in val:
        try:
            p = val.split(':')
            return int(p[0]), int(p[1])
        except: return None
    return None

def color_results_logic(val):
    """Koloruje wynik meczu."""
    res = parse_result(val)
    if res:
        t, o = res
        if t > o: return 'color: #28a745; font-weight: bold'
        elif t < o: return 'color: #dc3545; font-weight: bold'
        else: return 'color: #fd7e14; font-weight: bold'
    return ''

# --- 4. MENU ---
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

        df = prepare_dataframe_with_flags(df, 'narodowość' if 'narodowość' in df.columns else 'kraj')

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
        
        nat_col = 'narodowość' if 'narodowość' in df.columns else 'kraj'
        
        if only_foreigners and nat_col in df.columns:
            df = df[~df[nat_col].astype(str).str.contains("Polska", case=False, na=False)]

        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        df = prepare_dataframe_with_flags(df, nat_col)
        
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
            sezony = sorted(df['sezon'].astype(str).unique(), reverse=True)
            sezony = [s for s in sezony if len(s) > 4]

        c1, c2 = st.columns(2)
        wybrany_sezon = c1.selectbox("Wybierz sezon:", sezony) if sezony else None
        rywal_filter = c2.text_input("Filtruj po rywalu:")
        
        matches = df.copy()
        if wybrany_sezon:
            matches = matches[matches['sezon'] == wybrany_sezon]
        if rywal_filter:
            matches = matches[matches.astype(str).apply(lambda x: x.str.contains(rywal_filter, case=False)).any(axis=1)]

        col_roz = next((c for c in matches.columns if c in ['rozgrywki', 'liga', 'rodzaj']), None)

        if matches.empty:
            st.warning("Brak meczów.")
        else:
            datasets = []
            if col_roz:
                for r in matches[col_roz].unique():
                    datasets.append((r, matches[matches[col_roz] == r].copy()))
            else:
                datasets.append(("Wszystkie", matches))

            tabs = st.tabs([d[0] for d in datasets]) if col_roz else [st]

            for container, (name, subset) in zip(tabs, datasets):
                with container:
                    if 'data sortowania' in subset.columns:
                        subset = subset.sort_values('data sortowania', ascending=False)
                    
                    w, r, p = 0, 0, 0
                    for res in subset['wynik']:
                        parsed = parse_result(res)
                        if parsed:
                            if parsed[0] > parsed[1]: w += 1
                            elif parsed[0] < parsed[1]: p += 1
                            else: r += 1
                    
                    st.caption(f"📊 Bilans: ✅ {w} W | ➖ {r} R | ❌ {p} P")
                    
                    view = subset.drop(columns=['mecz', 'data sortowania'], errors='ignore')
                    st.dataframe(view.style.map(color_results_logic, subset=['wynik']), use_container_width=True, hide_index=True)

# =========================================================
# MODUŁ 4: STRZELCY
# =========================================================
elif opcja == "⚽ Klasyfikacja Strzelców":
    st.header("⚽ Klasyfikacja Strzelców")
    df = load_data("strzelcy.csv")
    
    if df is not None:
        sezony = ["Wszystkie sezony"] + sorted(df['sezon'].unique(), reverse=True) if 'sezon' in df.columns else ["Wszystkie"]
        
        c1, c2 = st.columns([2, 1])
        wyb_sezon = c1.selectbox("Wybierz okres:", sezony)
        tylko_obcy = c2.checkbox("🌍 Tylko obcokrajowcy")

        df_fil = df.copy()
        kraj_col = 'kraj' if 'kraj' in df_fil.columns else 'narodowość'
        
        if tylko_obcy and kraj_col in df_fil.columns:
            df_fil = df_fil[~df_fil[kraj_col].astype(str).str.contains("Polska", case=False)]

        cols_grp = ['imię i nazwisko', kraj_col] if kraj_col in df_fil.columns else ['imię i nazwisko']
        
        if wyb_sezon == "Wszystkie sezony":
            df_show = df_fil.groupby(cols_grp, as_index=False)['gole'].sum()
        elif 'sezon' in df_fil.columns:
            df_show = df_fil[df_fil['sezon'] == wyb_sezon].copy()
        else:
            df_show = df_fil

        if not df_show.empty:
            df_show = df_show.sort_values('gole', ascending=False)
            df_show = prepare_dataframe_with_flags(df_show, kraj_col)
            
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
            st.caption(f"Suma goli: {df_show['Bramki'].sum()}")
        else:
            st.warning("Brak danych.")

# =========================================================
# MODUŁ 5: KLUB 100
# =========================================================
elif opcja == "Klub 100":
    st.header("💯 Klub 100 (Najwięcej Meczów)")
    df = load_data("pilkarze.csv")
    
    if df is not None:
        target_col = next((c for c in df.columns if any(k in c for k in ['suma', 'mecze', 'występy', 'spotkania'])), None)
        nat_col = next((c for c in df.columns if c in ['narodowość', 'kraj']), None)
        
        if target_col:
            df[target_col] = pd.to_numeric(
                df[target_col].astype(str).str.replace(" ", ""), 
                errors='coerce'
            ).fillna(0).astype(int)
            
            df_100 = df[df[target_col] >= 100].copy()
            
            if not df_100.empty:
                df_100 = df_100.sort_values(by=target_col, ascending=False)

                st.subheader(f"Członkowie Klubu 100 (Razem: {len(df_100)})")
                top_chart = df_100.head(30)
                st.bar_chart(top_chart.set_index('imię i nazwisko')[target_col])
                
                if nat_col:
                    df_100 = prepare_dataframe_with_flags(df_100, nat_col)
                
                df_100 = df_100.rename(columns={'imię i nazwisko': 'Zawodnik', target_col: 'Mecze'})
                df_100.index = range(1, len(df_100) + 1)
                
                st.dataframe(
                    df_100,
                    use_container_width=True,
                    column_config={
                        "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                        "Mecze": st.column_config.NumberColumn("Mecze", format="%d")
                    }
                )
            else:
                st.info("Brak zawodników z 100+ meczami w bazie.")
        else:
            st.error("W pliku 'pilkarze.csv' nie znaleziono kolumny 'suma' lub 'mecze'.")
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
# MODUŁ 7: RYWALE
# =========================================================
elif opcja == "Rywale (H2H)":
    st.header("⚔️ Bilans z Rywalami")
    df = load_data("rywale.csv")
    if df is not None and not df.empty:
        rywal_col = df.columns[0]
        rywale = sorted(df[rywal_col].astype(str).unique())
        wybrany = st.selectbox("Wybierz rywala:", rywale)
        
        stat = df[df[rywal_col] == wybrany]
        st.dataframe(stat, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Wszyscy rywale")
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Mecze": st.column_config.NumberColumn(format="%d"),
                "Wygrane": st.column_config.NumberColumn(format="%d"),
                "Remisy": st.column_config.NumberColumn(format="%d"),
                "Porażki": st.column_config.NumberColumn(format="%d"),
                "Punkty": st.column_config.NumberColumn(format="%d"),
                "Punkty na mecz": st.column_config.NumberColumn(format="%.2f")
            }
        )

# =========================================================
# MODUŁ 8: TRENERZY (Z ULEPSZONYM ROZPOZNAWANIEM DAT)
# =========================================================
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP - Historia i Statystyki")
    df = load_data("trenerzy.csv")
    
    if df is not None:
        # --- 1. PRZETWARZANIE DAT TRENERÓW ---
        # Funkcja pomocnicza do bezpiecznej konwersji daty
        def smart_date_parse(series):
            # Próba 1: dd.mm.yyyy (najczęstszy w Polsce)
            dates = pd.to_datetime(series, format='%d.%m.%Y', errors='coerce')
            # Próba 2: jeśli się nie udało (dużo NaT), spróbuj automatu
            if dates.isna().mean() > 0.3: # Jeśli ponad 30% błędów
                dates = pd.to_datetime(series, dayfirst=True, errors='coerce')
            return dates

        if 'początek' in df.columns: 
            df['początek_dt'] = smart_date_parse(df['początek'])
        if 'koniec' in df.columns: 
            df['koniec_dt'] = smart_date_parse(df['koniec'])
            # Uzupełniamy brakujące daty końca dzisiejszą datą (dla obecnego trenera)
            df['koniec_dt'] = df['koniec_dt'].fillna(pd.Timestamp.today())

        # --- 2. DODANIE FLAG ---
        df = prepare_dataframe_with_flags(df, 'narodowość')

        # --- 3. KONWERSJA LICZB ---
        int_cols = ['wiek', 'suma dni', 'mecze', 'wygrane', 'remisy', 'przegrane', 'punkty']
        for c in int_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)

        # --- TABS ---
        tab1, tab2, tab3 = st.tabs(["📋 Lista Chronologiczna", "📊 Rankingi", "📈 Oś Czasu / Analiza"])

        # TAB 1: LISTA
        with tab1:
            df_view = df.sort_values('początek_dt', ascending=False)
            cols = ['funkcja', 'imię i nazwisko', 'Narodowość', 'Flaga', 'wiek', 'początek', 'koniec', 'mecze', 'punkty', 'śr. pkt /mecz']
            cols = [c for c in cols if c in df_view.columns]
            
            st.dataframe(
                df_view[cols], 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                    "śr. pkt /mecz": st.column_config.NumberColumn(format="%.2f"),
                    "wiek": st.column_config.NumberColumn(format="%d lat"),
                    "mecze": st.column_config.NumberColumn(format="%d"),
                    "punkty": st.column_config.NumberColumn(format="%d")
                }
            )

        # TAB 2: RANKINGI
        with tab2:
            st.subheader("🏆 Podsumowanie Trenerów")
            grp_cols = ['imię i nazwisko', 'Narodowość', 'Flaga']
            grp_cols = [c for c in grp_cols if c in df.columns]
            
            # Grupowanie
            df_agg = df.groupby(grp_cols, as_index=False)[['mecze', 'wygrane', 'remisy', 'przegrane', 'punkty']].sum()
            # Obliczenie średniej na nowo
            df_agg['śr. pkt /mecz'] = df_agg.apply(lambda x: x['punkty']/x['mecze'] if x['mecze']>0 else 0, axis=1)
            
            df_agg = df_agg.sort_values('punkty', ascending=False).reset_index(drop=True)
            df_agg.index += 1
            
            st.dataframe(
                df_agg, 
                use_container_width=True,
                column_config={
                    "Flaga": st.column_config.ImageColumn("Flaga", width="small"),
                    "śr. pkt /mecz": st.column_config.NumberColumn(format="%.2f"),
                    "mecze": st.column_config.ProgressColumn("Mecze", format="%d", min_value=0, max_value=int(df_agg['mecze'].max())),
                    "punkty": st.column_config.ProgressColumn("Punkty", format="%d", min_value=0, max_value=int(df_agg['punkty'].max()))
                }
            )

        # TAB 3: OŚ CZASU I ANALIZA MECZÓW
        with tab3:
            st.subheader("📈 Analiza Szczegółowa Kadencji")
            
            if HAS_PLOTLY:
                fig = px.scatter(
                    df.sort_values('początek_dt'),
                    x="początek_dt", y="śr. pkt /mecz",
                    size="mecze", color="śr. pkt /mecz",
                    hover_name="imię i nazwisko",
                    title="Historia formy (Wielkość kropki = Liczba meczów)",
                    color_continuous_scale="RdYlGn"
                )
                fig.update_layout(xaxis_title="Rok", yaxis_title="Średnia pkt/mecz")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Zainstaluj 'plotly' w requirements.txt")

            st.divider()
            st.subheader("🔎 Szczegóły Trenera i Lista Meczów")
            
            trenerzy_list = sorted(df['imię i nazwisko'].unique())
            wybrany_trener = st.selectbox("Wybierz trenera do analizy:", trenerzy_list)
            
            if wybrany_trener:
                coach_data = df[df['imię i nazwisko'] == wybrany_trener]
                mecze_df = load_data("mecze.csv")
                
                if mecze_df is not None:
                    # Szukamy kolumny z datą w mecze.csv
                    # Szukamy kolumn zawierających 'data', ale nie 'sort' (bo często jest data sortowania)
                    date_col = next((c for c in mecze_df.columns if 'data' in c and 'sort' not in c), None)
                    # Jeśli nie znaleziono, szukamy po prostu 'data'
                    if not date_col:
                        date_col = next((c for c in mecze_df.columns if 'data' in c), None)

                    if date_col:
                        # --- PANCERNE PARSOWANIE DATY MECZU ---
                        # 1. Próbujemy standardowy format dzień-miesiąc-rok
                        mecze_df['dt'] = pd.to_datetime(mecze_df[date_col], dayfirst=True, errors='coerce')
                        
                        # 2. Jeśli ponad połowa dat jest pusta (błąd), próbujemy format rok-miesiąc-dzień
                        if mecze_df['dt'].isna().mean() > 0.5:
                             mecze_df['dt'] = pd.to_datetime(mecze_df[date_col], errors='coerce')
                        
                        # 3. Usuwamy mecze, gdzie data jest nadal nieznana
                        mecze_df = mecze_df.dropna(subset=['dt'])
                        
                        # --- FILTROWANIE MECZÓW TRENERA ---
                        # Tworzymy maskę (filtr) o długości tabeli meczów, początkowo same fałsze
                        mask = pd.Series([False] * len(mecze_df))
                        mask.index = mecze_df.index # Ważne: synchronizacja indeksów
                        
                        for _, row in coach_data.iterrows():
                            start = row['początek_dt']
                            end = row['koniec_dt']
                            if pd.notnull(start) and pd.notnull(end):
                                # Dodajemy do maski mecze z tego okresu
                                current_period_mask = (mecze_df['dt'] >= start) & (mecze_df['dt'] <= end)
                                mask = mask | current_period_mask
                        
                        coach_matches = mecze_df[mask].copy()
                        
                        if not coach_matches.empty:
                            coach_matches = coach_matches.sort_values('dt')
                            
                            # Wykres liniowy punktów
                            pts_history = []
                            acc_pts = 0
                            for _, m in coach_matches.iterrows():
                                res = parse_result(m['wynik'])
                                pts = 0
                                if res:
                                    if res[0] > res[1]: pts = 3
                                    elif res[0] == res[1]: pts = 1
                                acc_pts += pts
                                pts_history.append(acc_pts)
                            
                            if HAS_PLOTLY:
                                fig_line = px.line(
                                    x=coach_matches['dt'], y=pts_history, markers=True,
                                    title=f"Progres punktowy: {wybrany_trener}",
                                    labels={'x': 'Data', 'y': 'Suma punktów'}
                                )
                                st.plotly_chart(fig_line, use_container_width=True)
                            
                            # Tabela
                            st.write(f"Znaleziono {len(coach_matches)} meczów:")
                            cols_view = [c for c in coach_matches.columns if c not in ['dt', 'data sortowania']]
                            st.dataframe(
                                coach_matches[cols_view].style.map(color_results_logic, subset=['wynik']),
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.warning(f"Brak meczów w bazie dla trenera {wybrany_trener} w zdefiniowanych datach.")
                            st.write(f"Sprawdzane okresy: {coach_data[['początek', 'koniec']].values}")
                    else:
                        st.error("W pliku mecze.csv nie znaleziono kolumny z datą (szukałem: 'data', 'data meczu').")
    else:
        st.error("Brak pliku: trenerzy.csv")
# =========================================================
# POZOSTAŁE MODUŁY
# =========================================================
elif opcja == "Transfery":
    st.header("💸 Historia Transferów")
    df = load_data("transfery.csv")
    df = prepare_dataframe_with_flags(df, 'kraj' if df is not None and 'kraj' in df.columns else 'narodowość')
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})

elif opcja == "Statystyki Wyników":
    st.header("🎲 Najczęstsze wyniki")
    df = load_data("wyniki.csv")
    if df is not None:
        if 'wynik' in df.columns: st.bar_chart(df.set_index('wynik')['częstotliwość'])
        st.dataframe(df, use_container_width=True, hide_index=True)

elif opcja == "Młoda Ekstraklasa":
    st.header("🎓 Młoda Ekstraklasa")
    df = load_data("me.csv")
    df = prepare_dataframe_with_flags(df, 'kraj' if df is not None and 'kraj' in df.columns else 'narodowość')
    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Flaga": st.column_config.ImageColumn("Flaga", width="small")})


