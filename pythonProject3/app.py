import streamlit as st
import pandas as pd
import os

# Konfiguracja strony
st.set_page_config(page_title="TSP Baza Danych", layout="wide")
st.title("⚽ Baza Danych TSP - Przeglądarka")


# Funkcja do ładowania danych
@st.cache_data
def load_data(filename):
    try:
        # Próba wczytania z różnymi kodowaniami, ponieważ polskie znaki bywają problematyczne
        return pd.read_csv(filename, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            return pd.read_csv(filename, encoding='windows-1250')
        except:
            return pd.read_csv(filename, encoding='latin-1')
    except FileNotFoundError:
        return None


# Sidebar - Menu nawigacji
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Wybierz moduł:",
                         ["Wyszukiwarka Piłkarzy", "Historia Meczów", "Najlepsi Strzelcy", "Trenerzy"])

# --- MODUŁ 1: WYSZUKIWARKA PIŁKARZY ---
if opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Wyszukiwarka Piłkarzy")
    df_players = load_data("TSP_Baza.xlsx - Piłkarze.csv")

    if df_players is not None:
        # Czyszczenie nazw kolumn (usuwanie spacji)
        df_players.columns = df_players.columns.str.strip()

        search_query = st.text_input("Wpisz nazwisko piłkarza:")

        if search_query:
            # Filtrowanie (case insensitive)
            results = df_players[
                df_players['imię i nazwisko'].astype(str).str.contains(search_query, case=False, na=False)]

            if not results.empty:
                st.success(f"Znaleziono {len(results)} wyników:")
                # Wyświetlamy tylko najciekawsze kolumny
                cols_to_show = ['imię i nazwisko', 'pozycja', 'data urodzenia', 'Wiek', 'SUMA']
                # Sprawdźmy czy kolumny istnieją w pliku
                available_cols = [c for c in cols_to_show if c in results.columns]
                st.dataframe(results[available_cols], use_container_width=True)
            else:
                st.warning("Nie znaleziono piłkarza.")
        else:
            st.info("Wpisz nazwisko powyżej, aby wyszukać.")
            st.dataframe(df_players.head(10))  # Pokazujemy pierwszych 10 jako podgląd
    else:
        st.error("Brak pliku: TSP_Baza.xlsx - Piłkarze.csv")

# --- MODUŁ 2: HISTORIA MECZÓW ---
elif opcja == "Historia Meczów":
    st.header("🏟️ Historia Meczów")
    df_matches = load_data("TSP_Baza.xlsx - Mecze.csv")

    if df_matches is not None:
        df_matches.columns = df_matches.columns.str.strip()

        # Filtrowanie po sezonie - POPRAWKA
        # 1. Usuwamy puste wiersze w kolumnie sezon
        # 2. Zamieniamy wszystko na tekst (str), żeby uniknąć błędów sortowania
        df_matches = df_matches.dropna(subset=['sezon'])
        sezony = df_matches['sezon'].astype(str).unique()

        # Teraz sortowanie zadziała bezpiecznie
        wybrany_sezon = st.selectbox("Wybierz sezon:", sorted(sezony, reverse=True))

        matches_filtered = df_matches[df_matches['sezon'] == wybrany_sezon]

        st.subheader(f"Mecze w sezonie {wybrany_sezon}")

        # Wyświetlanie w ładniejszej tabeli
        cols_match = ['data meczu', 'rywal', 'wynik', 'strzelcy', 'miejsce rozgrywania']
        available_cols = [c for c in cols_match if c in matches_filtered.columns]

        st.dataframe(matches_filtered[available_cols], use_container_width=True, hide_index=True)

        # Statystyki sezonu
        st.metric("Liczba meczów", len(matches_filtered))
    else:
        st.error("Brak pliku: TSP_Baza.xlsx - Mecze.csv")

# --- MODUŁ 3: NAJLEPSI STRZELCY ---
elif opcja == "Najlepsi Strzelcy":
    st.header("⚽ Najlepsi Strzelcy (Top 20)")
    df_scorers = load_data("TSP_Baza.xlsx - Strzelcy.csv")

    if df_scorers is not None:
        df_scorers.columns = df_scorers.columns.str.strip()

        # Upewniamy się, że SUMA jest liczbą
        if 'SUMA' in df_scorers.columns:
            df_scorers['SUMA'] = pd.to_numeric(df_scorers['SUMA'], errors='coerce').fillna(0)

            top_scorers = df_scorers.sort_values(by='SUMA', ascending=False).head(20)

            # Wykres słupkowy
            st.bar_chart(top_scorers.set_index('imię i nazwisko')['SUMA'])

            st.subheader("Tabela wyników")
            st.dataframe(top_scorers[['imię i nazwisko', 'SUMA']], use_container_width=True)
        else:
            st.error("Brak kolumny 'SUMA' w pliku.")
    else:
        st.error("Brak pliku: TSP_Baza.xlsx - Strzelcy.csv")

# --- MODUŁ 4: TRENERZY ---
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy")
    df_coaches = load_data("TSP_Baza.xlsx - Trenerzy.csv")

    if df_coaches is not None:
        df_coaches.columns = df_coaches.columns.str.strip()
        st.dataframe(df_coaches, use_container_width=True)
    else:
        st.error("Brak pliku: TSP_Baza.xlsx - Trenerzy.csv")

st.sidebar.info("Aplikacja stworzona na bazie plików CSV TSP.")