elif opcja == "Kalendarz":
    st.header("📅 Kalendarz Klubowy")
    
    # 1. Ustalanie daty (Prawdziwa vs Symulowana)
    if st.session_state.get('simulated_today'):
        today = st.session_state['simulated_today']
        st.warning(f"⚠️ TRYB SYMULACJI: Wyświetlasz kalendarz dla dnia: {today.strftime('%d.%m.%Y')}")
    else:
        today = datetime.date.today()
    
    # 2. Ładowanie danych
    df_m = load_data("mecze.csv")
    df_p = load_data("pilkarze.csv")
    df_curr = load_data("25_26.csv")
    
    # --- [NOWOŚĆ] LOGIKA DNIA MECZOWEGO ---
    match_today_alert = None
    if df_m is not None:
        # Szukamy kolumny z datą
        col_date_m = next((c for c in df_m.columns if 'data' in c and 'sort' not in c), None)
        if col_date_m:
            # Konwersja na obiekty date
            df_m['date_temp'] = pd.to_datetime(df_m[col_date_m], dayfirst=True, errors='coerce').dt.date
            
            # Sprawdzamy czy w "today" jest jakiś mecz
            todays_match = df_m[df_m['date_temp'] == today]
            
            if not todays_match.empty:
                m_row = todays_match.iloc[0]
                rival = m_row.get('rywal', 'Nieznany Rywal')
                
                # Sprawdzenie czy dom/wyjazd
                is_home = False
                if 'dom' in m_row:
                     is_home = str(m_row['dom']).lower() in ['1', 'true', 'tak', 'dom']
                
                place_icon = "🏠 u siebie" if is_home else "🚌 wyjazd"
                match_today_alert = f"⚔️ {rival} ({place_icon})"

    # Wyświetlenie Banera "Dzień Meczowy"
    if match_today_alert:
        st.markdown(f"""
        <div style="background-color: #d4edda; border: 2px solid #28a745; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: #155724; margin:0;">⚽ DZIEŃ MECZOWY! ⚽</h2>
            <h3 style="color: #155724; margin:5px 0;">TSP vs {match_today_alert}</h3>
            <p style="margin:0;">Powodzenia Panowie!</p>
        </div>
        """, unsafe_allow_html=True)
        st.balloons() # Opcjonalnie: baloniki na start

    # --- KONIEC NOWOŚCI, DALEJ STARY KOD ---

    # Listy pomocnicze
    current_squad_names = []
    # ... (reszta Twojego kodu bez zmian) ...
