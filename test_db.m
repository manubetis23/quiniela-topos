% Test connection to SQLite database from MATLAB
db_path = fullfile(pwd, 'quiniela_db.sqlite');

try
    % Create SQLite connection
    conn = sqlite(db_path);
    
    % Fetch some data: Total matches per competition
    query = 'SELECT Competicion, COUNT(*) as Total_Partidos FROM partidos_historico GROUP BY Competicion';
    results = fetch(conn, query);
    
    disp('¡Conexión exitosa a la base de datos SQLite desde MATLAB!');
    disp('Resumen de datos cargados:');
    disp(results);
    
    % Example query: Get Betis matches
    betis_query = 'SELECT Date, HomeTeam, AwayTeam, FTHG, FTAG FROM partidos_historico WHERE HomeTeam LIKE ''%Betis%'' OR AwayTeam LIKE ''%Betis%'' LIMIT 5';
    betis_results = fetch(conn, betis_query);
    disp('Últimos 5 partidos del Betis incluidos en la BD:');
    disp(betis_results);
    
    close(conn);
catch ME
    disp('Error conectando a SQLite:');
    disp(ME.message);
end
