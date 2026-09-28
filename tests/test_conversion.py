"""
Prueba de conversión: convierte cada archivo de tests/fixtures con la misma función
que usa el menú contextual y verifica el contenido del .md.

Uso:  python tests/test_conversion.py
      (con el python del entorno que tenga markitdown instalado)
      MARKITDOWN_APP_DIR=<carpeta> para probar otra copia de app/ (ver _app.py)
"""
import sys

from _app import RAIZ, cargar

FIXTURES = RAIZ / "tests" / "fixtures"
SALIDA = RAIZ / "tests" / "salida"
app = cargar()

ESPERADO = {
    "muestra.docx": ["# Informe de prueba", "ñandú", "| Horas | 42 |"],
    "muestra.xlsx": ["## Datos", "| Enero | 120 |"],
    "muestra.pptx": ["# Diapositiva de prueba", "Microservicios"],
    "muestra.pdf": ["Documento PDF de prueba"],
    "muestra.csv": ["| nombre | cantidad |", "| manzana | 3 |"],
    "muestra.html": ["# Titulo HTML", "**negrita**"],
}


def main() -> int:
    fallos = 0
    for nombre, fragmentos in ESPERADO.items():
        origen = FIXTURES / nombre
        destino = SALIDA / (origen.stem + "_" + origen.suffix.lstrip(".") + ".md")
        try:
            app.convertir(origen, destino)
            texto = destino.read_text(encoding="utf-8")
            faltan = [f for f in fragmentos if f not in texto]
        except Exception as e:  # noqa: BLE001
            faltan, texto = [f"EXCEPCIÓN {type(e).__name__}: {e}"], ""
        if faltan:
            fallos += 1
            print(f"FALLA  {nombre}: falta {faltan}\n{texto[:400]}\n")
        else:
            print(f"OK     {nombre}")
    print(f"\n{len(ESPERADO) - fallos}/{len(ESPERADO)} conversiones correctas")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
