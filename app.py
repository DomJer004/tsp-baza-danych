# --- TAB 5: WYNIKI (DYNAMICZNE) ---
    with tab5:
        st.subheader("🎲 Statystyki Wyników")
        
        if df_matches is not None and 'wynik' in df_matches.columns:
            # 1. Przygotowanie danych (standaryzacja usuwa spacje np. "1 : 0" -> "1:0")
            # Tworzymy kopię, żeby nie psuć głównego dataframe
            df_scores = df_matches.copy()
            df_scores['wynik_std'] = df_scores['wynik'].astype(str).str.replace(" ", "").str.strip()
            
            # Liczenie wystąpień
            score_counts = df_scores['wynik_std'].value_counts().reset_index()
            score_counts.columns = ['Wynik', 'Liczba']
            score_counts = score_counts.sort_values('Liczba', ascending=False) # Najczęstsze na górze

            # 2. Układ: Wykres po lewej, Szczegóły po prawej
            c1, c2 = st.columns([1.5, 1])
            
            with c1:
                st.markdown("#### 📊 Częstotliwość")
                if HAS_PLOTLY:
                    fig = px.bar(
                        score_counts.head(15), # Top 15 wyników
                        x='Wynik', 
                        y='Liczba', 
                        text='Liczba',
                        title="Najczęstsze wyniki (Top 15)",
                        color='Liczba',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(xaxis_title="Wynik", yaxis_title="Ilość meczów")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(score_counts.set_index('Wynik').head(15))

            with c2:
                st.markdown("#### 🔍 Sprawdź mecze")
                st.info("Wybierz wynik z listy, aby zobaczyć, kiedy padł.")
                
                # Selectbox z wynikami (format: "1:0 (54 mecze)")
                score_options = score_counts['Wynik'].tolist()
                def format_func(opt):
                    count = score_counts[score_counts['Wynik'] == opt]['Liczba'].values[0]
                    return f"{opt} ({count} x)"
                
                selected_score = st.selectbox("Wybierz wynik:", score_options, format_func=format_func)
                
                if selected_score:
                    # Filtrowanie meczów z tym wynikiem
                    matches_with_score = df_scores[df_scores['wynik_std'] == selected_score].copy()
                    
                    # Sortowanie od najnowszych
                    if 'dt_obj' in matches_with_score.columns:
                        matches_with_score = matches_with_score.sort_values('dt_obj', ascending=False)
                    
                    st.write(f"**Lista meczów z wynikiem {selected_score}:**")
                    
                    # Wybór kolumn do wyświetlenia
                    cols_show = ['Gdzie', 'data meczu', 'rywal', 'rozgrywki', 'Trener']
                    final_cols = [c for c in cols_show if c in matches_with_score.columns]
                    
                    # Wyświetlenie tabeli z kolorowaniem
                    st.dataframe(
                        matches_with_score[final_cols].style.map(color_results_logic, subset=['wynik'] if 'wynik' in final_cols else None),
                        use_container_width=True,
                        hide_index=True,
                        height=400 # Ograniczona wysokość z paskiem przewijania
                    )
        else:
            st.warning("Brak danych lub kolumny 'wynik' w pliku mecze.csv.")
