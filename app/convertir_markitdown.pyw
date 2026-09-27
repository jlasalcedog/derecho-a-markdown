# -*- coding: utf-8 -*-
"""
Derecho a Markdown: "Convertir a Markdown" en el menú contextual de Windows.

Uso:  pythonw.exe convertir_markitdown.pyw "C:\\ruta\\archivo.pdf"

1. Abre el diálogo "Guardar como" (carpeta del archivo y mismo nombre .md por defecto).
2. Convierte con microsoft/markitdown mostrando una ventana de progreso.
3. Ofrece abrir el .md resultante.
"""
import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

APP_NAME = "Derecho a Markdown"
APP_DIR = Path(__file__).resolve().parent
LOG_FILE = APP_DIR / "errores.log"
ICON_FILE = APP_DIR / "markitdown.ico"


def log_error(msg: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except OSError:
        pass


def convertir(origen: Path, destino: Path) -> int:
    """Convierte `origen` a Markdown y lo guarda en `destino`. Devuelve nº de caracteres."""
    from markitdown import MarkItDown  # import diferido: tarda ~1-2 s

    md = MarkItDown(enable_plugins=False)
    resultado = md.convert(str(origen))
    texto = resultado.text_content or ""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return len(texto)


def main() -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    # Nitidez en pantallas con escalado (evita diálogos borrosos)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw()
    root.title(APP_NAME)
    if ICON_FILE.exists():
        try:
            root.iconbitmap(default=str(ICON_FILE))
        except Exception:
            pass
    root.attributes("-topmost", True)  # que el diálogo salga al frente del Explorador

    if len(sys.argv) < 2:
        messagebox.showinfo(
            APP_NAME,
            "Haz click derecho sobre un archivo y elige\n"
            "\"Convertir a Markdown\".",
            parent=root,
        )
        return 1

    origen = Path(sys.argv[1]).resolve()
    if not origen.is_file():
        messagebox.showerror(APP_NAME, f"No se encontró el archivo:\n{origen}", parent=root)
        return 1

    # 1) ¿Dónde guardar?
    ruta = filedialog.asksaveasfilename(
        parent=root,
        title=f"Guardar Markdown de «{origen.name}»",
        initialdir=str(origen.parent),
        initialfile=origen.stem + ".md",
        defaultextension=".md",
        filetypes=[("Markdown", "*.md"), ("Texto", "*.txt"), ("Todos los archivos", "*.*")],
        confirmoverwrite=True,
    )
    if not ruta:
        return 0  # cancelado
    destino = Path(ruta)

    # 2) Ventana de progreso mientras convierte
    win = tk.Toplevel(root)
    win.title(APP_NAME)
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.protocol("WM_DELETE_WINDOW", lambda: None)  # no cerrar a mitad
    frame = ttk.Frame(win, padding=16)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=f"Convirtiendo «{origen.name}» a Markdown…").pack(anchor="w")
    barra = ttk.Progressbar(frame, mode="indeterminate", length=340)
    barra.pack(pady=(10, 0), fill="x")
    barra.start(12)
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x = (win.winfo_screenwidth() - w) // 2
    y = (win.winfo_screenheight() - h) // 3
    win.geometry(f"+{x}+{y}")

    estado: dict = {}

    def trabajo():
        try:
            estado["chars"] = convertir(origen, destino)
        except BaseException as e:  # noqa: BLE001
            estado["error"] = e
            log_error(f"{origen} -> {destino}\n{traceback.format_exc()}")

    hilo = threading.Thread(target=trabajo, daemon=True)
    hilo.start()

    def revisar():
        if hilo.is_alive():
            root.after(150, revisar)
            return
        barra.stop()
        win.destroy()
        if "error" in estado:
            e = estado["error"]
            messagebox.showerror(
                APP_NAME,
                f"No se pudo convertir «{origen.name}».\n\n"
                f"{type(e).__name__}: {e}\n\nDetalle en:\n{LOG_FILE}",
                parent=root,
            )
        else:
            aviso = ""
            if estado.get("chars", 0) == 0:
                aviso = "\n\nAtención: el resultado quedó vacío (¿PDF escaneado sin texto?)."
            if messagebox.askyesno(
                APP_NAME,
                f"Listo. Se guardó:\n{destino}{aviso}\n\n¿Abrir el archivo ahora?",
                parent=root,
            ):
                try:
                    os.startfile(str(destino))  # type: ignore[attr-defined]
                except Exception:
                    pass
        root.quit()

    root.after(150, revisar)
    root.mainloop()
    root.destroy()
    return 0 if "error" not in estado else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log_error(traceback.format_exc())
        raise
