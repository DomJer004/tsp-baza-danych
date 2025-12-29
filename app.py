import streamlit as st
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="TSP Baza Danych", layout="wide")
st.title("⚽ Baza Danych TSP - Przeglądarka")


# Funkcja do ładowania danych
@st.cache_data
def load_data(filename):
    try:
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


# Sidebar - Menu nawigacji
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Wybierz moduł:",
                         ["Wyszukiwarka Piłkarzy", "Historia Meczów", "Najlepsi Strzelcy", "Trenerzy"])

# --- MODUŁ 1: WYSZUKIWARKA PIŁKARZY ---
if opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Wyszukiwarka Piłkarzy")
    # ZMIANA NAZWY PLIKU TUTAJ:
    df_players = load_data("pilkarze.csv")

    if df_players is not None:
        df_players.columns = df_players.columns.str.strip()
        search_query = st.text_input("Wpisz nazwisko piłkarza:")

        if search_query:
            results = df_players[
                df_players['imię i nazwisko'].astype(str).str.contains(search_query, case=False, na=False)]
            if not results.empty:
                st.success(f"Znaleziono {len(results)} wyników:")
                cols_to_show = ['imię i nazwisko', 'pozycja', 'data urodzenia', 'Wiek', 'SUMA']
                available_cols = [c for c in cols_to_show if c in results.columns]
                st.dataframe(results[available_cols], use_container_width=True)
            else:
                st.warning("Nie znaleziono piłkarza.")
        else:
            st.info("Wpisz nazwisko powyżej, aby wyszukać.")
            st.dataframe(df_players.head(10))
    else:
        st.error("Brak pliku: pilkarze.csv. Upewnij się, że wgrałeś go na GitHub z małej litery!")

# --- MODUŁ 2: HISTORIA MECZÓW ---
elif opcja == "Historia Meczów":
    st.header("🏟️ Historia Meczów")
    # ZMIANA NAZWY PLIKU TUTAJ:
    df_matches = load_data("mecze.csv")

    if df_matches is not None:
        df_matches.columns = df_matches.columns.str.strip()

        # Poprawka sortowania sezonów
        df_matches = df_matches.dropna(subset=['sezon'])
        sezony = df_matches['sezon'].astype(str).unique()
        wybrany_sezon = st.selectbox("Wybierz sezon:", sorted(sezony, reverse=True))

        matches_filtered = df_matches[df_matches['sezon'] == wybrany_sezon]

        st.subheader(f"Mecze w sezonie {wybrany_sezon}")
        cols_match = ['data meczu', 'rywal', 'wynik', 'strzelcy', 'miejsce rozgrywania']
        available_cols = [c for c in cols_match if c in matches_filtered.columns]

        st.dataframe(matches_filtered[available_cols], use_container_width=True, hide_index=True)
        st.metric("Liczba meczów", len(matches_filtered))
    else:
        st.error("Brak pliku: mecze.csv")

# --- MODUŁ 3: NAJLEPSI STRZELCY ---
elif opcja == "Najlepsi Strzelcy":
    st.header("⚽ Najlepsi Strzelcy (Top 20)")
    # ZMIANA NAZWY PLIKU TUTAJ:
    df_scorers = load_data("strzelcy.csv")

    if df_scorers is not None:
        df_scorers.columns = df_scorers.columns.str.strip()
        if 'SUMA' in df_scorers.columns:
            df_scorers['SUMA'] = pd.to_numeric(df_scorers['SUMA'], errors='coerce').fillna(0)
            top_scorers = df_scorers.sort_values(by='SUMA', ascending=False).head(20)
            st.bar_chart(top_scorers.set_index('imię i nazwisko')['SUMA'])
            st.subheader("Tabela wyników")
            st.dataframe(top_scorers[['imię i nazwisko', 'SUMA']], use_container_width=True)
        else:
            st.error("Brak kolumny 'SUMA' w pliku.")
    else:
        st.error("Brak pliku: strzelcy.csv")

# --- MODUŁ 4: TRENERZY ---
elif opcja == "Trenerzy":
    st.header("👔 Trenerzy")
    # ZMIANA NAZWY PLIKU TUTAJ:
    df_coaches = load_data("trenerzy.csv")

    if df_coaches is not None:
        df_coaches.columns = df_coaches.columns.str.strip()
        st.dataframe(df_coaches, use_container_width=True)
    else:
        st.error("Brak pliku: trenerzy.csv")

st.sidebar.info("Aplikacja stworzona na bazie plików CSV TSP.")