import requests
import json

def test_sofascore_match_stats():
    # El Id del último derbi sevillano o cualquier partido de La Liga
    # Buscamos un partido reciente para testear las estadisticas avanzadas (xG) y Alineaciones (para bajas)
    # Por ejemplo, busquemos los partidos del dia de hoy o simplemente una busqueda de equipo
    
    headers = {
        "x-rapidapi-key": "ef2933a0camshb7abaa278f0d0fdp1ac942jsn4b367b8c3cde",
        "x-rapidapi-host": "sofascore.p.rapidapi.com"
    }

    # 1. Buscar el team_id del Betis o de La Liga
    print("Buscando Real Betis...")
    url_search = "https://sofascore.p.rapidapi.com/teams/search"
    querystring = {"name":"Real Betis"}
    
    try:
        res = requests.get(url_search, headers=headers, params=querystring)
        data = res.json()
        betis_id = None
        for team in data.get('teams', []):
            if 'Betis' in team['name']:
                betis_id = team['id']
                print(f"Betis ID encontrado: {betis_id}")
                break
                
        if not betis_id:
            print("No se encontro el equipo.")
            return

        # 2. Buscar ultimo partido
        url_events = "https://sofascore.p.rapidapi.com/teams/get-last-matches"
        querystring = {"teamId": str(betis_id), "page": "0"}
        res2 = requests.get(url_events, headers=headers, params=querystring)
        
        # Ojo, el formato devuelto puede variar, inspeccionamos:
        events_data = res2.json()
        if 'events' in events_data and len(events_data['events']) > 0:
            last_match = events_data['events'][0]
            match_id = last_match['id']
            print(f"Ultimo partido ID: {match_id} ({last_match['homeTeam']['name']} vs {last_match['awayTeam']['name']})")
            
            # 3. Pedir estadisticas (aqui es donde estaria el xG)
            url_stats = "https://sofascore.p.rapidapi.com/matches/get-statistics"
            querystring = {"matchId": str(match_id)}
            res3 = requests.get(url_stats, headers=headers, params=querystring)
            stats_data = res3.json()
            
            # Guardamos las estadisticas para verlas
            with open('sofascore_sample_stats.json', 'w') as f:
                json.dump(stats_data, f, indent=4)
            print("Estadisticas guardadas en sofascore_sample_stats.json")
            
            # 4. Pedir Alineaciones (Aqui estan los lesionados 'missingPlayers')
            url_lineups = "https://sofascore.p.rapidapi.com/matches/get-lineups"
            res4 = requests.get(url_lineups, headers=headers, params=querystring)
            lineups_data = res4.json()
            with open('sofascore_sample_lineups.json', 'w') as f:
                json.dump(lineups_data, f, indent=4)
            print("Alineaciones/Bajas guardadas en sofascore_sample_lineups.json")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sofascore_match_stats()
