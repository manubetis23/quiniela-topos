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

def generate_context_data(home, away, df_hist):
    """Extract contextual data about both teams for explanation generation."""
    ctx = {'home': home, 'away': away}
    
    df_hist['DateObj'] = pd.to_datetime(df_hist['Date'], format='%d/%m/%Y')
    
    for team, prefix in [(home, 'home'), (away, 'away')]:
        matches = df_hist[(df_hist['HomeTeam'] == team) | (df_hist['AwayTeam'] == team)].sort_values('DateObj')
        if matches.empty:
            ctx[f'{prefix}_pts'] = 0
            ctx[f'{prefix}_rank'] = 20
            ctx[f'{prefix}_form'] = 'N/A'
            ctx[f'{prefix}_form_pts'] = 0
            ctx[f'{prefix}_gf_avg'] = 0
            ctx[f'{prefix}_gc_avg'] = 0
            ctx[f'{prefix}_liga'] = 'Desconocida'
            continue
        
        last = matches.iloc[-1]
        is_home = last['HomeTeam'] == team
        pts_pre = last['Home_Points_Pre'] if is_home else last['Away_Points_Pre']
        result = last['FTR']
        pts_add = 3 if (is_home and result == 'H') or (not is_home and result == 'A') else (1 if result == 'D' else 0)
        ctx[f'{prefix}_pts'] = int(pts_pre) + pts_add if pd.notna(pts_pre) else 0
        
        rank_pre = last['Home_Rank_Pre'] if is_home else last['Away_Rank_Pre']
        ctx[f'{prefix}_rank'] = int(rank_pre) if pd.notna(rank_pre) else 20
        ctx[f'{prefix}_liga'] = str(last.get('Competicion', 'La Liga'))
        
        # Form last 5
        last5 = matches.tail(5)
        form_letters = []
        form_pts = 0
        for _, m in last5.iterrows():
            is_h = m['HomeTeam'] == team
            won = (is_h and m['FTR'] == 'H') or (not is_h and m['FTR'] == 'A')
            drew = m['FTR'] == 'D'
            if won: form_letters.append('V'); form_pts += 3
            elif drew: form_letters.append('E'); form_pts += 1
            else: form_letters.append('D')
        ctx[f'{prefix}_form'] = ''.join(form_letters)
        ctx[f'{prefix}_form_pts'] = form_pts
        
        # Goals averages (last 5)
        gf_list = []
        gc_list = []
        for _, m in last5.iterrows():
            is_h = m['HomeTeam'] == team
            gf_list.append(int(m['FTHG'] if is_h else m['FTAG']))
            gc_list.append(int(m['FTAG'] if is_h else m['FTHG']))
        ctx[f'{prefix}_gf_avg'] = round(sum(gf_list)/len(gf_list), 1) if gf_list else 0
        ctx[f'{prefix}_gc_avg'] = round(sum(gc_list)/len(gc_list), 1) if gc_list else 0
        
        # Home-specific / Away-specific record
        if prefix == 'home':
            home_matches = df_hist[df_hist['HomeTeam'] == team]
            if len(home_matches) >= 3:
                hm = home_matches.tail(5)
                hw = sum(1 for _, m in hm.iterrows() if m['FTR'] == 'H')
                ctx['home_home_record'] = f"{hw}V de {len(hm)} en casa"
            else:
                ctx['home_home_record'] = None
        else:
            away_matches = df_hist[df_hist['AwayTeam'] == team]
            if len(away_matches) >= 3:
                am = away_matches.tail(5)
                aw = sum(1 for _, m in am.iterrows() if m['FTR'] == 'A')
                ctx['away_away_record'] = f"{aw}V de {len(am)} fuera"
            else:
                ctx['away_away_record'] = None
    
    # H2H
    h2h = df_hist[((df_hist['HomeTeam'] == home) & (df_hist['AwayTeam'] == away)) |
                   ((df_hist['HomeTeam'] == away) & (df_hist['AwayTeam'] == home))].sort_values('DateObj')
    if not h2h.empty:
        h2h_last3 = h2h.tail(3)
        h2h_results = []
        for _, m in h2h_last3.iterrows():
            if m['HomeTeam'] == home:
                if m['FTR'] == 'H': h2h_results.append(f"{home}")
                elif m['FTR'] == 'D': h2h_results.append("Empate")
                else: h2h_results.append(f"{away}")
            else:
                if m['FTR'] == 'A': h2h_results.append(f"{home}")
                elif m['FTR'] == 'D': h2h_results.append("Empate")
                else: h2h_results.append(f"{away}")
        ctx['h2h'] = h2h_results
    else:
        ctx['h2h'] = None
    
    return ctx

