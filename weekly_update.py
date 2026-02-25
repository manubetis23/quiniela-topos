#!/usr/bin/env python3
"""
QUINIELA INTELIGENTE — Script de Actualización Semanal
Ejecutar cada lunes para descargar los últimos resultados,
recalcular features y reentrenar el modelo ML.

Uso manual:   python weekly_update.py
Uso con cron:  0 9 * * 1 cd /Users/manubetis23/Desktop/quiniela && env/bin/python weekly_update.py >> update.log 2>&1
"""

import subprocess
import sys
import os
from datetime import datetime

LOG_PREFIX = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

def run_step(name, script):
    print(f"\n{LOG_PREFIX} === PASO: {name} ===")
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print(f"{LOG_PREFIX} ✅ {name} completado correctamente.")
            if result.stdout:
                # Limit output to last 5 lines
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    print(f"    {line}")
            return True
        else:
            print(f"{LOG_PREFIX} ❌ {name} falló con código {result.returncode}")
            if result.stderr:
                print(f"    ERROR: {result.stderr[:300]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"{LOG_PREFIX} ⏰ {name} excedió el tiempo límite (120s)")
        return False
    except Exception as e:
        print(f"{LOG_PREFIX} ❌ {name} error inesperado: {e}")
        return False

def main():
    print("=" * 60)
    print(f"{LOG_PREFIX} ACTUALIZACIÓN SEMANAL — QUINIELA INTELIGENTE")
    print("=" * 60)
    
    steps = [
        ("1. Descargar datos actualizados (football-data.co.uk)", "data_collector.py"),
        ("2. Scraping Understat (xG, xGA, xPTS)", "understat_scraper_pw.py"),
        ("3. Feature Engineering completo", "feature_engineering.py"),
        ("4. Reentrenar modelo Random Forest", "quiniela_ml_train.py"),
    ]
    
    resultados = []
    for name, script in steps:
        if os.path.exists(script):
            ok = run_step(name, script)
            resultados.append((name, ok))
        else:
            print(f"{LOG_PREFIX} ⚠️  Script {script} no encontrado, saltando.")
            resultados.append((name, False))
    
    print("\n" + "=" * 60)
    print(f"{LOG_PREFIX} RESUMEN DE ACTUALIZACIÓN")
    print("=" * 60)
    
    for name, ok in resultados:
        status = "✅ OK" if ok else "❌ FALLO"
        print(f"  {status}  {name}")
    
    total_ok = sum(1 for _, ok in resultados if ok)
    print(f"\n  {total_ok}/{len(resultados)} pasos completados.")
    print("=" * 60)

if __name__ == "__main__":
    main()
