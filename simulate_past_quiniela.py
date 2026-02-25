import pandas as pd
import numpy as np
import joblib

def simulate_past_quiniela():
    print("=======================================================")
    print(" DEMOSTRACIÓN: QUINIELA PASADA (20-23 FEBRERO 2026) ")
    print("=======================================================\n")
    
    # Matches we want to simulate
    target_matches = [
        ("Ath Bilbao", "Elche"),
        ("Ath Madrid", "Espanol"),
        ("Osasuna", "Real Madrid"),
        ("Betis", "Vallecano"),
        ("Sociedad", "Oviedo"),
        ("Las Palmas", "Castellon"),
        ("Almeria", "Cordoba"),
        ("La Coruna", "Eibar"),
        ("Leganes", "Cultural Leonesa"),
        ("Huesca", "Mirandes"),
        ("Barcelona", "Levante"),
        ("Sp Gijon", "Valladolid"),
        ("Villarreal", "Valencia"),
        ("Getafe", "Sevilla"),
        ("Celta", "Mallorca") # Pleno
    ]
    
    df = pd.read_csv('LaLiga_ML_Dataset.csv')
    df['DateObj'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
    
    predictoras = [
        'Home_Rank_Pre', 'Away_Rank_Pre', 'Home_Form_L5', 'Away_Form_L5',
        'Home_Form_HomeL3', 'Away_Form_AwayL3', 'Home_Rest_Days', 'Away_Rest_Days',
        'Home_Played_Euro_Midweek', 'Away_Played_Euro_Midweek', 'H2H_Home_Pts_L3',
        'Home_xG_Understat', 'Home_xGA_Understat', 'Home_xPTS_Understat',
        'Away_xG_Understat', 'Away_xGA_Understat', 'Away_xPTS_Understat',
        'Prob_Home_Bookie', 'Prob_Draw_Bookie', 'Prob_Away_Bookie'
    ]
    
    model = joblib.load('quiniela_rf_model.pkl')
    
    resultados = []
    
    for (home, away) in target_matches:
        # Encontrar el partido exacto en el dataset
        match_row = df[(df['HomeTeam'] == home) & (df['AwayTeam'] == away)].sort_values('DateObj').tail(1)
        
        if match_row.empty:
            print(f"Error: {home} vs {away} no encontrado.")
            continue
            
        real_result_code = match_row['Target_Result'].values[0]
        real_result_str = {0: '1', 1: 'X', 2: '2'}[real_result_code]
        
        # Recalcular las cuotas implícitas
        match_row['Prob_Home_Bookie'] = 1 / match_row['AvgH']
        match_row['Prob_Draw_Bookie'] = 1 / match_row['AvgD']
        match_row['Prob_Away_Bookie'] = 1 / match_row['AvgA']
        
        X = match_row[predictoras]
        
        probs = model.predict_proba(X)[0]
        p1, pX, p2 = probs[0], probs[1], probs[2]
        
        entropia = - (p1 * np.log2(p1 + 1e-9) + pX * np.log2(pX + 1e-9) + p2 * np.log2(p2 + 1e-9))
        
        resultados.append({
            'Partido': f"{home} - {away}",
            'P1': p1, 'PX': pX, 'P2': p2,
            'Incertidumbre': entropia,
            'Real': real_result_str
        })
        
    df_res = pd.DataFrame(resultados)
    
    # Asignacion Optima para los 14 principales: 1 Triple, 2 Dobles, 11 Fijos
    df_14 = df_res.iloc[:14].copy()
    pleno = df_res.iloc[14] if len(df_res) == 15 else None
    
    df_14_sorted = df_14.sort_values(by='Incertidumbre', ascending=False)
    
    apuestas_asignadas = {}
    contador_triples, contador_dobles = 0, 0
    
    for idx, row in df_14_sorted.iterrows():
        orden_partidas = [('1', row['P1']), ('X', row['PX']), ('2', row['P2'])]
        orden_partidas.sort(key=lambda x: x[1], reverse=True)
        
        if contador_triples < 1:
            apuesta, tipo = "1 X 2", "Triple"
            contador_triples += 1
        elif contador_dobles < 2:
            apuesta, tipo = f"{orden_partidas[0][0]} {orden_partidas[1][0]}", "Doble"
            contador_dobles += 1
        else:
            apuesta, tipo = f"{orden_partidas[0][0]}", "Fijo"
            
        apuestas_asignadas[idx] = (apuesta, tipo)
    
    print(f"{'#':<2} {'Partido':<30} | {'Probabilidades (1 - X - 2)':<25} | {'Predicción Model':<20} | {'Resultado Real':<15} | {'Acierto?':<10}")
    print("-" * 120)
    
    aciertos_totales = 0
    for i in range(14):
        row = df_res.iloc[i]
        apuesta, tipo = apuestas_asignadas[i]
        real = row['Real']
        
        acierto = "✅ SÍ" if real in apuesta else "❌ NO"
        if real in apuesta: aciertos_totales += 1
            
        print(f"{(i+1):2d} {row['Partido']:<30} | {row['P1']*100:>5.1f}% {row['PX']*100:>5.1f}% {row['P2']*100:>5.1f}% | {apuesta:<10} ({tipo:<6}) | Real: {real:<9} | {acierto}")

    if pleno is not None:
        p_orden = [('1', pleno['P1']), ('X', pleno['PX']), ('2', pleno['P2'])]
        p_orden.sort(key=lambda x: x[1], reverse=True)
        mejor_resultado15 = p_orden[0][0]
        real_pleno = pleno['Real']
        acierto_pleno = "✅ SÍ" if real_pleno == mejor_resultado15 else "❌ NO"
        print("-" * 120)
        print(f"15 {pleno['Partido']:<30} | {pleno['P1']*100:>5.1f}% {pleno['PX']*100:>5.1f}% {pleno['P2']*100:>5.1f}% | {mejor_resultado15:<10} (PLENO ) | Real: {real_pleno:<9} | {acierto_pleno}")
    print("-" * 120)
    print(f"RESUMEN: {aciertos_totales}/14 ACIERTOS EN EL BOLETO.")

if __name__ == "__main__":
    simulate_past_quiniela()
