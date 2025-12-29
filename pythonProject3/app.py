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
            return pd.read_csv(filename, encoding='latin-1')
    except FileNotFoundError:
        return None


# Sidebar - Menu nawigacji
st.sidebar.header("Nawigacja")
opcja = st.sidebar.radio("Wybierz moduł:",
                         ["Wyszukiwarka Piłkarzy", "Obcokrajowcy (Flagi)", "Historia Meczów", "Klub 100 (Strzelcy)"])

# --- MODUŁ 1: WYSZUKIWARKA PIŁKARZY ---
if opcja == "Wyszukiwarka Piłkarzy":
    st.header("🏃 Wyszukiwarka Piłkarzy")
    df_players = load_data("pilkarze.csv")

    if df_players is not None:
        df_players.columns = df_players.columns.str.strip()
        search_query = st.text_input("Wpisz nazwisko piłkarza:")

        if search_query:
            # Szukanie po nazwisku
            results = df_players[
                df_players['imię i nazwisko'].astype(str).str.contains(search_query, case=False, na=False)]

            if not results.empty:
                st.success(f"Znaleziono {len(results)} wyników:")

                # Konfiguracja wyświetlania (jeśli dodasz kolumnę 'flaga_url' w CSV)
                column_config = {}
                if 'flaga_url' in results.columns:
                    column_config["flaga_url"] = st.column_config.ImageColumn("Flaga", help="Narodowość")

                st.dataframe(
                    results,
                    use_container_width=True,
                    column_config=column_config
                )
            else:
                st.warning("Nie znaleziono piłkarza.")
        else:
            st.info("Wpisz nazwisko powyżej, aby wyszukać.")
            st.dataframe(df_players.head(20))
    else:
        st.error("Brak pliku: pilkarze.csv")

# --- MODUŁ 2: OBCOKRAJOWCY (Test Flag) ---
elif opcja == "Obcokrajowcy (Flagi)":
    st.header("🌍 Obcokrajowcy w TSP")
    df_foreigners = load_data("obcokrajowcy.csv")

    if df_foreigners is not None:
        df_foreigners.columns = df_foreigners.columns.str.strip()

        # Instrukcja dla Ciebie w aplikacji
        st.info(
            "💡 Aby widzieć flagi jako obrazki, dodaj w pliku 'obcokrajowcy.csv' kolumnę o nazwie 'flaga_url' i wklej tam linki (np. https://flagcdn.com/w40/sk.png).")

        column_config = {}
        # Jeśli znajdzie kolumnę flaga_url, zamieni ją na obrazek
        if 'flaga_url' in df_foreigners.columns:
            column_config["flaga_url"] = st.column_config.ImageColumn("Kraj")

        st.dataframe(
            df_foreigners,
            use_container_width=True,
            column_config=column_config
        )
    else:
        st.error("Brak pliku: obcokrajowcy.csv")

# --- MODUŁ 3: HISTORIA MECZÓW ---
elif opcja == "Historia Meczów":
    st.header("🏟️ Historia Meczów")
    df_matches = load_data("mecze.csv")

    if df_matches is not None:
        df_matches.columns = df_matches.columns.str.strip()

        # Poprawka sortowania
        df_matches = df_matches.dropna(subset=['sezon'])
        sezony = df_matches['sezon'].astype(str).unique()
        wybrany_sezon = st.selectbox("Wybierz sezon:", sorted(sezony, reverse=True))

        matches_filtered = df_matches[df_matches['sezon'] == wybrany_sezon]

        st.subheader(f"Mecze w sezonie {wybrany_sezon}")
        st.dataframe(matches_filtered, use_container_width=True, hide_index=True)
    else:
        st.error("Brak pliku: mecze.csv")

# --- MODUŁ 4: KLUB 100 (STRZELCY) ---
elif opcja == "Klub 100 (Strzelcy)":
    st.header("⚽ Klub 100 - Najlepsi Strzelcy")
    # Zmienilem na Klub_100.csv bo taki widze w plikach
    df_scorers = load_data("Klub_100.csv")

    if df_scorers is not None:
        df_scorers.columns = df_scorers.columns.str.strip()

        # Sprawdzamy czy jest kolumna SUMA (czasem Excel dodaje spacje)
        col_suma = [c for c in df_scorers.columns if "SUMA" in c.upper()]

        if col_suma:
            target_col = col_suma[0]
            df_scorers[target_col] = pd.to_numeric(df_scorers[target_col], errors='coerce').fillna(0)
            top_scorers = df_scorers.sort_values(by=target_col, ascending=False).head(20)

            st.bar_chart(top_scorers.set_index('imię i nazwisko')[target_col])
            st.dataframe(top_scorers, use_container_width=True)
        else:
            st.warning("Nie znaleziono kolumny SUMA w pliku Klub_100.csv. Wyświetlam całą tabelę:")
            st.dataframe(df_scorers)
    else:
        st.error("Brak pliku: Klub_100.csv (Może nazywa się strzelcy.csv? Sprawdź nazwę pliku).")