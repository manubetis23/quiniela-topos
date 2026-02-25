import os
import sys
import pandas as pd
from flask import Flask, render_template, jsonify, request

# Asegurar que los imports locales funcionan
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# ============================================================
#  RUTAS DE PÁGINA
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

# ============================================================
#  API REST
# ============================================================

@app.route('/api/prediccion')
def api_prediccion():
    """Obtener la predicción de la jornada actual (scraping en vivo)."""
    try:
        from quiniela_predictor import generar_quiniela_optima
        resultados = generar_quiniela_optima(return_json=True)
        return jsonify({'status': 'ok', 'data': resultados})
    except ImportError:
        return jsonify({'status': 'error', 'message': 'La predicción en vivo solo está disponible en modo local (necesita Playwright). Usa el Boleto Manual para probar la IA.'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/predict-custom', methods=['POST'])
def api_predict_custom():
    """Predecir un boleto manual introducido por el usuario."""
    try:
        from quiniela_predictor import predict_custom_matches
        data = request.get_json()
        matches = [(m['home'], m['away']) for m in data.get('matches', [])]
        if not matches:
            return jsonify({'status': 'error', 'message': 'No matches provided'}), 400
        resultados = predict_custom_matches(matches)
        return jsonify({'status': 'ok', 'data': resultados})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/clasificacion')
def api_clasificacion():
    """Devolver la clasificación actual de Primera y Segunda."""
    try:
        df = pd.read_csv('LaLiga_ML_Dataset.csv')
        df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        
        all_teams = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
        
        clasificacion = []
        for team in all_teams:
            # Goles marcados y recibidos acumulados
            home_games = df[df['HomeTeam'] == team]
            away_games = df[df['AwayTeam'] == team]
            
            gf = int(home_games['FTHG'].sum() + away_games['FTAG'].sum()) if not home_games.empty or not away_games.empty else 0
            gc = int(home_games['FTAG'].sum() + away_games['FTHG'].sum()) if not home_games.empty or not away_games.empty else 0
            
            # Última aparición para puntos, rango y forma
            team_matches = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)]
            if team_matches.empty:
                continue
            last_match = team_matches.sort_values('DateObj').iloc[-1]
            
            if last_match['HomeTeam'] == team:
                pts_pre = last_match['Home_Points_Pre']
                form = last_match['Home_Form_L5']
                # Calcular puntos POST-partido
                result = last_match['FTR']
                pts_add = 3 if result == 'H' else (1 if result == 'D' else 0)
            else:
                pts_pre = last_match['Away_Points_Pre']
                form = last_match['Away_Form_L5']
                result = last_match['FTR']
                pts_add = 3 if result == 'A' else (1 if result == 'D' else 0)
            
            pts_post = (int(pts_pre) if pd.notna(pts_pre) else 0) + pts_add
            
            # Forma últimos 5: recalcular incluyendo el último partido
            team_sorted = team_matches.sort_values('DateObj')
            last_5 = team_sorted.tail(5)
            form_recalc = 0
            form_results = []
            for _, m in last_5.iterrows():
                if m['HomeTeam'] == team:
                    if m['FTR'] == 'H': form_recalc += 3; form_results.append('W')
                    elif m['FTR'] == 'D': form_recalc += 1; form_results.append('D')
                    else: form_results.append('L')
                else:
                    if m['FTR'] == 'A': form_recalc += 3; form_results.append('W')
                    elif m['FTR'] == 'D': form_recalc += 1; form_results.append('D')
                    else: form_results.append('L')
            
            liga = last_match.get('Competicion', 'La Liga')
            
            # Partidos jugados
            pj = len(team_matches)
            pg = sum(1 for _, m in team_matches.iterrows() if (m['HomeTeam']==team and m['FTR']=='H') or (m['AwayTeam']==team and m['FTR']=='A'))
            pe = sum(1 for _, m in team_matches.iterrows() if m['FTR']=='D')
            pp = pj - pg - pe
            
            clasificacion.append({
                'Equipo': team,
                'Puntos': pts_post,
                'PJ': pj, 'PG': pg, 'PE': pe, 'PP': pp,
                'Forma_L5': form_recalc,
                'Forma_Visual': ''.join(form_results),
                'GF': gf,
                'GC': gc,
                'DG': gf - gc,
                'Liga': str(liga)
            })
        
        clasificacion.sort(key=lambda x: (-x['Puntos'], -x['DG']))
        
        primera = [c for c in clasificacion if c['Liga'] == 'La Liga']
        segunda = [c for c in clasificacion if c['Liga'] == 'La Liga 2']
        
        return jsonify({'status': 'ok', 'primera': primera, 'segunda': segunda})
    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'message': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/stats/<equipo>')
