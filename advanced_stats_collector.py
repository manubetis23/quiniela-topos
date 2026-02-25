import requests
import json
import sqlite3
import pandas as pd
import time

API_KEY = "ef2933a0camshb7abaa278f0d0fdp1ac942jsn4b367b8c3cde"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "sofascore.p.rapidapi.com"
}

def get_la_liga_teams():
    # ID de La Liga en Sofascore es 8, season 2024/25 id 61643
    url = "https://sofascore.p.rapidapi.com/tournaments/get-standings"
    querystring = {"tournamentId":"8","seasonId":"61643","type":"total"}
    
    print("Obteniendo equipos de La Liga desde Sofascore...")
    res = requests.get(url, headers=HEADERS, params=querystring)
    data = res.json()
    
    teams = []
    try:
        standings = data['standings'][0]['rows']
        for row in standings:
            team_info = row['team']
            teams.append({'id': team_info['id'], 'name': team_info['name']})
        return teams
    except Exception as e:
        print(f"Error parseando clasificacion: {e}")
        return []

def get_team_advanced_stats(team_id):
    # Cogemos los ultimos 3 partidos para medir el xG reciente y estado de forma
    url = "https://sofascore.p.rapidapi.com/teams/get-last-matches"
    res = requests.get(url, headers=HEADERS, params={"teamId": str(team_id), "page": "0"})
    events = res.json().get('events', [])
    
    xG_list = []
    xGA_list = []
    possession_list = []
    missing_players_total = 0
    
    # Analizamos solo los ultimos 3 partidos validos (finalizados)
    count = 0
    for match in events:
        if match['status']['type'] == 'finished' and count < 3:
            match_id = match['id']
            is_home = (match['homeTeam']['id'] == team_id)
            team_key = 'home' if is_home else 'away'
            opp_key = 'away' if is_home else 'home'
            
            # 1. Estadisticas (xG, posesion)
            try:
                stats_res = requests.get("https://sofascore.p.rapidapi.com/matches/get-statistics", headers=HEADERS, params={"matchId": str(match_id)})
                stats_data = stats_res.json()
                
                # Buscar xG en el JSON
                period_stats = stats_data['statistics'][0]['groups'] # ALL
                for group in period_stats:
                    if group['groupName'] == 'Expected':
                        for item in group['statisticsItems']:
                            if item['name'] == 'Expected goals':
                                xG_list.append(float(item[team_key]))
                                xGA_list.append(float(item[opp_key]))
                    elif group['groupName'] == 'Possession':
                        for item in group['statisticsItems']:
                            if item['name'] == 'Ball possession':
                                pos_val = float(item[team_key].replace('%',''))
                                possession_list.append(pos_val)
                                
            except Exception as e:
                pass # Si no hay stats, saltamos
                
            # 2. Bajas (Lineups -> missingPlayers)
            try:
                lineups_res = requests.get("https://sofascore.p.rapidapi.com/matches/get-lineups", headers=HEADERS, params={"matchId": str(match_id)})
                lineups_data = lineups_res.json()
                if team_key in lineups_data and 'missingPlayers' in lineups_data[team_key]:
                    missing_players_total += len(lineups_data[team_key]['missingPlayers'])
            except Exception as e:
                pass
                
            count += 1
            # Evitar rate-limit
            time.sleep(1)
            
    avg_xG = sum(xG_list)/len(xG_list) if xG_list else 0
    avg_xGA = sum(xGA_list)/len(xGA_list) if xGA_list else 0
    avg_possession = sum(possession_list)/len(possession_list) if possession_list else 0
    
    return {
        'avg_xG_recent': round(avg_xG, 2),
        'avg_xGA_recent': round(avg_xGA, 2),
        'avg_possession': round(avg_possession, 2),
        'recent_injuries_avg': round(missing_players_total / max(1, count), 1)
    }

def main():
    teams = get_la_liga_teams()
    print(f"Se econtraron {len(teams)} equipos en La Liga.")
    
    all_stats = []
    
    for team in teams:
        print(f"Procesando {team['name']}...")
        stats = get_team_advanced_stats(team['id'])
        stats['Equipo'] = team['name']
        all_stats.append(stats)
        
    df = pd.DataFrame(all_stats)
    print("\n--- Estadísticas Avanzadas ---")
    print(df.head())
    
    # Guardar a SQLite y CSV
    conn = sqlite3.connect("quiniela_db.sqlite")
    df.to_sql("equipos_stats_avanzadas", conn, if_exists="replace", index=False)
    df.to_csv("LaLiga_Stats_Avanzadas.csv", index=False)
    conn.close()
    print("Datos avanzados guardados en LaLiga_Stats_Avanzadas.csv y SQLite.")

if __name__ == "__main__":
    main()