def generate_explanation(home, away, p1, pX, p2, df_hist):
    """Generate a human-readable explanation of why the AI predicts these percentages."""
    ctx = generate_context_data(home, away, df_hist)
    
    parts = []
    max_prob = max(p1, pX, p2)
    fav = home if p1 == max_prob else ('Empate' if pX == max_prob else away)
    
    # Position context
    hr, ar = ctx['home_rank'], ctx['away_rank']
    hp, ap = ctx['home_pts'], ctx['away_pts']
    if hr <= 4 and ar > 15:
        parts.append(f"{home} es {hr}º ({hp} pts) vs {away} {ar}º ({ap} pts)")
    elif ar <= 4 and hr > 15:
        parts.append(f"{away} es {ar}º ({ap} pts) jugando contra {home} {hr}º ({hp} pts)")
    elif abs(hr - ar) > 8:
        parts.append(f"Gran diferencia en liga: {home} {hr}º vs {away} {ar}º")
    else:
        parts.append(f"Posiciones cercanas: {home} {hr}º ({hp} pts) vs {away} {ar}º ({ap} pts)")
    
    # Relegation zone
    for team, prefix in [(home, 'home'), (away, 'away')]:
        rank = ctx[f'{prefix}_rank']
        if rank >= 18:
            parts.append(f"⚠️ {team} en zona de descenso ({rank}º)")
    
    # Form
    hf, af = ctx['home_form_pts'], ctx['away_form_pts']
    if hf >= 12:
        parts.append(f"{home} en racha: {ctx['home_form']} ({hf}/15 pts)")
    elif hf <= 4:
        parts.append(f"{home} en mala racha: {ctx['home_form']} ({hf}/15 pts)")
    if af >= 12:
        parts.append(f"{away} en racha: {ctx['away_form']} ({af}/15 pts)")
    elif af <= 4:
        parts.append(f"{away} en mala racha: {ctx['away_form']} ({af}/15 pts)")
    
    # Home/away factor
    if ctx.get('home_home_record'):
        parts.append(f"En casa: {ctx['home_home_record']}")
    if ctx.get('away_away_record'):
        parts.append(f"Fuera: {ctx['away_away_record']}")
    
    # Goals
    hgf, agf = ctx['home_gf_avg'], ctx['away_gf_avg']
    hgc, agc = ctx['home_gc_avg'], ctx['away_gc_avg']
    if hgf >= 2.0:
        parts.append(f"{home} ofensivo ({hgf} goles/partido)")
    if agc >= 2.0:
        parts.append(f"{away} encaja mucho ({agc} goles/partido)")
    if agf >= 2.0 and p2 > 0.35:
        parts.append(f"{away} también goleador ({agf} goles/partido)")
    
    # H2H
    if ctx['h2h']:
        h2h_str = ", ".join(ctx['h2h'])
        parts.append(f"H2H reciente: {h2h_str}")
    
    return " · ".join(parts[:4])  # Max 4 factors to keep it readable

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
        
        explicacion = generate_explanation(home, away, p1, pX, p2, df)
        
        resultados.append({
            'Partido_Id': i+1,
            'Home': home,
            'Away': away,
            'Partido': f"{home} - {away}",
            'P1': round(p1, 4), 'PX': round(pX, 4), 'P2': round(p2, 4),
            'Incertidumbre': round(float(entropia), 4),
            'Explicacion': explicacion
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

    if pleno_al_quince is not None:
        p_orden = [('1', pleno_al_quince['P1']), ('X', pleno_al_quince['PX']), ('2', pleno_al_quince['P2'])]
        p_orden.sort(key=lambda x: x[1], reverse=True)
        print(f"15. {pleno_al_quince['Partido']:<30} | {pleno_al_quince['P1']*100:>4.1f}% {pleno_al_quince['PX']*100:>4.1f}% {pleno_al_quince['P2']*100:>4.1f}% | >> {p_orden[0][0]:<8} (Pleno al 15)")

    print("=============================================================\n")

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
        
        explicacion = generate_explanation(home, away, p1, pX, p2, df)
        
        orden = [('1', p1), ('X', pX), ('2', p2)]
        orden.sort(key=lambda x: x[1], reverse=True)
        
        resultados.append({
            'Partido_Id': i+1,
            'Home': home, 'Away': away,
            'Partido': f"{home} - {away}",
            'P1': round(p1, 4), 'PX': round(pX, 4), 'P2': round(p2, 4),
            'Incertidumbre': round(float(entropia), 4),
            'Explicacion': explicacion,
            'Apuesta': orden[0][0],
            'Tipo': 'Fijo'
        })
    
    return resultados

if __name__ == "__main__":
    generar_quiniela_optima()