def api_stats(equipo):
    """Devolver estadísticas detalladas de un equipo."""
    try:
        df = pd.read_csv('LaLiga_ML_Dataset.csv')
        df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        
        team_matches = df[(df['HomeTeam'] == equipo) | (df['AwayTeam'] == equipo)].copy()
        team_matches = team_matches.sort_values('DateObj')
        
        partidos = []
        pts_acum = 0
        gf_acum = 0
        gc_acum = 0
        results_window = []
        
        for _, row in team_matches.iterrows():
            is_home = row['HomeTeam'] == equipo
            
            if is_home:
                gf = int(row['FTHG']) if pd.notna(row['FTHG']) else 0
                gc = int(row['FTAG']) if pd.notna(row['FTAG']) else 0
                rival = row['AwayTeam']
                condicion = 'Local'
                xg = float(row['Home_xG_Understat']) if pd.notna(row['Home_xG_Understat']) else 0
                xga = float(row['Home_xGA_Understat']) if pd.notna(row['Home_xGA_Understat']) else 0
                won = row['FTR'] == 'H'
                drew = row['FTR'] == 'D'
            else:
                gf = int(row['FTAG']) if pd.notna(row['FTAG']) else 0
                gc = int(row['FTHG']) if pd.notna(row['FTHG']) else 0
                rival = row['HomeTeam']
                condicion = 'Visitante'
                xg = float(row['Away_xG_Understat']) if pd.notna(row['Away_xG_Understat']) else 0
                xga = float(row['Away_xGA_Understat']) if pd.notna(row['Away_xGA_Understat']) else 0
                won = row['FTR'] == 'A'
                drew = row['FTR'] == 'D'
            
            # Puntos post-partido acumulados
            match_pts = 3 if won else (1 if drew else 0)
            pts_acum += match_pts
            gf_acum += gf
            gc_acum += gc
            
            # Resultado visual
            result_letter = 'W' if won else ('D' if drew else 'L')
            results_window.append(result_letter)
            
            # Forma últimos 5 (ventana deslizante)
            last5 = results_window[-5:]
            forma_l5 = sum(3 if r=='W' else 1 if r=='D' else 0 for r in last5)
            
            # GF/GC media últimos 5
            partidos.append({
                'Fecha': row['Date'],
                'FechaSort': row['DateObj'].strftime('%Y-%m-%d'),
                'Rival': rival,
                'Condicion': condicion,
                'Resultado': result_letter,
                'GF': gf,
                'GC': gc,
                'GF_Acum': gf_acum,
                'GC_Acum': gc_acum,
                'Puntos_Acum': pts_acum,
                'Forma_L5': forma_l5,
                'xG': round(xg, 2),
                'xGA': round(xga, 2)
            })
        
        return jsonify({'status': 'ok', 'equipo': equipo, 'partidos': partidos})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/equipos')
def api_equipos():
    """Lista de todos los equipos disponibles."""
    try:
        df = pd.read_csv('LaLiga_ML_Dataset.csv')
        equipos = sorted(list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())))
        return jsonify({'status': 'ok', 'equipos': equipos})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/evolucion-clasificacion')
def api_evolucion():
    """Evolución de puntos jornada a jornada para gráfica de líneas."""
    try:
        df = pd.read_csv('LaLiga_ML_Dataset.csv')
        df['DateObj'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        df = df.sort_values('DateObj')
        
        all_teams = sorted(list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())))
        
        evolution = {}
        for team in all_teams:
            team_points = []
            home_rows = df[df['HomeTeam'] == team][['DateObj', 'Home_Points_Pre']].rename(
                columns={'Home_Points_Pre': 'pts'})
            away_rows = df[df['AwayTeam'] == team][['DateObj', 'Away_Points_Pre']].rename(
                columns={'Away_Points_Pre': 'pts'})
            
            combined = pd.concat([home_rows, away_rows]).sort_values('DateObj')
            
            for _, row in combined.iterrows():
                team_points.append({
                    'fecha': row['DateObj'].strftime('%d/%m'),
                    'puntos': int(row['pts']) if pd.notna(row['pts']) else 0
                })
            
            evolution[team] = team_points
        
        return jsonify({'status': 'ok', 'evolution': evolution, 'teams': all_teams})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 3000))
    print(f"\n🏟️  QUINIELA TOPOS - Dashboard")
    print(f"    Abre tu navegador en: http://localhost:{port}\n")
    app.run(debug=True, port=port, host='0.0.0.0')
