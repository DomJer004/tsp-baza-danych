import streamlit as st
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# --- FUNKCJA ŁADUJĄCA DANE ---
@st.cache_data
def load_data(filename):
    try:
        df = pd.read_csv(filename, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(filename, encoding='windows-1250')
        except:
            try:
                df = pd.read_csv(filename, encoding='latin-1')
            except:
                return None
    except FileNotFoundError:
        return None
    
    # GLOBALNE CZYSZCZENIE:
    # 1. Zamiana pustych pól na "-"
    df = df.fillna("-")
    
    # 2. Usuwanie spacji z nazw kolumn
    df.columns = df.columns.str.strip()
    
    # 3. Usuwanie kolumny "lp." lub "Lp." z pliku (bo generujemy własną od 1)
    cols_to_drop = [c for c in df.columns if c.lower().replace('.', '') == 'lp']
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    return df

# --- POMOCNICZA FUNKCJA DO KONFIGURACJI FLAG ---
def get_flag_config(df):
    """Tworzy konfigurację, która zamienia linki w kolumnie 'flaga' na obrazki."""
    cfg = {}
    potential_cols = ['flaga', 'flaga_url', 'kraj_url', 'flag']
    
    for col in potential_cols:
        if col in df.columns:
            cfg[col] = st.column_config.ImageColumn("Narodowość", width="small")
    return cfg

# --- POMOCNICZA FUNKCJA DO WYŚWIETLANIA (NUMERACJA OD 1) ---
def show_table(dataframe, **kwargs):
    """Wyświetla tabelę z indeksem zaczynającym się od 1."""
    if dataframe is not None and not dataframe.empty:
        # Tworzymy kopię do wyświetlania
        df_show = dataframe.copy()
        # Resetujemy indeks i ustawiamy start od 1
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, **kwargs)
    else:
        st.dataframe(dataframe, **kwargs)

# --- SIDEBAR (MENU) ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Wybierz moduł:", [
    "Aktualny Sezon (25/26)",
    "Wyszukiwarka Piłkarzy", 
    "Historia Meczów", 
    "Klub 100 (Strzelcy)",
    "Frekwencja",
    "Rywale (H2H)",
    "Trenerzy",
    "Transfery",
    "Statystyki Wyników",
    "Młoda Ekstraklasa"
])

# =========================================================
# MODUŁ 1: AKTUALNY SEZON (25_26.csv)
# =========================================================
if opcja == "Aktualny Sezon (25/26)":
    st.header("📊 Statystyki sezonu 2025/2026")
    df = load_data("25_26.csv")
    
    if df is not None:
        filter_text = st.text_input("Szukaj w obecnej kadrze:")
        if filter_text:
            df = df[df.astype(str).apply(lambda x: x.str.contains(filter_text, case=False)).any(axis=1)]

        column_config = {
            "gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
            "asysty": st.column_config.NumberColumn("Asysty", format="%d 🅰️"),
        }
        column_config.update(get_flag_config(df))
            
        show_table(df, use_container_width=True, column_config=column_config)
    else:
        st.error("Brak pliku: 25_26.csv")

# =========================================================
# MODUŁ 2: WYSZUKIWARKA PIŁKARZY (pilkarze.csv)
# =========================================================
elif opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Baza Zawodników")
    df = load_data("pilkarze.csv")
    
    if df is not None:
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Wpisz nazwisko piłkarza:")
        with col2:
            st.write("") 
            st.write("") 
            only_foreigners = st.checkbox("🌍 Pokaż tylko obcokrajowców")
        
        if only_foreigners:
            if 'narodowość' in df.columns:
                df = df[~df['narodowość'].astype(str).str.contains("Polska", case=False, na=False)]
                st.info(f"Wyświetlam tylko obcokrajowców ({len(df)} zawodników).")

        if search:
            df = df[df['imię i nazwisko'].astype(str).str.contains(search, case=False, na=False)]
            
        show_table(df, use_container_width=True, column_config=get_flag_config(df))
    else:
        st.error("Brak pliku: pilkarze.csv")

# =========================================================
# MODUŁ 3: HISTORIA MECZÓW (mecze.csv)
# =========================================================
elif opcja == "Historia Meczów":
    st.header("🏟️ Archiwum Meczów")
    df = load_data("mecze.csv")
    
    if df is not None:
        df_clean = df[df['sezon'].astype(str).str.len() > 4]
        sezony = df_clean['sezon'].unique()
        
        col1, col2 = st.columns(2)
        with col1:
            wybrany_sezon = st.selectbox("Wybierz sezon:", sorted(sezony, reverse=True))
        with col2:
            rywal_filter = st.text_input("Filtruj po rywalu:")
            
        matches = df[df['sezon'] == wybrany_sezon]
        
        if rywal_filter:
            matches = matches[matches['rywal'].astype(str).str.contains(rywal_filter, case=False, na=False)]
            
        show_table(matches, use_container_width=True) 
    else:
        st.error("Brak pliku: mecze.csv")

