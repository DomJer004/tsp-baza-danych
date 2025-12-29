import streamlit as st
import pandas as pd
import datetime

# Próba importu plotly dla osi czasu
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# --- 2. SŁOWNIK FLAG (BEZ ANGLII, ZGODNIE Z ŻYCZENIEM) ---
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
    'Węgry': '🇭🇺', 'Austria': '🇦🇹', 'Brazylia': '🇧🇷'
}

# --- 3. FUNKCJE POMOCNICZE ---

@st.cache_data
def load_data(filename):
    """
    Pancerna funkcja ładująca dane.
    Ignoruje wielkość liter w nagłówkach i usuwa kolumnę LP.
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
    
    # NORMALIZACJA KOLUMN (wszystko na małe litery, usuwamy spacje)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Usuwanie kolumny LP
    cols_to_drop = [c for c in df.columns if c.replace('.', '') == 'lp']
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    return df

def add_flag(kraj_raw):
    """
    Dodaje flagę emoji do nazwy kraju.
    Np. "Polska" -> "🇵🇱 Polska"
    "Słowacja /Niemcy" -> "🇸🇰 Słowacja /Niemcy"
    """
    kraj_clean = str(kraj_raw).strip()
    
    # 1. Dokładne dopasowanie
    if kraj_clean in FLAGS_MAP:
        return f"{FLAGS_MAP[kraj_clean]} {kraj_clean}"
    
    # 2. Częściowe (dla podwójnych obywatelstw)
    for k, f in FLAGS_MAP.items():
        if k in kraj_clean:
            return f"{f} {kraj_clean}"
            
    return kraj_clean

def get_flag_config(df):
    """Konfiguracja kolumn obrazkowych (dla URLi, tutaj nieużywana dla emoji)."""
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
    """Analizuje wynik (np. '1-0', '2:2') -> (gole_tsp, gole_rywal)."""
    if not isinstance(val, str):
        return None
    val = val.replace('-', ':').replace(' ', '')
    if ':' in val:
        try:
            parts = val.split(':')
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None
    return None

def color_results_logic(val):
    """Koloruje wynik w tabeli."""
    res = parse_result(val)
    if res:
        tsp, opp = res
        if tsp > opp: return 'color: #28a745; font-weight: bold' # Zielony
        elif tsp < opp: return 'color: #dc3545; font-weight: bold' # Czerwony
        else: return 'color: #fd7e14; font-weight: bold' # Pomarańczowy
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
            st.error("Brak kolumny 'wynik'!")
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
                matches = df.copy()
        with col2:
            rywal_filter = st.text_input("Filtruj po rywalu:")
        
        if rywal_filter:
            matches = matches[matches.astype(str).apply(lambda x: x.str.contains(rywal_filter, case=False)).any(axis=1)]

        col_rozgrywki = next((c for c in matches.columns if c in ['rozgrywki', 'liga', 'rodzaj', 'typ']), None)

        if matches.empty:
            st.warning("Brak meczów.")
        else:
            datasets = []
            if col_rozgrywki:
                tabs = st.tabs([str(r) for r in matches[col_rozgrywki].unique()])
                for tab, r in zip(tabs, matches[col_rozgrywki].unique()):
                    datasets.append((tab, matches[matches[col_rozgrywki] == r].copy()))
            else:
                datasets.append((st, matches))

            for container, subset in datasets:
                with container:
                    if 'data sortowania' in subset.columns:
                        subset = subset.sort_values('data sortowania', ascending=False)
                    elif 'data meczu' in subset.columns:
                        subset = subset.sort_values('data meczu', ascending=False)
                    
                    # Bilans
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
        if 'gole' not in df.columns:
            st.error("Błąd: Brak kolumny 'gole'.")
            st.stop()

        sezony = ["Wszystkie sezony"] + list(sorted(df['sezon'].unique(), reverse=True)) if 'sezon' in df.columns else ["Wszystkie sezony"]
        
        col1, col2 = st.columns([2, 1])
        wybrany_sezon = col1.selectbox("Wybierz okres:", sezony)
        pokaz_obcokrajowcow = col2.checkbox("🌍 Tylko obcokrajowcy")

        df_fil = df.copy()
        col_kraj = 'kraj' if 'kraj' in df_fil.columns else 'narodowość'
        
        if pokaz_obcokrajowcow and col_kraj in df_fil.columns:
            df_fil = df_fil[~df_fil[col_kraj].astype(str).str.contains("Polska", case=False)]

        cols_grp = ['imię i nazwisko'] + ([col_kraj] if col_kraj in df_fil.columns else [])
        
        if wybrany_sezon == "Wszystkie sezony":
            df_show = df_fil.groupby(cols_grp, as_index=False)['gole'].sum()
        elif 'sezon' in df_fil.columns:
            df_show = df_fil[df_fil['sezon'] == wybrany_sezon][cols_grp + ['gole']].copy()
        else:
            df_show = df_fil

        if not df_show.empty:
            df_show = df_show.sort_values('gole', ascending=False)
            if col_kraj in df_show.columns:
                df_show[col_kraj] = df_show[col_kraj].apply(add_flag)
                df_show = df_show.rename(columns={col_kraj: 'Narodowość'})
            
            df_show = df_show.rename(columns={'imię i nazwisko': 'Zawodnik', 'gole': 'Bramki'})
            df_show.index = range(1, len(df_show) + 1)
            st.dataframe(df_show, use_container_width=True)
            st.caption(f"Suma goli: {df_show['Bramki'].sum()}")
        else:
            st.warning("Brak danych.")

# =========================================================
# MODUŁ 5: KLUB 100
# =========================================================
elif opcja == "Klub 100":
    st.header("💯 Klub 100 (Najwięcej Meczów)")
    df = load_data("klub_100.csv")
    if df is not None:
        target_col = next((c for c in df.columns if any(k in c for k in ['mecze', 'występy', 'suma'])), None)
        
        if target_col:
            st.subheader("Top 30 – Rekordziści")
            df_chart = df.copy()
            df_chart[target_col] = pd.to_numeric(df_chart[target_col].astype(str).str.replace(" ", ""), errors='coerce').fillna(0)
            st.bar_chart(df_chart.sort_values(target_col, ascending=False).head(30).set_index('imię i nazwisko')[target_col])
        
        show_table(df, use_container_width=True, column_config=get_flag_config(df))

# =========================================================
# MODUŁ 6: FREKWENCJA
# =========================================================
elif opcja == "Frekwencja":
    st.header("📢 Frekwencja na stadionie")
    df = load_data("frekwencja.csv")
    if df is not None:
        col_avg = next((c for c in df.columns if 'średnia' in c), None)
        if col_avg and 'sezon' in df.columns:
            df_c = df.copy()
            df_c['num'] = pd.to_numeric(df_c[col_avg].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0)
            st.line_chart(df_c.set_index('sezon')['num'])
        show_table(df, use_container_width=True)

# =========================================================
# MODUŁ 7: RYWALE
# =========================================================
elif opcja == "Rywale (H2H)":
    st.header("⚔️ Bilans z Rywalami")
    df = load_data("rywale.csv")
    if df is not None and not df.empty:
        rival_col = df.columns[0]
        wybrany = st.selectbox("Wybierz rywala:", sorted(df[rival_col].astype(str).unique()))
        st.table(df[df[rival_col] == wybrany])
        st.divider()
        st.subheader("Wszyscy rywale")
        show_table(df, use_container_width=True)

# =========================================================
# MODUŁ 8: TRENERZY (NOWY - LINIOWA OŚ CZASU)
# =========================================================
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP - Historia i Statystyki")
    df = load_data("trenerzy.csv")
    
    if df is not None:
        # 1. Parsowanie dat i liczb
        if 'początek' in df.columns:
            df['początek_dt'] = pd.to_datetime(df['początek'], format='%d.%m.%Y', errors='coerce')
        if 'koniec' in df.columns:
            df['koniec_dt'] = pd.to_datetime(df['koniec'], format='%d.%m.%Y', errors='coerce')
            df['koniec_dt'] = df['koniec_dt'].fillna(pd.Timestamp.today())

        # Dodanie flag
        if 'narodowość' in df.columns:
            df['narodowość'] = df['narodowość'].apply(add_flag)

        # Konwersja liczb dla pewności
        nums = ['mecze', 'wygrane', 'remisy', 'przegrane', 'punkty', 'suma dni']
        for c in nums:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        # 2. Obliczenie średniej punktów (jeśli brak w pliku lub błędna)
        if 'mecze' in df.columns and 'punkty' in df.columns:
             df['śr. pkt /mecz'] = df.apply(lambda x: x['punkty'] / x['mecze'] if x['mecze'] > 0 else 0.0, axis=1)

        # ZAKŁADKI
        tab1, tab2, tab3 = st.tabs(["📋 Lista Chronologiczna", "📊 Rankingi", "📈 Wykres Formy (Oś Czasu)"])

        # -- ZAKŁADKA 1: LISTA --
        with tab1:
            df_chron = df.sort_values(by='początek_dt', ascending=False).copy()
            cols_show = ['funkcja', 'imię i nazwisko', 'narodowość', 'wiek', 'początek', 'koniec', 'mecze', 'punkty', 'śr. pkt /mecz']
            cols_show = [c for c in cols_show if c in df_chron.columns]
            
            st.dataframe(
                df_chron[cols_show],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "śr. pkt /mecz": st.column_config.NumberColumn(format="%.2f"),
                    "wiek": st.column_config.NumberColumn(format="%d lat")
                }
            )

        # -- ZAKŁADKA 2: RANKINGI ZBIORCZE --
        with tab2:
            st.subheader("🏆 Podsumowanie Trenerów (Łącznie)")
            
            # Grupowanie (sumujemy kadencje tego samego trenera)
            df_agg = df.groupby(['imię i nazwisko', 'narodowość'], as_index=False)[nums].sum()
            # Przeliczenie średniej ważonej
            df_agg['śr. pkt /mecz'] = df_agg.apply(lambda x: x['punkty']/x['mecze'] if x['mecze']>0 else 0, axis=1)
            
            # Sortowanie i indeks
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
            
            # Statystyki Top 3
            if not df_agg.empty:
                c1, c2, c3 = st.columns(3)
                top_m = df_agg.loc[df_agg['mecze'].idxmax()]
                top_p = df_agg.loc[df_agg['punkty'].idxmax()]
                # Średnia dla trenerów z min 10 meczami
                df_10 = df_agg[df_agg['mecze'] >= 10]
                top_a = df_10.loc[df_10['śr. pkt /mecz'].idxmax()] if not df_10.empty else top_p
                
                c1.metric("Najwięcej meczów", f"{top_m['imię i nazwisko']}", f"{int(top_m['mecze'])}")
                c2.metric("Najwięcej punktów", f"{top_p['imię i nazwisko']}", f"{int(top_p['punkty'])}")
                c3.metric("Najlepsza średnia (min. 10 spotkań)", f"{top_a['imię i nazwisko']}", f"{top_a['śr. pkt /mecz']:.2f}")

        # -- ZAKŁADKA 3: NOWA OŚ CZASU (Wykres Scatter) --
        with tab3:
            st.subheader("📈 Historia efektywności trenerów")
            st.caption("Oś pozioma to czas. Wysokość kropki to średnia punktów (jakość). Wielkość kropki to liczba meczów (staż).")
            
            if HAS_PLOTLY:
                # Sortujemy chronologicznie
                df_chart = df.sort_values('początek_dt').copy()
                
                # Tworzymy wykres
                fig = px.scatter(
                    df_chart,
                    x="początek_dt",
                    y="śr. pkt /mecz",
                    size="mecze",          # Wielkość kropki zależy od liczby meczów
                    color="śr. pkt /mecz", # Kolor zależy od punktów (gradient)
                    hover_name="imię i nazwisko",
                    hover_data=["mecze", "punkty", "początek", "koniec"],
                    text="imię i nazwisko", # Podpisujemy kropki
                    color_continuous_scale="RdYlGn", # Czerwony -> Żółty -> Zielony
                    title="Oś czasu: Kadencje i Wyniki"
                )
                
                # Dodajemy linię łączącą, żeby widać było chronologię
                fig.update_traces(mode='markers+lines+text', textposition='top center')
                
                # Ustawienia wyglądu
                fig.update_layout(
                    xaxis_title="Rok objęcia funkcji",
                    yaxis_title="Średnia pkt / mecz",
                    showlegend=False,
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Zainstaluj bibliotekę 'plotly', aby zobaczyć interaktywny wykres.")

# =========================================================
# MODUŁ 9: TRANSFERY
# =========================================================
elif opcja == "Transfery":
    st.header("💸 Historia Transferów")
    df = load_data("transfery.csv")
    safe_df = df if df is not None else pd.DataFrame()
    show_table(df, use_container_width=True, column_config=get_flag_config(safe_df))

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
    safe_df = df if df is not None else pd.DataFrame()
    show_table(df, use_container_width=True, column_config=get_flag_config(safe_df))

