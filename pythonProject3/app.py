import streamlit as st
import pandas as pd
import datetime

# Próba importu plotly dla osi czasu trenerów
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# --- 2. SŁOWNIK FLAG (BEZ ANGLII) ---
FLAGS_MAP = {
    'Polska': '🇵🇱', 'Hiszpania': '🇪🇸', 'Słowacja': '🇸🇰', 
    'Łotwa': '🇱🇻', 'Chorwacja': '🇭🇷', 'Kamerun': '🇨🇲', 
    'Zimbabwe': '🇿🇼', 'Finlandia': '🇫🇮', 'Gruzja': '🇬🇪', 
    'Słowenia': '🇸🇮', 'Ukraina': '🇺🇦', 'Holandia': '🇳🇱', 
    'Czechy': '🇨🇿', 'Białoruś': '🇧🇾', 'Serbia': '🇷🇸', 
    'Litwa': '🇱🇹', 'Turcja': '🇹🇷', 'Bośnia i Hercegowina': '🇧🇦',
    'Japonia': '🇯🇵', 'Senegal': '🇸🇳', 'Bułgaria': '🇧🇬',
    'Izrael': '🇮🇱', 'Nigieria': '🇳🇬', 'Grecja': '🇬🇷',
    'Francja': '🇫🇷', 'Niemcy': '🇩🇪', 'Argentyna': '🇦🇷',
    'USA': '🇺🇸', 'Kolumbia': '🇨🇴', 'Włochy': '🇮🇹', 
    'Belgia': '🇧🇪', 'Szwecja': '🇸🇪', 'Portugalia': '🇵🇹', 
    'Węgry': '🇭🇺', 'Austria': '🇦🇹'
}

# --- 3. FUNKCJE POMOCNICZE ---