# =========================================================
# MODUŁ 4: KLUB 100 (klub_100.csv)
# =========================================================
elif opcja == "Klub 100 (Strzelcy)":
    st.header("🔫 Najskuteczniejsi (Klub 100)")
    df = load_data("klub_100.csv")
    
    if df is not None:
        col_suma = [c for c in df.columns if "SUMA" in c.upper()]
        
        if col_suma:
            target_col = col_suma[0]
            df_chart = df.copy()
            df_chart[target_col] = pd.to_numeric(df_chart[target_col].replace("-", 0), errors='coerce').fillna(0)
            
            top = df_chart.sort_values(by=target_col, ascending=False).head(30)
            st.bar_chart(top.set_index('imię i nazwisko')[target_col])
            
            show_table(df, use_container_width=True, column_config=get_flag_config(df))
        else:
            show_table(df, use_container_width=True, column_config=get_flag_config(df))
    else:
        st.error("Brak pliku: klub_100.csv")

# =========================================================
# MODUŁ 5: FREKWENCJA (frekwencja.csv)
# =========================================================
elif opcja == "Frekwencja":
    st.header("📢 Frekwencja na stadionie")
    df = load_data("frekwencja.csv")
    
    if df is not None:
        def clean_number(x):
            if isinstance(x, str):
                clean_str = x.replace('-', '0').replace('\xa0', '').replace(' ', '').replace(',', '.')
                try:
                    return float(clean_str)
                except:
                    return 0
            return x

        if 'średnia domowa' in df.columns:
            df_chart = df.copy()
            df_chart['średnia_num'] = df_chart['średnia domowa'].apply(clean_number)
            st.line_chart(df_chart.set_index('sezon')['średnia_num'])
            
        show_table(df, use_container_width=True)
    else:
        st.error("Brak pliku: frekwencja.csv")

# =========================================================
# MODUŁ 6: RYWALE (rywale.csv)
# =========================================================
elif opcja == "Rywale (H2H)":
    st.header("⚔️ Bilans z Rywalami")
    df = load_data("rywale.csv")
    
    if df is not None:
        rival_col = df.columns[0] 
        lista_rywali = sorted(df[rival_col].astype(str).unique())
        wybrany_rywal = st.selectbox("Wybierz przeciwnika:", lista_rywali)
        
        statystyki = df[df[rival_col] == wybrany_rywal]
        
        if not statystyki.empty:
            st.subheader(f"Bilans przeciwko: {wybrany_rywal}")
            # Tu był błąd, teraz jest poprawnie:
            st.table(statystyki)
            
        st.divider()
        st.subheader("Wszyscy rywale")
        show_table(df, use_container_width=True)
    else:
        st.error("Brak pliku: rywale.csv")

# =========================================================
# MODUŁ 7: TRENERZY (trenerzy.csv)
# =========================================================
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP")
    df = load_data("trenerzy.csv")
    
    if df is not None:
        show_table(df, use_container_width=True, column_config=get_flag_config(df))
    else:
        st.error("Brak pliku: trenerzy.csv")

# =========================================================
# MODUŁ 8: TRANSFERY (transfery.csv)
# =========================================================
elif opcja == "Transfery":
    st.header("💸 Historia Transferów")
    df = load_data("transfery.csv")
    
    if df is not None:
        show_table(df, use_container_width=True, column_config=get_flag_config(df))
    else:
        st.error("Brak pliku: transfery.csv")

# =========================================================
# MODUŁ 9: WYNIKI (wyniki.csv)
# =========================================================
elif opcja == "Statystyki Wyników":
    st.header("🎲 Najczęstsze wyniki meczów")
    df = load_data("wyniki.csv")
    
    if df is not None:
        if 'wynik' in df.columns and 'częstotliwość' in df.columns:
            st.bar_chart(df.set_index('wynik')['częstotliwość'])
        show_table(df, use_container_width=True)
    else:
        st.error("Brak pliku: wyniki.csv")

# =========================================================
# MODUŁ 10: MŁODA EKSTRAKLASA (me.csv)
# =========================================================
elif opcja == "Młoda Ekstraklasa":
    st.header("🎓 Młoda Ekstraklasa (Archiwum)")
    df = load_data("me.csv")
    
    if df is not None:
        show_table(df, use_container_width=True, column_config=get_flag_config(df))
    else:
        st.error("Brak pliku: me.csv")
