import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def train_quiniela_model():
    print("=======================================================")
    print("  ENTRENAMIENTO AVANZADO: RANDOM FOREST + HYPER-TUNING ")
    print("=======================================================\n")

    # 1. Cargar y Preparar Datos
    filename = 'LaLiga_ML_Dataset.csv'
    df = pd.read_csv(filename)

    # Filtrar jornadas iniciales (ruido de pre-temporada)
    idx_validos = (df['Home_Points_Pre'] > 5) | (df['Away_Points_Pre'] > 5)
    df_clean = df[idx_validos].copy()

    # Añadimos las Cuotas Promedio (AvgH, AvgD, AvgA) como "Sabiduría del Mercado"
    # Convertidas a probabilidad implicita (1/Cuota)
    df_clean['Prob_Home_Bookie'] = 1 / df_clean['AvgH']
    df_clean['Prob_Draw_Bookie'] = 1 / df_clean['AvgD']
    df_clean['Prob_Away_Bookie'] = 1 / df_clean['AvgA']

    predictoras = [
        'Home_Rank_Pre', 'Away_Rank_Pre',
        'Home_Form_L5', 'Away_Form_L5',
        'Home_Form_HomeL3', 'Away_Form_AwayL3',
        'Home_Rest_Days', 'Away_Rest_Days',
        'Home_Played_Euro_Midweek', 'Away_Played_Euro_Midweek',
        'H2H_Home_Pts_L3',
        'Home_xG_Understat', 'Home_xGA_Understat', 'Home_xPTS_Understat',
        'Away_xG_Understat', 'Away_xGA_Understat', 'Away_xPTS_Understat',
        'Prob_Home_Bookie', 'Prob_Draw_Bookie', 'Prob_Away_Bookie',
        'Home_ShotsOnTarget_Avg5', 'Away_ShotsOnTarget_Avg5',
        'Home_Shots_Avg5', 'Away_Shots_Avg5',
        'Home_Fouls_Avg5', 'Away_Fouls_Avg5'
    ]

    X = df_clean[predictoras]
    y = df_clean['Target_Result']

    # Imputar NaNs con la media
    X = X.fillna(X.mean())

    print(f"Data preparada: {len(X)} muestras, {len(predictoras)} features.")

    # 2. Split (Cronológico)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"Set de Entrenamiento: {len(X_train)} partidos.")
    print(f"Set de Prueba: {len(X_test)} partidos.\n")

    # 3. Afinamiento de Hiperparámetros (GridSearchCV)
    print("Buscando los hiperparámetros óptimos (Grid Search)...")
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [5, 10, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [2, 4, 6],
        'max_features': ['sqrt', 'log2']
    }
    
    # Pesos de muestra (Sample Weights) para dar más importancia a la temporada actual
    # Como el DataFrame está ordenado cronológicamente, los últimos índices son los más recientes.
    # Vamos a crear una curva de pesos desde 1.0 (hace 5 años) hasta 3.0 (ahora)
    weights_train = np.linspace(1.0, 3.0, len(X_train))
    
    rf_base = RandomForestClassifier(class_weight='balanced', random_state=42)
    grid_search = GridSearchCV(estimator=rf_base, param_grid=param_grid, 
                               cv=3, n_jobs=-1, scoring='accuracy', verbose=1)
    
    grid_search.fit(X_train, y_train, sample_weight=weights_train)
    
    best_rf = grid_search.best_estimator_
    print("\n¡Mejores hiperparámetros encontrados!")
    print(grid_search.best_params_)

    # 4. Evaluación del Modelo Optimizado
    y_pred = best_rf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n=== RESULTADOS DE PREDICCION OPTIMIZADOS (TEST) ===")
    print(f"Aciertos totales: {sum(y_pred == y_test)} / {len(y_test)} ({accuracy*100:.2f}%)")
    print(classification_report(y_test, y_pred))
    
    # Matriz de confusion visual
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['1', 'X', '2'], yticklabels=['1', 'X', '2'])
    plt.xlabel('Prediccción Modelo')
    plt.ylabel('Resultado Real')
    plt.title('Matriz de Confusión')
    plt.savefig('quiniela_confusion_matrix.png')

    # 5. Feature Importance (¿Qué variables mira más el bosque?)
    importances = best_rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("\nTOP 5 VARIABLES MAS IMPORTANTES (Scikit-Learn Gini Importance):")
    for i in range(5):
        print(f" {i+1}. {predictoras[indices[i]]} (Peso: {importances[indices[i]]:.4f})")
        
    plt.figure(figsize=(10, 6))
    plt.title("Importancia de la Variables Predictoras (Random Forest)")
    plt.bar(range(X.shape[1]), importances[indices], align="center", color='darkred')
    plt.xticks(range(X.shape[1]), [predictoras[i] for i in indices], rotation=90)
    plt.xlim([-1, X.shape[1]])
    plt.tight_layout()
    plt.savefig('quiniela_importancia_variables_py.png')
    
    # 6. Guardar Modelo para Producción
    import joblib
    joblib.dump(best_rf, 'quiniela_rf_model.pkl')
    print("\nModelo final optimizado guardado como 'quiniela_rf_model.pkl'.")
    print("Graficas de evaluación guardadas en PNG.")

if __name__ == "__main__":
    train_quiniela_model()
