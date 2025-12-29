import streamlit as st
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="TSP Baza Danych", layout="wide", page_icon="⚽")
st.title("⚽ Baza Danych TSP - Centrum Wiedzy")

# --- FUNKCJE POMOCNICZE ---

@st.cache_data
def load_data(filename):
    """Ładuje dane z CSV, naprawia kodowanie i normalizuje nazwy kolumn."""
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
    
    # GLOBALNE CZYSZCZENIE:
    df = df.fillna("-")
    
    # --- PANCERNA NORMALIZACJA KOLUMN ---
    # 1. Usuwamy białe znaki (spacje) z początku i końca nazw kolumn
    # 2. Zamieniamy wszystko na małe litery (np. "Gole" -> "gole")
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Usuwanie kolumny "lp." (generujemy własną)
    # Teraz szukamy 'lp' lub 'lp.' w wersji małymi literami
    cols_to_drop = [c for c in df.columns if c.replace('.', '') == 'lp']
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
# MODUŁ: STRZELCY (Z DIAGNOSTYKĄ)
# =========================================================
elif opcja == "⚽ Klasyfikacja Strzelców":
    st.header("⚽ Klasyfikacja Strzelców")
    df = load_data("strzelcy.csv")
    
    if df is not None:
        # --- DIAGNOSTYKA (dla Ciebie) ---
        # Sprawdzamy, czy kluczowe kolumny istnieją po normalizacji (małymi literami)
        wymagane = ['imię i nazwisko', 'gole']
        brakujace = [col for col in wymagane if col not in df.columns]
        
        if brakujace:
            st.error(f"⚠️ BŁĄD DANYCH: W pliku brakuje kolumn: {brakujace}")
            st.write("Program widzi w Twoim pliku takie kolumny (są zamienione na małe litery):")
            st.code(list(df.columns))
            st.stop() # Zatrzymujemy działanie modułu, żeby nie sypało błędami
        
        # --- KONIEC DIAGNOSTYKI ---

        # 1. Filtry
        if 'sezon' in df.columns:
            dostepne_sezony = sorted(df['sezon'].unique(), reverse=True)
            opcje_sezonu = ["Wszystkie sezony"] + list(dostepne_sezony)
        else:
            opcje_sezonu = ["Wszystkie sezony (brak kolumny sezon)"]

        col1, col2 = st.columns([2, 1])
        with col1:
            wybrany_sezon = st.selectbox("Wybierz okres:", opcje_sezonu)
        with col2:
            st.write("") 
            st.write("") 
            pokaz_obcokrajowcow = st.checkbox("🌍 Tylko obcokrajowcy")

        # 2. Logika
        df_filtered = df.copy()

        # A. Obcokrajowcy (szukamy kolumny 'kraj' lub 'narodowość')
        col_kraj = 'kraj' if 'kraj' in df.columns else 'narodowość'
        
        if pokaz_obcokrajowcow and col_kraj in df_filtered.columns:
            df_filtered = df_filtered[~df_filtered[col_kraj].astype(str).str.contains("Polska", case=False)]

        # B. Sezon / Agregacja
        if wybrany_sezon == "Wszystkie sezony":
            # Sumujemy gole
            # Jeśli nie ma kolumny kraj, grupujemy tylko po nazwisku
            group_cols = ['imię i nazwisko']
            if col_kraj in df_filtered.columns:
                group_cols.append(col_kraj)
                
            df_display = df_filtered.groupby(group_cols, as_index=False)['gole'].sum()
        
        elif "brak kolumny sezon" not in wybrany_sezon:
            # Konkretny sezon
            df_display = df_filtered[df_filtered['sezon'] == wybrany_sezon].copy()
            # Bierzemy co jest
            cols = ['imię i nazwisko', 'gole']
            if col_kraj in df_filtered.columns:
                cols.append(col_kraj)
            df_display = df_display[cols]
        else:
            df_display = df_filtered

        # 3. Wyświetlanie
        if df_display.empty:
            st.warning("Brak zawodników (tabela jest pusta po filtrowaniu).")
        else:
            df_display = df_display.sort_values(by='gole', ascending=False)
            
            # Flagi
            if col_kraj in df_display.columns:
                df_display[col_kraj] = df_display[col_kraj].apply(add_flag)
                df_display = df_display.rename(columns={col_kraj: 'Narodowość'})
            
            df_display = df_display.rename(columns={
                'imię i nazwisko': 'Zawodnik',
                'gole': 'Bramki'
            })

            # Reset indeksu
            df_display = df_display.reset_index(drop=True)
            df_display.index += 1
            
            st.dataframe(df_display, use_container_width=True)