@st.cache_data
def load_data(filename):
    """
    Pancerna funkcja ładująca dane.
    1. Obsługuje różne kodowania znaków.
    2. Zamienia nagłówki kolumn na małe litery i usuwa spacje.
    3. Usuwa kolumnę LP.
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
    
    # Normalizacja danych
    df = df.fillna("-")
    
    # NORMALIZACJA KOLUMN (wszystko na małe litery)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Usuwanie kolumny LP
    cols_to_drop = [c for c in df.columns if c.replace('.', '') == 'lp']
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    return df

def add_flag(kraj_raw):
    """Dodaje flagę do nazwy kraju."""
    kraj_clean = str(kraj_raw).strip()
    if kraj_clean in FLAGS_MAP:
        return f"{FLAGS_MAP[kraj_clean]} {kraj_clean}"
    for k, f in FLAGS_MAP.items():
        if k in kraj_clean:
            return f"{f} {kraj_clean}"
    return kraj_clean

def get_flag_config(df):
    """Konfiguracja kolumn obrazkowych."""
    cfg = {}
    potential_cols = ['flaga', 'flaga_url', 'kraj_url', 'flag']
    for col in potential_cols:
        if col in df.columns:
            cfg[col] = st.column_config.ImageColumn("Narodowość", width="small")
    return cfg

def show_table(dataframe, **kwargs):
    """Wyświetla tabelę z indeksem od 1."""
    if dataframe is not None and not dataframe.empty:
        df_show = dataframe.copy()
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, **kwargs)
    else:
        st.dataframe(dataframe, **kwargs)

def parse_result(val):
    """
    Analizuje wynik (np. '1-0', '2:2').
    Zwraca: (gole_tsp, gole_rywal).
    Zakłada, że TSP jest zawsze po LEWEJ stronie.
    """
    if not isinstance(val, str):
        return None
    
    # Ujednolicenie
    val = val.replace('-', ':').replace(' ', '')
    
    if ':' in val:
        try:
            parts = val.split(':')
            tsp = int(parts[0])
            opp = int(parts[1])
            return tsp, opp
        except ValueError:
            return None
    return None

def color_results_logic(val):
    """Koloruje wynik w tabeli."""
    res = parse_result(val)
    if res:
        tsp, opp = res
        if tsp > opp:
            return 'color: #28a745; font-weight: bold' # Zielony
        elif tsp < opp:
            return 'color: #dc3545; font-weight: bold' # Czerwony
        else:
            return 'color: #fd7e14; font-weight: bold' # Pomarańczowy
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

        column_config = {
            "gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
            "asysty": st.column_config.NumberColumn("Asysty", format="%d 🅰️"),
        }
        column_config.update(get_flag_config(df))
        show_table(df, use_container_width=True, column_config=column_config)

# =========================================================
# MODUŁ 2: WYSZUKIWARKA PIŁKARZY
# =========================================================
elif opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Baza Zawodników")
    df = load_data("pilkarze.csv")
    
    if df is not None:
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Wpisz nazwisko:")
        with col2:
            st.write("") 
            st.write("") 
            only_foreigners = st.checkbox("🌍 Tylko obcokrajowcy")
        
        nat_col = 'narodowość' if 'narodowość' in df.columns else 'kraj'
        
        if only_foreigners and nat_col in df.columns:
            df = df[~df[nat_col].astype(str).str.contains("Polska", case=False, na=False)]
            st.info(f"Wyświetlam tylko obcokrajowców.")

        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        show_table(df, use_container_width=True, column_config=get_flag_config(df))

# =========================================================
# MODUŁ 3: HISTORIA MECZÓW
# =========================================================
elif opcja == "Historia Meczów":
    st.header("🏟️ Archiwum Meczów")
    df = load_data("mecze.csv")
    
    if df is not None:
        if 'wynik' not in df.columns:
            st.error("Brak kolumny 'wynik' w pliku mecze.csv!")
            st.stop()

        if 'sezon' in df.columns:
            df_clean = df[df['sezon'].astype(str).str.len() > 4]
            sezony = sorted(df_clean['sezon'].unique(), reverse=True)
        else:
            sezony = []

        col1, col2 = st.columns(2)
        with col1:
            if sezony:
                wybrany_sezon = st.selectbox("Wybierz sezon:", sezony)
                matches = df[df['sezon'] == wybrany_sezon].copy()
            else:
                st.warning("Brak kolumny 'sezon'. Wyświetlam wszystko.")
                matches = df.copy()
        with col2:
            rywal_filter = st.text_input("Filtruj po rywalu:")
        
        if rywal_filter:
            matches = matches[matches.astype(str).apply(lambda x: x.str.contains(rywal_filter, case=False)).any(axis=1)]

        col_rozgrywki = None
        for c in matches.columns:
            if c in ['rozgrywki', 'liga', 'rodzaj', 'typ', 'puchar']:
                col_rozgrywki = c
                break

        if matches.empty:
            st.warning("Brak meczów.")
        else:
            datasets_to_show = []
            if col_rozgrywki:
                unikalne_rozgrywki = matches[col_rozgrywki].unique()
                tabs = st.tabs([str(r) for r in unikalne_rozgrywki])
                for tab, rozgrywka in zip(tabs, unikalne_rozgrywki):
                    subset = matches[matches[col_rozgrywki] == rozgrywka].copy()
                    datasets_to_show.append((tab, subset))
            else:
                datasets_to_show.append((st, matches))

            for container, subset in datasets_to_show:
                with container:
                    if 'data sortowania' in subset.columns:
                        subset = subset.sort_values(by='data sortowania', ascending=False)
                    elif 'data meczu' in subset.columns:
                        subset = subset.sort_values(by='data meczu', ascending=False)
                    
                    wygrane = 0
                    remisy = 0
                    porazki = 0
                    for w in subset['wynik']:
                        res = parse_result(w)
                        if res:
                            t, o = res
                            if t > o: wygrane += 1
                            elif t < o: porazki += 1
                            else: remisy += 1
                    
                    st.caption(f"📊 Bilans: ✅ {wygrane} W | ➖ {remisy} R | ❌ {porazki} P")
                    
                    subset_view = subset.drop(columns=['mecz', 'data sortowania'], errors='ignore')
                    
                    st.dataframe(
                        subset_view.style.map(color_results_logic, subset=['wynik']),
                        use_container_width=True,
                        hide_index=True
                    )

# =========================================================
# MODUŁ 4: STRZELCY (AGREGACJA)
# =========================================================
elif opcja == "⚽ Klasyfikacja Strzelców":
    st.header("⚽ Klasyfikacja Strzelców")
    df = load_data("strzelcy.csv")
    
    if df is not None:
        if 'gole' not in df.columns:
            st.error("Błąd: Brak kolumny 'gole'.")
            st.stop()

        if 'sezon' in df.columns:
            dostepne_sezony = sorted(df['sezon'].unique(), reverse=True)
            opcje_sezonu = ["Wszystkie sezony"] + list(dostepne_sezony)
        else:
            opcje_sezonu = ["Wszystkie sezony"]

        col1, col2 = st.columns([2, 1])
        with col1:
            wybrany_sezon = st.selectbox("Wybierz okres:", opcje_sezonu)
        with col2:
            st.write("") 
            st.write("") 
            pokaz_obcokrajowcow = st.checkbox("🌍 Tylko obcokrajowcy")

        df_filtered = df.copy()
        
        col_kraj = 'kraj' if 'kraj' in df.columns else 'narodowość'
        if pokaz_obcokrajowcow and col_kraj in df_filtered.columns:
            df_filtered = df_filtered[~df_filtered[col_kraj].astype(str).str.contains("Polska", case=False)]

        cols_base = ['imię i nazwisko']
        if col_kraj in df_filtered.columns:
            cols_base.append(col_kraj)

        if wybrany_sezon == "Wszystkie sezony":
            df_display = df_filtered.groupby(cols_base, as_index=False)['gole'].sum()
        elif 'sezon' in df_filtered.columns:
            df_display = df_filtered[df_filtered['sezon'] == wybrany_sezon].copy()
            df_display = df_display[cols_base + ['gole']]
        else:
            df_display = df_filtered

        if df_display.empty:
            st.warning("Brak danych.")
        else:
            df_display = df_display.sort_values(by='gole', ascending=False)
            
            if col_kraj in df_display.columns:
                df_display[col_kraj] = df_display[col_kraj].apply(add_flag)
                df_display = df_display.rename(columns={col_kraj: 'Narodowość'})
            
            df_display = df_display.rename(columns={'imię i nazwisko': 'Zawodnik', 'gole': 'Bramki'})
            df_display = df_display.reset_index(drop=True)
            df_display.index += 1
            
            st.dataframe(df_display, use_container_width=True)
            st.caption(f"Suma goli w tabeli: {df_display['Bramki'].sum()}")

# =========================================================
# MODUŁ 5: KLUB 100 (MECZE)
# =========================================================
elif opcja == "Klub 100":
    st.header("💯 Klub 100 (Najwięcej Meczów)")
    df = load_data("klub_100.csv")
    
    if df is not None:
        target_col = None
        keywords = ['mecze', 'występy', 'spotkania', 'suma']
        for col in df.columns:
            if any(k in col for k in keywords):
                target_col = col
                break
        
        if target_col:
            st.subheader("Top 30 – Rekordziści")
            df_chart = df.copy()
            df_chart[target_col] = pd.to_numeric(
                df_chart[target_col].astype(str).str.replace(" ", ""), 
                errors='coerce'
            ).fillna(0)
            
            top = df_chart.sort_values(by=target_col, ascending=False).head(30)
            st.bar_chart(top.set_index('imię i nazwisko')[target_col])
        
        show_table(df, use_container_width=True, column_config=get_flag_config(df))

# =========================================================
# MODUŁ 6: FREKWENCJA
# =========================================================
elif opcja == "Frekwencja":
    st.header("📢 Frekwencja na stadionie")
    df = load_data("frekwencja.csv")
    if df is not None:
        col_srednia = None
        for c in df.columns:
            if 'średnia' in c:
                col_srednia = c
                break
        
        if col_srednia:
            df_chart = df.copy()
            df_chart['num'] = pd.to_numeric(df_chart[col_srednia].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0)
            if 'sezon' in df.columns:
                st.line_chart(df_chart.set_index('sezon')['num'])
        
        show_table(df, use_container_width=True)

# =========================================================
# MODUŁ 7: RYWALE
# =========================================================
elif opcja == "Rywale (H2H)":
    st.header("⚔️ Bilans z Rywalami")
    df = load_data("rywale.csv")
    if df is not None:
        if not df.empty:
            rival_col = df.columns[0]
            rywale = sorted(df[rival_col].astype(str).unique())
            wybrany = st.selectbox("Wybierz rywala:", rywale)
            st.table(df[df[rival_col] == wybrany])
            st.divider()
            st.subheader("Wszyscy rywale")
            show_table(df, use_container_width=True)

# =========================================================
# MODUŁ 8: TRENERZY (NOWY)
# =========================================================
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP - Historia i Statystyki")
    df = load_data("trenerzy.csv")
    
    if df is not None:
        # Daty
        if 'początek' in df.columns:
            df['początek_dt'] = pd.to_datetime(df['początek'], format='%d.%m.%Y', errors='coerce')
        if 'koniec' in df.columns:
            df['koniec_dt'] = pd.to_datetime(df['koniec'], format='%d.%m.%Y', errors='coerce')
            df['koniec_dt'] = df['koniec_dt'].fillna(pd.Timestamp.today())

        if 'narodowość' in df.columns:
            df['narodowość'] = df['narodowość'].apply(add_flag)

        tab1, tab2, tab3 = st.tabs(["📋 Lista Chronologiczna", "📊 Rankingi", "⏳ Oś Czasu"])

        with tab1:
            df_chron = df.sort_values(by='początek_dt', ascending=False).copy()
            cols_to_show = [
                'funkcja', 'imię i nazwisko', 'narodowość', 'wiek', 
                'początek', 'koniec', 'suma dni', 
                'mecze', 'wygrane', 'remisy', 'przegrane', 
                'punkty', 'śr. pkt /mecz'
            ]
            cols_to_show = [c for c in cols_to_show if c in df_chron.columns]
            
            st.dataframe(
                df_chron[cols_to_show],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "śr. pkt /mecz": st.column_config.NumberColumn(format="%.2f"),
                    "wiek": st.column_config.NumberColumn(format="%d lat")
                }
            )

        with tab2:
            st.subheader("🏆 Podsumowanie Trenerów (Łącznie)")
            numeric_cols = ['mecze', 'wygrane', 'remisy', 'przegrane', 'punkty', 'suma dni']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df_agg = df.groupby(['imię i nazwisko', 'narodowość'], as_index=False)[numeric_cols].sum()
            df_agg['śr. pkt /mecz'] = df_agg.apply(
                lambda x: x['punkty'] / x['mecze'] if x['mecze'] > 0 else 0, axis=1
            )
            df_agg = df_agg.sort_values(by='punkty', ascending=False).reset_index(drop=True)
            df_agg.index += 1

            st.dataframe(
                df_agg,
                use_container_width=True,
                column_config={
                    "śr. pkt /mecz": st.column_config.NumberColumn(format="%.2f"),
                    "mecze": st.column_config.ProgressColumn("Mecze", format="%d", min_value=0, max_value=int(df_agg['mecze'].max())),
                    "punkty": st.column_config.ProgressColumn("Punkty", format="%d", min_value=0, max_value=int(df_agg['punkty'].max()))
                }
            )

            col_a, col_b, col_c = st.columns(3)
            top_mecze = df_agg.loc[df_agg['mecze'].idxmax()]
            top_pts = df_agg.loc[df_agg['punkty'].idxmax()]
            df_min10 = df_agg[df_agg['mecze'] >= 10]
            if not df_min10.empty:
                top_avg = df_min10.loc[df_min10['śr. pkt /mecz'].idxmax()]
            else:
                top_avg = top_pts

            with col_a:
                st.metric("Najwięcej meczów", f"{top_mecze['imię i nazwisko']}", f"{int(top_mecze['mecze'])} spotkań")
            with col_b:
                st.metric("Najwięcej punktów", f"{top_pts['imię i nazwisko']}", f"{int(top_pts['punkty'])} pkt")
            with col_c:
                st.metric("Najlepsza średnia (min. 10 spotkań)", f"{top_avg['imię i nazwisko']}", f"{top_avg['śr. pkt /mecz']:.2f}")

        with tab3:
            st.subheader("📅 Oś czasu")
            if HAS_PLOTLY:
                df_gantt = df.sort_values('początek_dt')
                fig = px.timeline(
                    df_gantt, 
                    x_start="początek_dt", 
                    x_end="koniec_dt", 
                    y="imię i nazwisko",
                    color="funkcja",
                    hover_data=["mecze", "punkty"],
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Zainstaluj bibliotekę plotly, aby zobaczyć wykres.")

# =========================================================
# MODUŁ 9: TRANSFERY
# =========================================================
elif opcja == "Transfery":
    st.header("💸 Historia Transferów")
    df = load_data("transfery.csv")
    show_table(df, use_container_width=True, column_config=get_flag_config(df or pd.DataFrame()))

# =========================================================
# MODUŁ 10: WYNIKI
# =========================================================
elif opcja == "Statystyki Wyników":
    st.header("🎲 Najczęstsze wyniki meczów")
    df = load_data("wyniki.csv")
    if df is not None:
        if 'wynik' in df.columns and 'częstotliwość' in df.columns:
            st.bar_chart(df.set_index('wynik')['częstotliwość'])
        show_table(df, use_container_width=True)

# =========================================================
# MODUŁ 11: MŁODA EKSTRAKLASA
# =========================================================
elif opcja == "Młoda Ekstraklasa":
    st.header("🎓 Młoda Ekstraklasa")
    df = load_data("me.csv")
    show_table(df, use_container_width=True, column_config=get_flag_config(df or pd.DataFrame()))
