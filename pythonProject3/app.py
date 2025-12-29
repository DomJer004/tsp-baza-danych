import streamlit as st
import pandas as pd
import re

# --- 1. KONFIGURACJA STRONY (MUSI BYĆ PIERWSZA) ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# --- 2. SŁOWNIK FLAG ---
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
    'USA': '🇺🇸', 'Kolumbia': '🇨🇴', 'Anglia': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'Włochy': '🇮🇹', 'Belgia': '🇧🇪', 'Szwecja': '🇸🇪',
    'Portugalia': '🇵🇹', 'Węgry': '🇭🇺', 'Austria': '🇦🇹'
}

# --- 3. FUNKCJE POMOCNICZE ---

@st.cache_data
def load_data(filename):
    """
    Pancerna funkcja ładująca. 
    1. Próbuje różnych kodowań znaków.
    2. Zamienia nazwy kolumn na małe litery i usuwa spacje (np. "Wynik " -> "wynik").
    3. Usuwa kolumnę 'lp'.
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
    
    # NORMALIZACJA KOLUMN (kluczowy moment - wszystko na małe litery)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Usuwanie LP
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
    Zwraca: (gole_tsp, gole_rywal) lub None.
    Zakłada, że TSP jest zawsze po LEWEJ.
    """
    if not isinstance(val, str):
        return None
    
    # Zamieniamy myślnik na dwukropek dla ujednolicenia
    val = val.replace('-', ':')
    
    if ':' in val:
        try:
            parts = val.split(':')
            tsp = int(parts[0].strip())
            opp = int(parts[1].strip())
            return tsp, opp
        except ValueError:
            return None
    return None

def color_results_logic(val):
    """Funkcja kolorująca dla Pandas Styler."""
    res = parse_result(val)
    if res:
        tsp, opp = res
        if tsp > opp:
            return 'color: #28a745; font-weight: bold' # Zielony (Wygrana)
        elif tsp < opp:
            return 'color: #dc3545; font-weight: bold' # Czerwony (Porażka)
        else:
            return 'color: #fd7e14; font-weight: bold' # Pomarańczowy (Remis)
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
        
        # Filtr obcokrajowców (sprawdzamy kolumnę 'narodowość' lub 'kraj')
        nat_col = 'narodowość' if 'narodowość' in df.columns else 'kraj'
        
        if only_foreigners and nat_col in df.columns:
            df = df[~df[nat_col].astype(str).str.contains("Polska", case=False, na=False)]
            st.info(f"Wyświetlam tylko obcokrajowców.")

        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
            
        show_table(df, use_container_width=True, column_config=get_flag_config(df))

# =========================================================
# MODUŁ 3: HISTORIA MECZÓW (AUTOMATYCZNY BILANS)
# =========================================================
elif opcja == "Historia Meczów":
    st.header("🏟️ Archiwum Meczów")
    df = load_data("mecze.csv")
    
    if df is not None:
        # Diagnostyka kolumn
        if 'wynik' not in df.columns:
            st.error("Brak kolumny 'wynik' w pliku mecze.csv!")
            st.stop()

        # Przygotowanie listy sezonów
        if 'sezon' in df.columns:
            # Filtrujemy tylko sensowne sezony (dłuższe niż 4 znaki)
            df_clean = df[df['sezon'].astype(str).str.len() > 4]
            sezony = sorted(df_clean['sezon'].unique(), reverse=True)
        else:
            sezony = []

        # Filtry
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

        # Szukanie kolumny z ligą/rozgrywkami
        col_rozgrywki = None
        for c in matches.columns:
            if c in ['rozgrywki', 'liga', 'rodzaj', 'typ', 'puchar']:
                col_rozgrywki = c
                break

        if matches.empty:
            st.warning("Brak meczów.")
        else:
            # Logika wyświetlania (z podziałem na zakładki lub bez)
            datasets_to_show = [] # Lista krotek (nazwa_zakładki, dataframe)
            
            if col_rozgrywki:
                unikalne_rozgrywki = matches[col_rozgrywki].unique()
                tabs = st.tabs([str(r) for r in unikalne_rozgrywki])
                for tab, rozgrywka in zip(tabs, unikalne_rozgrywki):
                    subset = matches[matches[col_rozgrywki] == rozgrywka].copy()
                    datasets_to_show.append((tab, subset))
            else:
                # Jeśli brak kolumny rozgrywki, wyświetlamy jeden widok główny
                datasets_to_show.append((st, matches))

            # Pętla generująca widoki (tabela + bilans)
            for container, subset in datasets_to_show:
                with container:
                    # 1. Sortowanie (jeśli są kolumny techniczne)
                    if 'data sortowania' in subset.columns:
                        subset = subset.sort_values(by='data sortowania', ascending=False)
                    elif 'data meczu' in subset.columns:
                        subset = subset.sort_values(by='data meczu', ascending=False)
                    
                    # 2. Obliczanie statystyk (AUTOMATYCZNIE Z WYNIKU)
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
                    
                    st.caption(f"📊 Bilans: ✅ {wygrane} Zwycięstw | ➖ {remisy} Remisów | ❌ {porazki} Porażek")
                    
                    # 3. Usuwanie kolumn technicznych przed wyświetleniem
                    subset_view = subset.drop(columns=['mecz', 'data sortowania'], errors='ignore')
                    
                    # 4. Wyświetlanie z kolorowaniem
                    st.dataframe(
                        subset_view.style.map(color_results_logic, subset=['wynik']),
                        use_container_width=True,
                        hide_index=True
                    )

