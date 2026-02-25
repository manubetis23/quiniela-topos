% =========================================================================
% SCRIPT: quiniela_ml_train.m
% OBJETIVO: Imputar NaNs, dividir el dataset y entrenar el modelo de 
% predicción (Random Forest / Bagged Trees) para la Quiniela.
% =========================================================================
clear; clc;

fprintf('=======================================================\n');
fprintf('     ENTRENAMIENTO DEL MODELO: RANDOM FOREST (1X2)     \n');
fprintf('=======================================================\n\n');

%% 1. Preparacion de Datos
filename = 'LaLiga_ML_Dataset.csv';
opts = detectImportOptions(filename);
df = readtable(filename, opts);

% Filtramos las 5 primeras jornadas para evitar datos pre-temporada sin sentido
idx_validos = df.Home_Points_Pre > 5 | df.Away_Points_Pre > 5;
df_clean = df(idx_validos, :);

% Variables predictoras (Excluimos identificadores como Goles o Nombres)
predictoras = {'Home_Rank_Pre', 'Away_Rank_Pre', ...
               'Home_Form_L5', 'Away_Form_L5', ...
               'Home_Form_HomeL3', 'Away_Form_AwayL3',...
               'Home_Rest_Days', 'Away_Rest_Days', ...
               'Home_Played_Euro_Midweek', 'Away_Played_Euro_Midweek',...
               'H2H_Home_Pts_L3', ...
               'Home_xG_Understat', 'Home_xGA_Understat', 'Home_xPTS_Understat', ...
               'Away_xG_Understat', 'Away_xGA_Understat', 'Away_xPTS_Understat'};

% Matriz X (Features) y Vector Y (Target)
X = df_clean(:, predictoras);
Y = df_clean.Target_Result; % 0: Local(1), 1: Empate(X), 2: Visitante(2)

% Tratamiento de valores ausentes (NaNs) en H2H (Equipos recien ascendidos)
% Rellenamos con el promedio (imputacion basica)
for i = 1:width(X)
    col_name = X.Properties.VariableNames{i};
    if any(isnan(X{:,i}))
        promedio = mean(X{:,i}, 'omitnan');
        X{isnan(X{:,i}), i} = promedio;
    end
end

fprintf('Data preparada: %d muestras, %d features.\n', height(X), width(X));

%% 2. Split en Train y Test (Entrenamiento y Validacion)
% Usaremos el 80% inicial de la temporada para entrenar
% y el 20% final de la temporada para predecir (Testing)
train_ratio = 0.8;
n_total = height(X);
n_train = round(train_ratio * n_total);

X_train = X(1:n_train, :);
Y_train = Y(1:n_train);

X_test = X(n_train+1:end, :);
Y_test = Y(n_train+1:end);

fprintf('Set de Entrenamiento (Train): %d partidos (historico).\n', n_train);
fprintf('Set de Prueba (Test): %d partidos (futuro virtual).\n\n', n_total - n_train);

%% 3. Entrenamiento: Random Forest (TreeBagger)
fprintf('Entrenando modelo Random Forest (150 arboles)...\n');

% Random Forest es excepcionalmente bueno lidiando con el desbalance de 
% victorias locales ('1') vs ('2'). Tambien es no-lineal y robusto.
numTrees = 150;
% OOBPrediction='on' guarda el error "Out of Bag" para evaluar internamente
modelo_rf = TreeBagger(numTrees, X_train, Y_train, ...
    'Method', 'classification', ...
    'OOBPrediction', 'on', ...
    'MinLeafSize', 5);

fprintf('Modelo entrenado con exito!\n');

%% 4. Evaluacion (Testing)
% Predecimos sobre el set de prueba final
[Y_pred_str, Y_scores] = predict(modelo_rf, X_test);
Y_pred = str2double(Y_pred_str);

% Calculo de la precision global (Accuracy)
aciertos = sum(Y_pred == Y_test);
accuracy = (aciertos / length(Y_test)) * 100;

fprintf('\n=== RESULTADOS DE PREDICCION (TEST) ===\n');
fprintf('Aciertos totales: %d / %d (%.2f%%)\n', aciertos, length(Y_test), accuracy);

% 5. Importancia de Variables (Feature Importance)
% Evaluamos que caracteristicas usó más el bosque para acertar
fprintf('\nCalculando OOB Feature Importance...\n');
try
    % Calcular importancia (puede tardar en versiones viejas)
    modelo_rf_imp = TreeBagger(numTrees, X_train, Y_train, ...
        'Method', 'classification', 'OOBPredictorImportance', 'on', 'MinLeafSize', 5);
    
    importancias = modelo_rf_imp.OOBPermutedPredictorDeltaError;
    [imp_sort, idx_sort] = sort(importancias, 'descend');
    
    fprintf('\nTOP 5 VARIABLES MAS IMPORTANTES PARA PREDECIR UN PARTIDO:\n');
    for i = 1:5
       fprintf(' %d. %s (Peso: %.4f)\n', i, predictoras{idx_sort(i)}, imp_sort(i)); 
    end
    
    % Grafica de importancia
    figure('Name', 'Feature Importance (Random Forest)', 'Position', [100 100 800 500]);
    barh(imp_sort(1:10));
    set(gca, 'YTickLabel', predictoras(idx_sort(1:10)), 'YDir', 'reverse');
    xlabel('Importancia (Delta Error)');
    title('Importancia de las Variables Predictoras');
    grid on;
    saveas(gcf, 'quiniela_importancia_variables.png');
catch
    fprintf('Error obteniendo la importancia de las variables.\n');
end

% Guardar el modelo entrenado
save('quiniela_model.mat', 'modelo_rf', 'predictoras');
fprintf('\nModelo guardado en quiniela_model.mat\n');
