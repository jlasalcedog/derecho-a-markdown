"""Carga app/convertir_markitdown.pyw como módulo (un .pyw no se importa directo)."""
import importlib.util
import os
from importlib.machinery import SourceFileLoader
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# En CI se apunta a la copia instalada en %LOCALAPPDATA%\DerechoAMarkdown\app
APP_DIR = Path(os.environ.get("MARKITDOWN_APP_DIR", RAIZ / "app"))


def cargar():
    loader = SourceFileLoader("convertir_markitdown", str(APP_DIR / "convertir_markitdown.pyw"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod
