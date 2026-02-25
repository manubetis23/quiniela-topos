% =========================================================================
% SCRIPT: quiniela_ml_analysis.m
% OBJETIVO: Cargar el dataset derivado de La Liga y entrenar un 
% modelo de Machine Learning para predecir la Quiniela (1, X, 2).
% =========================================================================
clear; clc; close all;

fprintf('=======================================================\n');
fprintf('     SISTEMA PREDICTIVO QUINIELA (FASE 4 - MATLAB)     \n');
fprintf('=======================================================\n\n');

%% 1. Cargar el Dataset
filename = 'LaLiga_ML_Dataset.csv';
fprintf('Cargando dataset: %s...\n', filename);

% Como el CSV tiene columnas complejas de texto y números, readtable es lo ideal
opts = detectImportOptions(filename);
% MATLAB detecta el formato en la gran mayoría de casos. Si hay error
% se manejará aquí.

try
    df = readtable(filename, opts);
    fprintf('Exito! Dataset cargado con %d partidos y %d variables.\n', height(df), width(df));
catch exception
    fprintf('Error al cargar %s: %s\n', filename, exception.message);
    return;
end

%% 2. Análisis Exploratorio de Datos (EDA)
fprintf('\n--- Iniciando Analisis Exploratorio (EDA) ---\n');

% Eliminar las primeras jornadas (ruido)
% Las jornadas 1 a la 5 no tienen historico suficiente de estados de forma o H2H
fprintf('Eliminando partidos con poco historico pre-partido (ruido)...\n');
% Usamos Home_Matches para saber cuantos partidos llevaban
idx_validos = df.Home_Points_Pre > 5 | df.Away_Points_Pre > 5; % Filtro simple
df_clean = df(idx_validos, :);

fprintf('Partidos validos para el modelo: %d\n', height(df_clean));

% 2.1 Distribución del Target (Resultados 1 X 2)
victorias_locales = sum(df_clean.Target_Result == 0);
empates = sum(df_clean.Target_Result == 1);
victorias_visitantes = sum(df_clean.Target_Result == 2);

figure('Name', 'Distribucion Resultados Quiniela', 'Position', [100 100 800 400]);
subplot(1,2,1);
pie([victorias_locales, empates, victorias_visitantes], {'1 (Local)', 'X (Empate)', '2 (Visitante)'});
title('Distribucion Historica (1X2)');

subplot(1,2,2);
bar([victorias_locales, empates, victorias_visitantes]);
set(gca, 'XTickLabel', {'1', 'X', '2'});
ylabel('Frecuencia');
title('Desequilibrio de Clases');
grid on;
saveas(gcf, 'quiniela_distribucion.png');

% 2.2 Feature Selection (Correlaciones)
fprintf('\nCalculando correlaciones (Feature Importance inicial)...\n');

% Seleccionar solo variables numericas predictoras y el target
% Excluimos identificadores, cuotas (que seran para validar el value), etc.
predictoras = {'Home_Rank_Pre', 'Away_Rank_Pre', ...
               'Home_Form_L5', 'Away_Form_L5', ...
               'Home_Rest_Days', 'Away_Rest_Days', ...
               'Home_xPTS_Understat', 'Away_xPTS_Understat', ...
               'H2H_Home_Pts_L3', 'Target_Result'};

try
    data_ml = df_clean(:, predictoras);
    % Convertir a matriz numerica
    matriz_corr = corr(table2array(data_ml), 'Rows', 'pairwise');
    
    % Mostrar correlacion con el Target_Result
    fprintf('\nCorrelacion (Lineal) de variables con el Target (0=Local, 2=Visitante):\n');
    for i = 1:length(predictoras)-1
        fprintf('  - %-25s: %6.3f\n', predictoras{i}, matriz_corr(i, end));
    end
    
catch e
    fprintf('Aviso: Algunas columnas podrian tener NaNs u otro problema para correlacionar.\n');
end

% 2.3 Visualizacion de Patrones (Ej: Racha vs Target)
figure('Name', 'Analisis de Patrones Complejos', 'Position', [150 150 900 400]);
colors = lines(3); % Colores para 1, X, 2

% Subplot 1: Diferencia de xPTS de Understat
subplot(1,2,1);
hold on;
diff_xPTS = df_clean.Home_xPTS_Understat - df_clean.Away_xPTS_Understat;
diff_Form = df_clean.Home_Form_L5 - df_clean.Away_Form_L5;
idx_1 = df_clean.Target_Result == 0;
idx_X = df_clean.Target_Result == 1;
idx_2 = df_clean.Target_Result == 2;

scatter(diff_xPTS(idx_1), diff_Form(idx_1), 50, colors(1,:), 'filled');
scatter(diff_xPTS(idx_X), diff_Form(idx_X), 50, colors(2,:), '*');
scatter(diff_xPTS(idx_2), diff_Form(idx_2), 50, colors(3,:), 'd', 'filled');
hold off;

xlabel('Diferencia de xPTS (Understat)');
ylabel('Diferencia de Racha (Ultimos 5)');
title('Diferencia de Forma y xPTS vs Resultado');
legend('1', 'X', '2', 'Location', 'Best');
grid on;

% Subplot 2: Fatiga vs Clasificacion
subplot(1,2,2);
hold on;
diff_Rank = df_clean.Home_Rank_Pre - df_clean.Away_Rank_Pre;
diff_Rest = df_clean.Home_Rest_Days - df_clean.Away_Rest_Days;

scatter(diff_Rank(idx_1), diff_Rest(idx_1), 50, colors(1,:), 'filled');
scatter(diff_Rank(idx_X), diff_Rest(idx_X), 50, colors(2,:), '*');
scatter(diff_Rank(idx_2), diff_Rest(idx_2), 50, colors(3,:), 'd', 'filled');
hold off;

xlabel('Diferencia Rank (Home - Away)');
ylabel('Diferencia Descanso (Home - Away)');
title('Fatiga y Posicion vs Resultado');
legend('1', 'X', '2', 'Location', 'Best');
grid on;

saveas(gcf, 'quiniela_patrones.png');

fprintf('\nEDA Finalizado. Graficos guardados (quiniela_distribucion.png, quiniela_patrones.png).\n');
fprintf('Revisaremos los resultados visualmente antes de entrenar el modelo (Phase 4B).\n');
