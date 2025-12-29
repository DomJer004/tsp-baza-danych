import streamlit as st
import pandas as pd
import altair as alt

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# --- FUNKCJA ŁADUJĄCA DANE ---
@st.cache_data
def load_data(filename):
    try:
        # Próba wczytania z różnymi kodowaniami
        return pd.read_csv(filename, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            return pd.read_csv(filename, encoding='windows-1250')
        except:
            try:
                return pd.read_csv(filename, encoding='latin-1')
            except:
                return None
    except FileNotFoundError:
        return None

# --- SIDEBAR (MENU) ---
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Wybierz moduł:", [
    "Aktualny Sezon (25/26)",
    "Wyszukiwarka Piłkarzy", 
    "Historia Meczów", 
    "Klub 100 (Strzelcy)",
    "Obcokrajowcy",
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
        df.columns = df.columns.str.strip()
        
        # Filtrowanie (proste wyszukiwanie)
        filter_text = st.text_input("Szukaj w obecnej kadrze:")
        if filter_text:
            df = df[df.astype(str).apply(lambda x: x.str.contains(filter_text, case=False)).any(axis=1)]

        # Kolorowanie kolumn (np. gole na zielono) - konfiguracja
        column_config = {
            "flaga": st.column_config.ImageColumn("Kraj"),
            "gole": st.column_config.NumberColumn("Gole", format="%d ⚽"),
            "asysty": st.column_config.NumberColumn("Asysty", format="%d 🅰️"),
            "minuty": st.column_config.ProgressColumn("Minuty", min_value=0, max_value=3000, format="%d min")
        }
        
        # Wyświetlamy tabelę
        # Sprawdzamy czy mamy kolumnę flaga_url (lub flaga), jesli nie, uzywamy standardowej
        if 'flaga_url' in df.columns:
            column_config['flaga_url'] = st.column_config.ImageColumn("Kraj")
            
        st.dataframe(df, use_container_width=True, column_config=column_config, hide_index=True)
    else:
        st.error("Brak pliku: 25_26.csv")

# =========================================================
# MODUŁ 2: WYSZUKIWARKA PIŁKARZY (pilkarze.csv)
# =========================================================
elif opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Wszyscy Piłkarze w Historii")
    df = load_data("pilkarze.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        search = st.text_input("Wpisz nazwisko piłkarza:")
        
        if search:
            results = df[df['imię i nazwisko'].astype(str).str.contains(search, case=False, na=False)]
            if not results.empty:
                st.success(f"Znaleziono: {len(results)}")
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("Brak wyników.")
        else:
            st.info("Wpisz nazwisko, aby przeszukać całą bazę.")
            st.dataframe(df.head(50), use_container_width=True) 
    else:
        st.error("Brak pliku: pilkarze.csv")

# =========================================================
# MODUŁ 3: HISTORIA MECZÓW (mecze.csv)
# =========================================================
elif opcja == "Historia Meczów":
    st.header("🏟️ Archiwum Meczów")
    df = load_data("mecze.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        # Czyszczenie kolumny sezon
        df = df.dropna(subset=['sezon'])
        sezony = df['sezon'].astype(str).unique()
        
        col1, col2 = st.columns(2)
        with col1:
            wybrany_sezon = st.selectbox("Wybierz sezon:", sorted(sezony, reverse=True))
        with col2:
            rywal_filter = st.text_input("Filtruj po rywalu (opcjonalnie):")
            
        matches = df[df['sezon'] == wybrany_sezon]
        
        if rywal_filter:
            matches = matches[matches['rywal'].astype(str).str.contains(rywal_filter, case=False, na=False)]
            
        st.dataframe(matches, use_container_width=True, hide_index=True)
    else:
        st.error("Brak pliku: mecze.csv")

# =========================================================
# MODUŁ 4: KLUB 100 (klub_100.csv)
# =========================================================
elif opcja == "Klub 100 (Strzelcy)":
    st.header("🔫 Najskuteczniejsi (Klub 100)")
    df = load_data("klub_100.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        # Szukamy kolumny z sumą goli
        col_suma = [c for c in df.columns if "SUMA" in c.upper()]
        
        if col_suma:
            target_col = col_suma[0]
            # Konwersja na liczby (usuwanie spacji itp)
            df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
            top = df.sort_values(by=target_col, ascending=False).head(30)
            
            st.bar_chart(top.set_index('imię i nazwisko')[target_col])
            st.dataframe(top, use_container_width=True)
        else:
            st.dataframe(df)
    else:
        st.error("Brak pliku: klub_100.csv")

# =========================================================
# MODUŁ 5: OBCOKRAJOWCY (obcokrajowcy.csv)
# =========================================================
elif opcja == "Obcokrajowcy":
    st.header("🌍 Obcokrajowcy")
    df = load_data("obcokrajowcy.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        
        # Opcja grupowania po kraju
        kraje = df['narodowość'].value_counts()
        
        tab1, tab2 = st.tabs(["Lista", "Statystyki krajów"])
        
        with tab1:
            st.info("💡 Dodaj kolumnę 'flaga_url' w CSV, aby widzieć flagi.")
            cfg = {}
            if 'flaga_url' in df.columns:
                cfg['flaga_url'] = st.column_config.ImageColumn("Flaga")
            st.dataframe(df, use_container_width=True, column_config=cfg)
            
        with tab2:
            st.bar_chart(kraje)
    else:
        st.error("Brak pliku: obcokrajowcy.csv")

# =========================================================
# MODUŁ 6: FREKWENCJA (frekwencja.csv)
# =========================================================
elif opcja == "Frekwencja":
    st.header("📢 Frekwencja na stadionie")
    df = load_data("frekwencja.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        
        # Czyszczenie danych (usuwanie spacji z liczb np. "3 500" -> 3500)
        def clean_number(x):
            if isinstance(x, str):
                return float(x.replace('\xa0', '').replace(' ', '').replace(',', '.'))
            return x

        if 'średnia domowa' in df.columns:
            df['średnia_num'] = df['średnia domowa'].apply(clean_number)
            
            st.line_chart(df.set_index('sezon')['średnia_num'])
            
            st.subheader("Szczegóły sezonów")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Brak kolumny 'średnia domowa' w pliku.")
            st.dataframe(df)
    else:
        st.error("Brak pliku: frekwencja.csv")

# =========================================================
# MODUŁ 7: RYWALE (rywale.csv)
# =========================================================
elif opcja == "Rywale (H2H)":
    st.header("⚔️ Bilans z Rywalami")
    df = load_data("rywale.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        # Zakładam, że pierwsza kolumna to Rywal
        rival_col = df.columns[0] 
        
        lista_rywali = sorted(df[rival_col].astype(str).unique())
        wybrany_rywal = st.selectbox("Wybierz przeciwnika:", lista_rywali)
        
        statystyki = df[df[rival_col] == wybrany_rywal]
        
        if not statystyki.empty:
            st.subheader(f"Bilans przeciwko: {wybrany_rywal}")
            st.table(statystyki)
        else:
            st.write("Brak danych.")
            
        st.divider()
        st.subheader("Wszyscy rywale")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Brak pliku: rywale.csv")

# =========================================================
# MODUŁ 8: TRENERZY (trenerzy.csv)
# =========================================================
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP")
    df = load_data("trenerzy.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Brak pliku: trenerzy.csv")

# =========================================================
# MODUŁ 9: TRANSFERY (transfery.csv)
# =========================================================
elif opcja == "Transfery":
    st.header("💸 Historia Transferów")
    df = load_data("transfery.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Brak pliku: transfery.csv")

# =========================================================
# MODUŁ 10: WYNIKI (wyniki.csv)
# =========================================================
elif opcja == "Statystyki Wyników":
    st.header("🎲 Najczęstsze wyniki meczów")
    df = load_data("wyniki.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        # Zakładam kolumny: wynik, częstotliwość
        if 'wynik' in df.columns and 'częstotliwość' in df.columns:
            st.bar_chart(df.set_index('wynik')['częstotliwość'])
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Brak pliku: wyniki.csv")

# =========================================================
# MODUŁ 11: MŁODA EKSTRAKLASA (me.csv)
# =========================================================
elif opcja == "Młoda Ekstraklasa":
    st.header("🎓 Młoda Ekstraklasa (Archiwum)")
    df = load_data("me.csv")
    
    if df is not None:
        df.columns = df.columns.str.strip()
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Brak pliku: me.csv")
