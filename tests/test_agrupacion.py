"""
Prueba de la selección múltiple con procesos reales (named pipes en Windows):
1) 6 procesos lanzados a la vez  -> 1 líder con las 6 rutas, 5 delegan.
2) Un proceso que llega tarde (el líder ya cerró su lote y sigue "en el diálogo")
   no se pierde: espera y lidera un lote nuevo.
3) planificar_destinos(): nombres repetidos y archivos existentes.

Uso:  python tests/test_agrupacion.py
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from _app import cargar

AQUI = Path(__file__).resolve().parent
HELPER = str(AQUI / "_agrupar_helper.py")
fallos = []


def check(cond, msg):
    print(("OK     " if cond else "FALLA  ") + msg)
    if not cond:
        fallos.append(msg)


def lanzar(ruta, mantener=None):
    args = [sys.executable, HELPER, ruta] + ([str(mantener)] if mantener else [])
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def resultado(p, timeout=30):
    out, err = p.communicate(timeout=timeout)
    if p.returncode != 0:
        print(err)
    return json.loads(out.strip().splitlines()[-1])


# 1) lote simultáneo -------------------------------------------------------------
rutas = [f"C:\\docs\\archivo_{i}.pdf" for i in range(6)]
procs = []
for r in rutas:
    procs.append(lanzar(r))
    time.sleep(0.03)  # el Explorador los lanza casi a la vez
res = [resultado(p) for p in procs]
lideres = [r for r in res if r is not None]
check(len(lideres) == 1, f"un solo líder (hubo {len(lideres)})")
check(len(lideres) == 1 and sorted(lideres[0]) == sorted(rutas), "el líder recibió las 6 rutas")

# 2) llegada tardía --------------------------------------------------------------
lider = lanzar("C:\\docs\\primero.pdf", mantener=3)
r1 = json.loads(lider.stdout.readline())  # el líder ya cerró su lote y está "en el diálogo"
tarde = lanzar("C:\\docs\\tarde.pdf")
r2 = resultado(tarde)
lider.communicate(timeout=30)
check(r1 == ["C:\\docs\\primero.pdf"], f"primer lote intacto: {r1}")
check(r2 == ["C:\\docs\\tarde.pdf"], f"el tardío lideró su propio lote: {r2}")

# 3) nombres de destino ----------------------------------------------------------
app = cargar()
with tempfile.TemporaryDirectory() as tmp:
    carpeta = Path(tmp)
    origenes = [Path("x/informe.pdf"), Path("y/Informe.docx"), Path("x/notas.pptx")]
    plan = [d.name for _, d in app.planificar_destinos(origenes, carpeta)]
    check(plan == ["informe (pdf).md", "Informe (docx).md", "notas.md"], f"nombres repetidos: {plan}")
    (carpeta / "notas.md").write_text("previo")
    plan = [d.name for _, d in app.planificar_destinos(origenes, carpeta, reemplazar=False)]
    check(plan[2] == "notas (1).md", f"no reemplaza existentes: {plan}")
    plan = [d.name for _, d in app.planificar_destinos(origenes, carpeta, reemplazar=True)]
    check(plan[2] == "notas.md", f"reemplaza si se pide: {plan}")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} fallas'}")
sys.exit(1 if fallos else 0)
