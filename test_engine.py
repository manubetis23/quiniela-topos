from quiniela_predictor import generar_quiniela_optima
import json

res = generar_quiniela_optima(return_json=True)
print("Engine Output Length:", len(res))
try:
    print(json.dumps(res[:1], indent=2))
except Exception as e:
    print(e)