# =========================================================
# MODUŁ 4: STRZELCY (DŁUGI FORMAT + SUMOWANIE)
# =========================================================
elif opcja == "⚽ Klasyfikacja Strzelców":
    st.header("⚽ Klasyfikacja Strzelców")
    df = load_data("strzelcy.csv")
    
    if df is not None:
        if 'gole' not in df.columns:
            st.error("Błąd: Brak kolumny 'gole' w pliku.")
            st.stop()

        # Filtry
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

        # Filtr obcokrajowców
        col_kraj = 'kraj' if 'kraj' in df.columns else 'narodowość'
        if pokaz_obcokrajowcow and col_kraj in df_filtered.columns:
            df_filtered = df_filtered[~df_filtered[col_kraj].astype(str).str.contains("Polska", case=False)]

        # Agregacja / Wybór sezonu
        cols_base = ['imię i nazwisko']
        if col_kraj in df_filtered.columns:
            cols_base.append(col_kraj)

        if wybrany_sezon == "Wszystkie sezony":
            # Sumujemy gole
            df_display = df_filtered.groupby(cols_base, as_index=False)['gole'].sum()
        elif 'sezon' in df_filtered.columns:
            df_display = df_filtered[df_filtered['sezon'] == wybrany_sezon].copy()
            df_display = df_display[cols_base + ['gole']]
        else:
            df_display = df_filtered

        # Wyświetlanie
        if df_display.empty:
            st.warning("Brak danych.")
        else:
            df_display = df_display.sort_values(by='gole', ascending=False)
            
            # Flagi
            if col_kraj in df_display.columns:
                df_display[col_kraj] = df_display[col_kraj].apply(add_flag)
                df_display = df_display.rename(columns={col_kraj: 'Narodowość'})
            
            df_display = df_display.rename(columns={'imię i nazwisko': 'Zawodnik', 'gole': 'Bramki'})
            
            # Reset indeksu (ranking 1, 2, 3)
            df_display = df_display.reset_index(drop=True)
            df_display.index += 1
            
            st.dataframe(df_display, use_container_width=True)
            st.caption(f"Suma goli w tabeli: {df_display['Bramki'].sum()}")

# =========================================================
# MODUŁ 5: KLUB 100 (LICZBA MECZÓW)
# =========================================================
elif opcja == "Klub 100":
    st.header("💯 Klub 100 (Najwięcej Meczów)")
    df = load_data("klub_100.csv")
    
    if df is not None:
        # Szukanie kolumny z meczami
        target_col = None
        keywords = ['mecze', 'występy', 'spotkania', 'suma']
        for col in df.columns:
            if any(k in col for k in keywords):
                target_col = col
                break
        
        if target_col:
            st.subheader("Top 30 – Rekordziści")
            df_chart = df.copy()
            # Czyszczenie danych liczbowych
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
        # Wykres, jeśli jest średnia
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
# MODUŁ 8: TRENERZY
# =========================================================
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy TSP")
    df = load_data("trenerzy.csv")
    show_table(df, use_container_width=True, column_config=get_flag_config(df or pd.DataFrame()))

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



