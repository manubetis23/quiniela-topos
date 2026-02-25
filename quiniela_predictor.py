import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

from get_quiniela_matches import obtener_jornada_quiniela

def build_dataset_for_prediction(matches, df_hist):
    print("Extrayendo métricas más recientes para los 15 equipos...")
    
    predictoras = [
        'Home_Rank_Pre', 'Away_Rank_Pre', 'Home_Form_L5', 'Away_Form_L5',
        'Home_Form_HomeL3', 'Away_Form_AwayL3', 'Home_Rest_Days', 'Away_Rest_Days',
        'Home_Played_Euro_Midweek', 'Away_Played_Euro_Midweek', 'H2H_Home_Pts_L3',
        'Home_xG_Understat', 'Home_xGA_Understat', 'Home_xPTS_Understat',
        'Away_xG_Understat', 'Away_xGA_Understat', 'Away_xPTS_Understat',
        'Prob_Home_Bookie', 'Prob_Draw_Bookie', 'Prob_Away_Bookie'
    ]
    
    # Calcular los promedios globales por si nos encontramos equipos de Segunda (imputación)
    medias = df_hist[predictoras].mean()
    
    filas_prediccion = []
    
    for (home, away) in matches:
        fila = {}
        
        # --- DATOS LOCAL (HOME) ---
        hist_h = df_hist[(df_hist['HomeTeam'] == home) | (df_hist['AwayTeam'] == home)]
        if not hist_h.empty:
            ultimo_h = hist_h.iloc[-1]
            if ultimo_h['HomeTeam'] == home:
                fila['Home_Rank_Pre'] = ultimo_h['Home_Rank_Pre']
                fila['Home_Form_L5'] = ultimo_h['Home_Form_L5']
                fila['Home_Form_HomeL3'] = ultimo_h['Home_Form_HomeL3']
                fila['Home_xG_Understat'] = ultimo_h['Home_xG_Understat']
                fila['Home_xGA_Understat'] = ultimo_h['Home_xGA_Understat']
                fila['Home_xPTS_Understat'] = ultimo_h['Home_xPTS_Understat']
            else:
                fila['Home_Rank_Pre'] = ultimo_h['Away_Rank_Pre']
                fila['Home_Form_L5'] = ultimo_h['Away_Form_L5']
                fila['Home_Form_HomeL3'] = ultimo_h['Away_Form_AwayL3']
                fila['Home_xG_Understat'] = ultimo_h['Away_xG_Understat']
                fila['Home_xGA_Understat'] = ultimo_h['Away_xGA_Understat']
                fila['Home_xPTS_Understat'] = ultimo_h['Away_xPTS_Understat']
                
            fila['Home_Rest_Days'] = 7 # Promedio predeterminado
            fila['Home_Played_Euro_Midweek'] = 0
            
        else:
            # Equipo de Segunda División (o no listado). Usamos medias de liga
            fila['Home_Rank_Pre'] = 10  # Mitad de tabla
            fila['Home_Form_L5'] = medias['Home_Form_L5']
            fila['Home_Form_HomeL3'] = medias['Home_Form_HomeL3']
            fila['Home_Rest_Days'] = 7
            fila['Home_Played_Euro_Midweek'] = 0
            fila['Home_xG_Understat'] = medias['Home_xG_Understat']
            fila['Home_xGA_Understat'] = medias['Home_xGA_Understat']
            fila['Home_xPTS_Understat'] = medias['Home_xPTS_Understat']

        # --- DATOS VISITANTE (AWAY) ---
        hist_a = df_hist[(df_hist['HomeTeam'] == away) | (df_hist['AwayTeam'] == away)]
        if not hist_a.empty:
            ultimo_a = hist_a.iloc[-1]
            if ultimo_a['AwayTeam'] == away:
                fila['Away_Rank_Pre'] = ultimo_a['Away_Rank_Pre']
                fila['Away_Form_L5'] = ultimo_a['Away_Form_L5']
                fila['Away_Form_AwayL3'] = ultimo_a['Away_Form_AwayL3']
                fila['Away_xG_Understat'] = ultimo_a['Away_xG_Understat']
                fila['Away_xGA_Understat'] = ultimo_a['Away_xGA_Understat']
                fila['Away_xPTS_Understat'] = ultimo_a['Away_xPTS_Understat']
            else:
                fila['Away_Rank_Pre'] = ultimo_a['Home_Rank_Pre']
                fila['Away_Form_L5'] = ultimo_a['Home_Form_L5']
                fila['Away_Form_AwayL3'] = ultimo_a['Home_Form_HomeL3']
                fila['Away_xG_Understat'] = ultimo_a['Home_xG_Understat']
                fila['Away_xGA_Understat'] = ultimo_a['Home_xGA_Understat']
                fila['Away_xPTS_Understat'] = ultimo_a['Home_xPTS_Understat']
                
            fila['Away_Rest_Days'] = 7
            fila['Away_Played_Euro_Midweek'] = 0
        else:
            fila['Away_Rank_Pre'] = 10
            fila['Away_Form_L5'] = medias['Away_Form_L5']
            fila['Away_Form_AwayL3'] = medias['Away_Form_AwayL3']
            fila['Away_Rest_Days'] = 7
            fila['Away_Played_Euro_Midweek'] = 0
            fila['Away_xG_Understat'] = medias['Away_xG_Understat']
            fila['Away_xGA_Understat'] = medias['Away_xGA_Understat']
            fila['Away_xPTS_Understat'] = medias['Away_xPTS_Understat']

        # Extras: H2H y Cuotas
        # Asignamos cuota neutral para partidos no registrados, salvo que saquemos de api
        fila['H2H_Home_Pts_L3'] = medias['H2H_Home_Pts_L3']
        fila['Prob_Home_Bookie'] = 0.38
        fila['Prob_Draw_Bookie'] = 0.31
        fila['Prob_Away_Bookie'] = 0.31
        
        filas_prediccion.append(fila)
        
    df_pred = pd.DataFrame(filas_prediccion)
    # Reordenar para que coincida exactamente con las columnas de entrenamiento
    df_pred = df_pred[predictoras]
    return df_pred