# =========================================================
# MODUŁ 3: HISTORIA MECZÓW (BEZ KOLUMN TECHNICZNYCH)
# =========================================================
elif opcja == "Historia Meczów":
    st.header("🏟️ Archiwum Meczów")
    df = load_data("mecze.csv")
    
    if df is not None:
        # Funkcja kolorująca (bez zmian)
        def color_results(val):
            if isinstance(val, str) and ':' in val:
                try:
                    parts = val.split(':')
                    gole_nasze = int(parts[0])
                    gole_rywala = int(parts[1])
                    
                    if gole_nasze > gole_rywala:
                        return 'color: #28a745; font-weight: bold' # Zielony
                    elif gole_nasze < gole_rywala:
                        return 'color: #dc3545; font-weight: bold' # Czerwony
                    else:
                        return 'color: #fd7e14; font-weight: bold' # Pomarańczowy
                except ValueError:
                    return ''
            return ''

        # Filtrowanie sezonu
        df_clean = df[df['sezon'].astype(str).str.len() > 4]
        sezony = df_clean['sezon'].unique()
        
        col1, col2 = st.columns(2)
        with col1:
            wybrany_sezon = st.selectbox("Wybierz sezon:", sorted(sezony, reverse=True))
        with col2:
            rywal_filter = st.text_input("Filtruj po rywalu:")
            
        matches = df[df['sezon'] == wybrany_sezon].copy()
        
        if rywal_filter:
            matches = matches[matches['rywal'].astype(str).str.contains(rywal_filter, case=False, na=False)]

        # Wykrywanie kolumny rozgrywki
        col_rozgrywki = None
        for c in matches.columns:
            if c.lower() in ['rozgrywki', 'liga', 'rodzaj', 'typ']:
                col_rozgrywki = c
                break
        
        if matches.empty:
            st.warning("Brak meczów spełniających kryteria.")
        else:
            if not col_rozgrywki:
                # Wersja bez podziału na ligi
                # Sortowanie przed usunięciem kolumny
                if 'data sortowania' in matches.columns:
                    matches = matches.sort_values(by='data sortowania', ascending=False)
                
                # Usuwanie kolumn z widoku
                matches_view = matches.drop(columns=['mecz', 'data sortowania'], errors='ignore')
                
                st.dataframe(matches_view.style.map(color_results, subset=['wynik']), use_container_width=True, hide_index=True)
            else:
                # Wersja z zakładkami (Ekstraklasa, Puchar itp.)
                rozgrywki_list = matches[col_rozgrywki].unique()
                tabs = st.tabs([str(r) for r in rozgrywki_list])
                
                for tab, rozgrywka in zip(tabs, rozgrywki_list):
                    with tab:
                        subset = matches[matches[col_rozgrywki] == rozgrywka].copy()
                        
                        # 1. Najpierw sortujemy (jeśli jest kolumna sortująca)
                        if 'data sortowania' in subset.columns:
                            subset = subset.sort_values(by='data sortowania', ascending=False)
                        elif 'data meczu' in subset.columns:
                            subset = subset.sort_values(by='data meczu', ascending=False)

                        # Statystyki bilansu
                        wygrane = 0
                        remisy = 0
                        porazki = 0
                        for wynik in subset['wynik']:
                            if isinstance(wynik, str) and ':' in wynik:
                                try:
                                    parts = wynik.split(':')
                                    g_nasze, g_rywala = int(parts[0]), int(parts[1])
                                    if g_nasze > g_rywala: wygrane += 1
                                    elif g_nasze < g_rywala: porazki += 1
                                    else: remisy += 1
                                except: pass
                        
                        st.caption(f"Bilans w {rozgrywka}: ✅ {wygrane} W | ➖ {remisy} R | ❌ {porazki} P")

                        # 2. Teraz usuwamy niechciane kolumny
                        subset_view = subset.drop(columns=['mecz', 'data sortowania'], errors='ignore')

                        # 3. Wyświetlamy
                        st.dataframe(subset_view.style.map(color_results, subset=['wynik']), use_container_width=True, hide_index=True)

    else:
        st.error("Brak pliku: mecze.csv")

# =========================================================
# MODUŁ: KLUB 100 (POPRAWIONY)
# =========================================================
elif opcja == "Klub 100":
    st.header("💯 Klub 100 (Najwięcej Meczów)")
    df = load_data("klub_100.csv")
    
    if df is not None:
        # Szukamy kolumny z liczbą meczów (wszystko jest już z małej litery dzięki load_data)
        target_col = None
        keywords = ['mecze', 'występy', 'spotkania', 'suma']
        
        for col in df.columns:
            if any(keyword in col for keyword in keywords):
                target_col = col
                break
        
        if target_col:
            st.success(f"Znaleziono kolumnę z danymi: '{target_col}'") # Info dla Ciebie, że działa
            st.subheader("Top 30 – Rekordziści pod względem występów")
            
            df_chart = df.copy()
            # Czyszczenie liczb
            df_chart[target_col] = pd.to_numeric(
                df_chart[target_col].astype(str).str.replace(" ", ""), 
                errors='coerce'
            ).fillna(0)
            
            top = df_chart.sort_values(by=target_col, ascending=False).head(30)
            st.bar_chart(top.set_index('imię i nazwisko')[target_col])
        else:
            st.warning("⚠️ Nie znaleziono kolumny z liczbą meczów (szukałem: mecze, występy, suma).")
            st.write("Dostępne kolumny w pliku:", list(df.columns))

        # Tabela
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
            # POPRAWKA BŁĘDU (zamknięty nawias):
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



