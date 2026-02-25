import pandas as pd
from datetime import datetime

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except:
        return pd.NaT

# Diccionario de mapeo: Football-Data.co.uk -> Understat
TEAM_MAP = {
    'Alaves': 'Alaves',
    'Ath Bilbao': 'Athletic Club',
    'Ath Madrid': 'Atletico Madrid',
    'Barcelona': 'Barcelona',
    'Betis': 'Real Betis',
    'Celta': 'Celta Vigo',
    'Elche': 'Elche',
    'Espanol': 'Espanyol',
    'Getafe': 'Getafe',
    'Girona': 'Girona',
    'Levante': 'Levante',
    'Mallorca': 'Mallorca',
    'Osasuna': 'Osasuna',
    'Oviedo': 'Real Oviedo',
    'Real Madrid': 'Real Madrid',
    'Sevilla': 'Sevilla',
    'Sociedad': 'Real Sociedad',
    'Valencia': 'Valencia',
    'Vallecano': 'Rayo Vallecano',
    'Villarreal': 'Villarreal'
}

EURO_TEAMS = ['Real Madrid', 'Barcelona', 'Ath Madrid', 'Villarreal', 'Ath Bilbao', 'Betis', 'Celta', 'Vallecano']

EURO_WEEKS_2025_2026 = [
    ("16/09/2025", "18/09/2025"), ("24/09/2025", "25/09/2025"), ("30/09/2025", "02/10/2025"),
    ("21/10/2025", "23/10/2025"), ("04/11/2025", "06/11/2025"), ("25/11/2025", "27/11/2025"),
    ("09/12/2025", "11/12/2025"), ("20/01/2026", "22/01/2026"), ("27/01/2026", "29/01/2026"),
    ("10/02/2026", "12/02/2026"), ("17/02/2026", "19/02/2026"), ("03/03/2026", "05/03/2026"),
    ("10/03/2026", "12/03/2026"), ("07/04/2026", "09/04/2026"), ("14/04/2026", "16/04/2026"),
    ("28/04/2026", "30/04/2026"), ("05/05/2026", "07/05/2026")
]
euro_weeks_parsed = [(parse_date(s), parse_date(e)) for s, e in EURO_WEEKS_2025_2026]

