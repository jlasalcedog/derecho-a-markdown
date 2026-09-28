"""Simula un proceso lanzado por el Explorador: llama a recolectar() e imprime el resultado.
Uso: python _agrupar_helper.py <ruta> [segundos que el líder "muestra el diálogo"]"""
import json
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _app import cargar  # noqa: E402

app = cargar()
rutas = app.recolectar(sys.argv[1], espera=1.0, maximo=8.0)
print(json.dumps(rutas), flush=True)
if rutas is not None and len(sys.argv) > 2:
    time.sleep(float(sys.argv[2]))
