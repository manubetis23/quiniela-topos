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
                pts = last_match['Home_Points_Pre']
                rank = last_match['Home_Rank_Pre']
                form = last_match['Home_Form_L5']
            else:
                pts = last_match['Away_Points_Pre']
                rank = last_match['Away_Rank_Pre']
                form = last_match['Away_Form_L5']
            
            liga = last_match.get('Competicion', 'La Liga')
            
            clasificacion.append({
                'Equipo': team,
                'Puntos': int(pts) if pd.notna(pts) else 0,
                'Posicion': int(rank) if pd.notna(rank) else 99,
                'Forma_L5': int(form) if pd.notna(form) else 0,
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
        
        home_matches = df[df['HomeTeam'] == equipo].copy()
        away_matches = df[df['AwayTeam'] == equipo].copy()
        
        partidos = []
        for _, row in home_matches.iterrows():
            partidos.append({
                'Fecha': row['Date'],
                'Rival': row['AwayTeam'],
                'Condicion': 'Local',
                'Resultado': row['FTR'],
                'GF': int(row['FTHG']) if pd.notna(row['FTHG']) else 0,
                'GC': int(row['FTAG']) if pd.notna(row['FTAG']) else 0,
                'Puntos_Acum': int(row['Home_Points_Pre']) if pd.notna(row['Home_Points_Pre']) else 0,
                'Posicion': int(row['Home_Rank_Pre']) if pd.notna(row['Home_Rank_Pre']) else 0,
                'Forma_L5': int(row['Home_Form_L5']) if pd.notna(row['Home_Form_L5']) else 0,
                'xG': float(row['Home_xG_Understat']) if pd.notna(row['Home_xG_Understat']) else 0,
                'xGA': float(row['Home_xGA_Understat']) if pd.notna(row['Home_xGA_Understat']) else 0
            })
            
        for _, row in away_matches.iterrows():
            partidos.append({
                'Fecha': row['Date'],
                'Rival': row['HomeTeam'],
                'Condicion': 'Visitante',
                'Resultado': row['FTR'],
                'GF': int(row['FTAG']) if pd.notna(row['FTAG']) else 0,
                'GC': int(row['FTHG']) if pd.notna(row['FTHG']) else 0,
                'Puntos_Acum': int(row['Away_Points_Pre']) if pd.notna(row['Away_Points_Pre']) else 0,
                'Posicion': int(row['Away_Rank_Pre']) if pd.notna(row['Away_Rank_Pre']) else 0,
                'Forma_L5': int(row['Away_Form_L5']) if pd.notna(row['Away_Form_L5']) else 0,
                'xG': float(row['Away_xG_Understat']) if pd.notna(row['Away_xG_Understat']) else 0,
                'xGA': float(row['Away_xGA_Understat']) if pd.notna(row['Away_xGA_Understat']) else 0
            })
        
        partidos.sort(key=lambda x: x['Fecha'])
        
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