def feature_engineering():
    print("Iniciando Feature Engineering avanzado sobre La Liga...")
    
    # 1. Cargar Datos
    df_la_liga = pd.read_csv("LaLiga_Data.csv")
    df_segunda = pd.read_csv("Segunda_Data.csv")
    
    # Concatenar y Ordenar por Fecha (Cronológicamente muy importante para Form)
    df = pd.concat([df_la_liga, df_segunda], ignore_index=True)
    df['DateObj'] = df['Date'].apply(parse_date)
    df = df.sort_values('DateObj').reset_index(drop=True)
    
    # Rellenar Odds nulas con la media local
    df['AvgH'] = df['AvgH'].fillna(df['AvgH'].mean())
    df['AvgD'] = df['AvgD'].fillna(df['AvgD'].mean())
    df['AvgA'] = df['AvgA'].fillna(df['AvgA'].mean())
    
    # Cargar Understat Data
    df_understat = pd.read_csv("Understat_LaLiga_Stats.csv")
    # Crear diccionarios de busqueda rápida de Understat asumiendo que el poder real del equipo es su promedio anual
    understat_dict = {}
    for _, row in df_understat.iterrows():
        understat_dict[row['Equipo']] = {
            'xG_season': row['avg_xG_season'],
            'xGA_season': row['avg_xGA_season'],
            'xpts_season': row['avg_xpts_season']
        }
    
    # Diccionarios de estado
    team_stats = {}
    h2h_stats = {} # Diccionario de diccionarios: h2h[teamA][teamB] = [puntos_A_vs_B, ...]
    
    def init_team(t):
        if t not in team_stats:
            team_stats[t] = {
                'points': 0,
                'goals_scored': 0,
                'goals_conceded': 0,
                'home_points': 0,
                'away_points': 0,
                'matches_played': 0,
                'home_matches': 0,
                'away_matches': 0,
                'last_5_results': [], 
                'last_3_home_results': [],
                'last_3_away_results': [],
                'last_match_date': parse_date("01/08/2025"), # Pre-temporada default
            }
        if t not in h2h_stats:
            h2h_stats[t] = {}

    def init_h2h(ta, tb):
        if tb not in h2h_stats[ta]:
            h2h_stats[ta][tb] = []
        if ta not in h2h_stats[tb]:
            h2h_stats[tb][ta] = []

    def get_standings():
        # Clasificar por puntos, luego por diferencia de goles, luego goles marcados
        sorted_teams = sorted(team_stats.keys(), key=lambda x: (
            team_stats[x]['points'], 
            team_stats[x]['goals_scored'] - team_stats[x]['goals_conceded'],
            team_stats[x]['goals_scored']
        ), reverse=True)
        return {team: rank + 1 for rank, team in enumerate(sorted_teams)}

    def calculate_rest_days(team, current_date):
        last_date = team_stats[team]['last_match_date']
        rest_days = (current_date - last_date).days
        
        # Ajustar si jugaron en Europa entre su ultimo partido oficial de liga y este
        played_europe = 0
        if team in EURO_TEAMS:
            for e_start, e_end in euro_weeks_parsed:
                if last_date < e_start and current_date > e_end:
                    # Jugó el miercoles/jueves, aproximamos el descanso desde ese dia
                    mid_europe_date = e_start + (e_end - e_start) / 2
                    rest_days = (current_date - mid_europe_date).days
                    played_europe = 1
                    break
        return rest_days, played_europe

    # Arrays para las nuevas columnas "PRE-PARTIDO"
    features = {
        'Home_Points_Pre': [], 'Away_Points_Pre': [],
        'Home_Rank_Pre': [], 'Away_Rank_Pre': [], # Clasificacion exacta
        'Home_Form_L5': [], 'Away_Form_L5': [],
        'Home_Form_HomeL3': [], 'Away_Form_AwayL3': [], # Capacidad de local y visitante
        'Home_Rest_Days': [], 'Away_Rest_Days': [],
        'Home_Played_Euro_Midweek': [], 'Away_Played_Euro_Midweek': [], # Fatiga europea
        'H2H_Home_Pts_L3': [], # Pts historicos del Home vs Away
        
        # Understat integracion
        'Home_xG_Understat': [], 'Home_xGA_Understat': [], 'Home_xPTS_Understat': [],
        'Away_xG_Understat': [], 'Away_xGA_Understat': [], 'Away_xPTS_Understat': []
    }

    for idx, row in df.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        date_obj = row['DateObj']
        
        init_team(home)
        init_team(away)
        init_h2h(home, away)
        
        # --- A. Extraer estado ANTES del partido ---
        current_standings = get_standings()
        
        features['Home_Points_Pre'].append(team_stats[home]['points'])
        features['Away_Points_Pre'].append(team_stats[away]['points'])
        
        features['Home_Rank_Pre'].append(current_standings[home])
        features['Away_Rank_Pre'].append(current_standings[away])
        
        # Descanso y fatiga europea
        h_rest, h_euro = calculate_rest_days(home, date_obj)
        features['Home_Rest_Days'].append(h_rest)
        features['Home_Played_Euro_Midweek'].append(h_euro)
        
        a_rest, a_euro = calculate_rest_days(away, date_obj)
        features['Away_Rest_Days'].append(a_rest)
        features['Away_Played_Euro_Midweek'].append(a_euro)
            
        # Form
        features['Home_Form_L5'].append(sum(team_stats[home]['last_5_results']))
        features['Away_Form_L5'].append(sum(team_stats[away]['last_5_results']))
        features['Home_Form_HomeL3'].append(sum(team_stats[home]['last_3_home_results']))
        features['Away_Form_AwayL3'].append(sum(team_stats[away]['last_3_away_results']))
        
        # H2H (Ultimos 3 enfentamientos)
        home_h2h_points = sum(h2h_stats[home][away][-3:]) if len(h2h_stats[home][away]) > 0 else 0
        features['H2H_Home_Pts_L3'].append(home_h2h_points)
        
        # Integrar Understat
        home_und_name = TEAM_MAP.get(home, home)
        away_und_name = TEAM_MAP.get(away, away)
        
        u_home = understat_dict.get(home_und_name, {'xG_season': 1.0, 'xGA_season': 1.0, 'xpts_season': 1.0})
        u_away = understat_dict.get(away_und_name, {'xG_season': 1.0, 'xGA_season': 1.0, 'xpts_season': 1.0})
        
        features['Home_xG_Understat'].append(u_home['xG_season'])
        features['Home_xGA_Understat'].append(u_home['xGA_season'])
        features['Home_xPTS_Understat'].append(u_home['xpts_season'])
        
        features['Away_xG_Understat'].append(u_away['xG_season'])
        features['Away_xGA_Understat'].append(u_away['xGA_season'])
        features['Away_xPTS_Understat'].append(u_away['xpts_season'])
        
        # --- B. Actualizar estado DESPUÉS del partido ---
        fthg = row['FTHG']
        ftag = row['FTAG']
        
        if fthg > ftag: 
            h_pts, a_pts = 3, 0
        elif fthg < ftag: 
            h_pts, a_pts = 0, 3
        else: 
            h_pts, a_pts = 1, 1
            
        team_stats[home]['points'] += h_pts
        team_stats[away]['points'] += a_pts
        team_stats[home]['home_points'] += h_pts
        team_stats[away]['away_points'] += a_pts
        
        team_stats[home]['goals_scored'] += fthg
        team_stats[home]['goals_conceded'] += ftag
        team_stats[away]['goals_scored'] += ftag
        team_stats[away]['goals_conceded'] += fthg
        
        team_stats[home]['matches_played'] += 1
        team_stats[away]['matches_played'] += 1
        team_stats[home]['home_matches'] += 1
        team_stats[away]['away_matches'] += 1
        
        team_stats[home]['last_match_date'] = date_obj
        team_stats[away]['last_match_date'] = date_obj
        
        # Mantenemos solo historial reciente
        for t, pts in [(home, h_pts), (away, a_pts)]:
            team_stats[t]['last_5_results'].append(pts)
            if len(team_stats[t]['last_5_results']) > 5:
                team_stats[t]['last_5_results'].pop(0)
                
        team_stats[home]['last_3_home_results'].append(h_pts)
        if len(team_stats[home]['last_3_home_results']) > 3:
            team_stats[home]['last_3_home_results'].pop(0)
            
        team_stats[away]['last_3_away_results'].append(a_pts)
        if len(team_stats[away]['last_3_away_results']) > 3:
            team_stats[away]['last_3_away_results'].pop(0)
            
        h2h_stats[home][away].append(h_pts)
        h2h_stats[away][home].append(a_pts)

    # Añadir nuevas features al Dataframe mediante pd.concat para evitar PerformanceWarning
    feature_df = pd.DataFrame(features)
    df_final = pd.concat([df, feature_df], axis=1)
    
    # Target de Clasificación para Machine Learning 
    # (0: Gana Local, 1: Empate, 2: Gana Visitante)
    def get_result(row):
        if row['FTHG'] > row['FTAG']: return 0  # 1 en Quiniela
        elif row['FTHG'] == row['FTAG']: return 1 # X en Quiniela
        else: return 2                            # 2 en Quiniela
        
    df_final['Target_Result'] = df_final.apply(get_result, axis=1)
    
    print("\nMuestra del DataFrame con Feature Engineering Avanzado (Clasificación, Fatiga y Target):")
    cols_to_show = ['HomeTeam', 'AwayTeam', 'Home_Rank_Pre', 'Away_Rank_Pre', 'Home_Rest_Days', 'Away_Played_Euro_Midweek', 'Target_Result']
    print(df_final[cols_to_show].tail(5))
    
    df_final.to_csv("LaLiga_ML_Dataset.csv", index=False)
    print("\nDataset ML definitivo guardado en 'LaLiga_ML_Dataset.csv'")

if __name__ == "__main__":
    feature_engineering()