def generar_quiniela_optima(return_json=False):
    if not return_json:
        print("=======================================================")
        print("      ORQUESTADOR PREDICTIVO: QUINIELA INTELIGENTE     ")
        print("=======================================================\n")
        print("Paso 1: Obteniendo Boleto Oficial de esta Semana...")
    
    matches = obtener_jornada_quiniela()
    if len(matches) == 0:
        if not return_json:
            print("Error: No se ha podido extraer la jornada de internet.")
        return [] if return_json else None
        
    if not return_json:
        print(f"Exito. {len(matches)} partidos encontrados.\n")
        print("Paso 2: Cargando histórico y modelo ML...")
    
    df = pd.read_csv('LaLiga_ML_Dataset.csv')
    df['Prob_Home_Bookie'] = 1 / df['AvgH']
    df['Prob_Draw_Bookie'] = 1 / df['AvgD']
    df['Prob_Away_Bookie'] = 1 / df['AvgA']
    
    model = joblib.load('quiniela_rf_model.pkl')
    
    X_pred = build_dataset_for_prediction(matches, df)
    probabilidades = model.predict_proba(X_pred)
    
    resultados = []
    
    for i in range(min(15, len(matches))):
        home, away = matches[i]
        
        p1 = float(probabilidades[i][0])
        pX = float(probabilidades[i][1])
        p2 = float(probabilidades[i][2])
        
        entropia = - (p1 * np.log2(p1 + 1e-9) + pX * np.log2(pX + 1e-9) + p2 * np.log2(p2 + 1e-9))
        
        resultados.append({
            'Partido_Id': i+1,
            'Home': home,
            'Away': away,
            'Partido': f"{home} - {away}",
            'P1': round(p1, 4), 'PX': round(pX, 4), 'P2': round(p2, 4),
            'Incertidumbre': round(float(entropia), 4)
        })

    df_res = pd.DataFrame(resultados)
    
    pleno_al_quince = df_res.iloc[14] if len(df_res) >= 15 else None
    df_14 = df_res.iloc[:14].copy()
    
    df_14_sorted = df_14.sort_values(by='Incertidumbre', ascending=False)
    
    apuestas_asignadas = {}
    contador_triples, contador_dobles = 0, 0
    
    for _, row in df_14_sorted.iterrows():
        id_partido = row['Partido_Id']
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
            
        apuestas_asignadas[id_partido] = (apuesta, tipo)
    
    # Enrich resultados with bet assignment
    for r in resultados[:14]:
        apuesta, tipo = apuestas_asignadas[r['Partido_Id']]
        r['Apuesta'] = apuesta
        r['Tipo'] = tipo
    
    if pleno_al_quince is not None and len(resultados) >= 15:
        p_orden = [('1', resultados[14]['P1']), ('X', resultados[14]['PX']), ('2', resultados[14]['P2'])]
        p_orden.sort(key=lambda x: x[1], reverse=True)
        resultados[14]['Apuesta'] = p_orden[0][0]
        resultados[14]['Tipo'] = 'Pleno'
    
    if return_json:
        return resultados
    
    # Terminal output
    print("\n-------------------------------------------------------------")
    print(" BOLETO CIENTÍFICO QUINIELA (1 Triple, 2 Dobles) ")
    print("-------------------------------------------------------------")
    
    for i in range(14):
        row = df_res.iloc[i]
        apuesta, tipo = apuestas_asignadas[row['Partido_Id']]
        print(f"{(i+1):2d}. {row['Partido']:<30} | {row['P1']*100:>4.1f}% {row['PX']*100:>4.1f}% {row['P2']*100:>4.1f}% | >> {apuesta:<8} ({tipo})")
        
    print("-------------------------------------------------------------")

def predict_custom_matches(matches_list):
    """Predict custom matches provided as list of (home, away) tuples."""
    df = pd.read_csv('LaLiga_ML_Dataset.csv')
    df['Prob_Home_Bookie'] = 1 / df['AvgH']
    df['Prob_Draw_Bookie'] = 1 / df['AvgD']
    df['Prob_Away_Bookie'] = 1 / df['AvgA']
    
    model = joblib.load('quiniela_rf_model.pkl')
    X_pred = build_dataset_for_prediction(matches_list, df)
    probabilidades = model.predict_proba(X_pred)
    
    resultados = []
    for i, (home, away) in enumerate(matches_list):
        p1 = float(probabilidades[i][0])
        pX = float(probabilidades[i][1])
        p2 = float(probabilidades[i][2])
        entropia = - (p1 * np.log2(p1 + 1e-9) + pX * np.log2(pX + 1e-9) + p2 * np.log2(p2 + 1e-9))
        
        orden = [('1', p1), ('X', pX), ('2', p2)]
        orden.sort(key=lambda x: x[1], reverse=True)
        
        resultados.append({
            'Partido_Id': i+1,
            'Home': home, 'Away': away,
            'Partido': f"{home} - {away}",
            'P1': round(p1, 4), 'PX': round(pX, 4), 'P2': round(p2, 4),
            'Incertidumbre': round(float(entropia), 4),
            'Apuesta': orden[0][0],
            'Tipo': 'Fijo'
        })
    
    return resultados

if __name__ == "__main__":
    generar_quiniela_optima()
