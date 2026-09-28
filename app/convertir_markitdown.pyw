# -*- coding: utf-8 -*-
"""
Derecho a Markdown: "Convertir a Markdown" en el menú contextual de Windows.

Uso:  pythonw.exe convertir_markitdown.pyw "C:\\ruta\\archivo.pdf"

Con varios archivos seleccionados, el Explorador lanza un proceso por archivo.
El primero en arrancar se queda como "líder": recibe las rutas de los demás por
un named pipe y muestra UNA sola ventana para todo el lote. Los demás le entregan
su ruta y terminan sin mostrar nada.

- 1 archivo  -> diálogo "Guardar como" (carpeta del archivo, mismo nombre .md).
- Varios     -> se elige la carpeta de destino una vez, barra "N de M",
                botón Cancelar y resumen final.
"""
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

APP_NAME = "Derecho a Markdown"
APP_DIR = Path(__file__).resolve().parent
LOG_FILE = APP_DIR / "errores.log"
ICON_FILE = APP_DIR / "markitdown.ico"

# Agrupación de la selección múltiple
ESPERA_SILENCIO = 0.8  # s sin llegar rutas nuevas => el lote está completo
ESPERA_MAXIMA = 10.0   # s como máximo recolectando
REINTENTO = 0.3        # s entre intentos de un proceso "seguidor"


# --------------------------------------------------------------------------- utilidades
def log_error(msg: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except OSError:
        pass


def _nuevo_conversor():
    from markitdown import MarkItDown  # import diferido: tarda ~1-2 s

    return MarkItDown(enable_plugins=False)


def convertir(origen: Path, destino: Path, md=None) -> int:
    """Convierte `origen` a Markdown y lo guarda en `destino`. Devuelve nº de caracteres."""
    md = md or _nuevo_conversor()
    texto = md.convert(str(origen)).text_content or ""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return len(texto)


def planificar_destinos(origenes, carpeta: Path, reemplazar: bool = True):
    """Devuelve [(origen, destino)] para un lote.

    - Si dos archivos comparten nombre base (informe.pdf, informe.docx) se agrega la
      extensión: "informe (pdf).md", "informe (docx).md".
    - Con reemplazar=False, si el .md ya existe se usa "nombre (1).md", "(2)"...
    """
    origenes = [Path(o) for o in origenes]
    conteo = {}
    for o in origenes:
        conteo[o.stem.lower()] = conteo.get(o.stem.lower(), 0) + 1

    usados, plan = set(), []
    for o in origenes:
        base = o.stem if conteo[o.stem.lower()] == 1 else f"{o.stem} ({o.suffix.lstrip('.').lower()})"
        destino = carpeta / f"{base}.md"
        n = 1
        while destino.name.lower() in usados or (not reemplazar and destino.exists()):
            destino = carpeta / f"{base} ({n}).md"
            n += 1
        usados.add(destino.name.lower())
        plan.append((o, destino))
    return plan


# --------------------------------------------------------------------------- instancia única
def _direccion():
    usuario = "".join(c for c in (os.environ.get("USERNAME") or os.environ.get("USER") or "user") if c.isalnum())
    if sys.platform == "win32":
        return rf"\\.\pipe\derecho-a-markdown-{usuario}", "AF_PIPE"
    import tempfile  # (solo para pruebas fuera de Windows)

    return os.path.join(tempfile.gettempdir(), f"derecho-a-markdown-{usuario}.sock"), "AF_UNIX"


def recolectar(ruta: str, espera=ESPERA_SILENCIO, maximo=ESPERA_MAXIMA):
    """Devuelve la lista de rutas del lote si este proceso es el líder,
    o None si entregó su ruta a otro proceso (y debe terminar)."""
    from multiprocessing.connection import Client, Listener

    direccion, familia = _direccion()
    while True:
        # 1) ¿Soy el primero? Crear el pipe falla si ya existe (FIRST_PIPE_INSTANCE).
        try:
            listener = Listener(direccion, family=familia)
            break
        except OSError:
            pass
        # 2) Ya hay un líder: entregarle la ruta.
        try:
            with Client(direccion, family=familia) as c:
                c.send(ruta)
                if c.recv() == "ok":
                    return None
            # "ocupado": el líder ya cerró su lote; esperar a que termine y liderar el siguiente
        except (OSError, EOFError):
            if familia == "AF_UNIX" and os.path.exists(direccion):
                try:
                    os.unlink(direccion)  # socket huérfano de un proceso que murió
                except OSError:
                    pass
        time.sleep(REINTENTO)

    estado = {"rutas": [ruta], "ultima": time.monotonic(), "abierto": True}
    lock = threading.Lock()

    def servir():
        while True:
            try:
                conn = listener.accept()
            except Exception:
                return
            try:
                r = conn.recv()
                with lock:
                    if estado["abierto"]:
                        estado["rutas"].append(r)
                        estado["ultima"] = time.monotonic()
                        conn.send("ok")
                    else:
                        conn.send("ocupado")
            except Exception:
                pass
            finally:
                conn.close()

    # El listener queda vivo hasta que termine el proceso: los que lleguen tarde
    # reciben "ocupado" y reintentan, en vez de perderse.
    threading.Thread(target=servir, daemon=True).start()
    inicio = time.monotonic()
    while True:
        time.sleep(0.05)
        with lock:
            ahora = time.monotonic()
            if ahora - estado["ultima"] >= espera or ahora - inicio >= maximo:
                estado["abierto"] = False
                rutas = list(estado["rutas"])
                break

    vistos, unicos = set(), []
    for r in rutas:
        clave = os.path.normcase(os.path.abspath(r))
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(r)
    unicos.sort(key=lambda r: Path(r).name.lower())
    return unicos


# --------------------------------------------------------------------------- interfaz
def _preparar_tk():
    import tkinter as tk

    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # diálogos nítidos con escalado
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
    root.attributes("-topmost", True)  # que los diálogos salgan al frente del Explorador
    return root


class Progreso:
    """Ventana pequeña con texto, barra y (opcional) botón Cancelar."""

    def __init__(self, root, total=None, cancelable=False):
        import tkinter as tk
        from tkinter import ttk

        self.cancelado = False
        self.win = tk.Toplevel(root)
        self.win.title(APP_NAME)
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.cancelar if cancelable else (lambda: None))
        frame = ttk.Frame(self.win, padding=16)
        frame.pack(fill="both", expand=True)
        self.texto = tk.StringVar(value="Preparando…")
        ttk.Label(frame, textvariable=self.texto, width=58).pack(anchor="w")
        if total:
            self.barra = ttk.Progressbar(frame, mode="determinate", length=380, maximum=total)
        else:
            self.barra = ttk.Progressbar(frame, mode="indeterminate", length=380)
            self.barra.start(12)
        self.barra.pack(pady=(10, 0), fill="x")
        if cancelable:
            self.boton = ttk.Button(frame, text="Cancelar", command=self.cancelar)
            self.boton.pack(anchor="e", pady=(12, 0))
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() - self.win.winfo_width()) // 2
        y = (self.win.winfo_screenheight() - self.win.winfo_height()) // 3
        self.win.geometry(f"+{x}+{y}")

    def cancelar(self):
        self.cancelado = True
        self.texto.set("Cancelando… (se termina el archivo actual)")
        try:
            self.boton.state(["disabled"])
        except Exception:
            pass

    def cerrar(self):
        try:
            self.barra.stop()
        except Exception:
            pass
        self.win.destroy()


def _en_segundo_plano(root, trabajo, al_terminar, cada=None):
    """Ejecuta `trabajo` en un hilo; llama a `cada()` periódicamente y `al_terminar()` al final."""
    hilo = threading.Thread(target=trabajo, daemon=True)
    hilo.start()

    def revisar():
        if cada:
            cada()
        if hilo.is_alive():
            root.after(120, revisar)
        else:
            al_terminar()

    root.after(120, revisar)


def flujo_individual(root, origen: Path) -> int:
    from tkinter import filedialog, messagebox

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
        return 0
    destino = Path(ruta)
    prog = Progreso(root)
    prog.texto.set(f"Convirtiendo «{origen.name}» a Markdown…")
    estado: dict = {}

    def trabajo():
        try:
            estado["chars"] = convertir(origen, destino)
        except BaseException as e:  # noqa: BLE001
            estado["error"] = e
            log_error(f"{origen} -> {destino}\n{traceback.format_exc()}")

    def fin():
        prog.cerrar()
        if "error" in estado:
            e = estado["error"]
            messagebox.showerror(
                APP_NAME,
                f"No se pudo convertir «{origen.name}».\n\n{type(e).__name__}: {e}\n\nDetalle en:\n{LOG_FILE}",
                parent=root,
            )
        else:
            aviso = ""
            if estado.get("chars", 0) == 0:
                aviso = "\n\nAtención: el resultado quedó vacío (¿PDF escaneado sin texto?)."
            if messagebox.askyesno(
                APP_NAME, f"Listo. Se guardó:\n{destino}{aviso}\n\n¿Abrir el archivo ahora?", parent=root
            ):
                _abrir(destino)
        root.quit()

    _en_segundo_plano(root, trabajo, fin)
    root.mainloop()
    return 2 if "error" in estado else 0


def flujo_lote(root, origenes) -> int:
    from tkinter import filedialog, messagebox

    carpetas = {o.parent for o in origenes}
    try:
        inicial = Path(os.path.commonpath([str(c) for c in carpetas]))
    except ValueError:  # distintas unidades (C:, D:)
        inicial = origenes[0].parent
    carpeta = filedialog.askdirectory(
        parent=root,
        title=f"Carpeta donde guardar los {len(origenes)} archivos Markdown",
        initialdir=str(inicial),
        mustexist=False,
    )
    if not carpeta:
        return 0
    carpeta = Path(carpeta)

    plan = planificar_destinos(origenes, carpeta, reemplazar=True)
    existentes = [d for _, d in plan if d.exists()]
    if existentes:
        lista = "\n".join(f"• {d.name}" for d in existentes[:8]) + ("\n…" if len(existentes) > 8 else "")
        r = messagebox.askyesnocancel(
            APP_NAME,
            f"{len(existentes)} archivo(s) ya existen en la carpeta:\n{lista}\n\n"
            "Sí = reemplazarlos\nNo = guardar con otro nombre, ej. «nombre (1).md»\nCancelar = no convertir nada",
            parent=root,
        )
        if r is None:
            return 0
        if r is False:
            plan = planificar_destinos(origenes, carpeta, reemplazar=False)

    total = len(plan)
    prog = Progreso(root, total=total, cancelable=True)
    estado = {"i": 0, "texto": "Cargando MarkItDown…", "ok": [], "vacios": [], "errores": []}

    def trabajo():
        try:
            md = _nuevo_conversor()
        except BaseException as e:  # noqa: BLE001
            log_error(traceback.format_exc())
            estado["errores"] = [(o, e) for o, _ in plan]
            return
        for i, (o, d) in enumerate(plan):
            if prog.cancelado:
                break
            estado["texto"] = f"Convirtiendo {i + 1} de {total}: {o.name}"
            try:
                n = convertir(o, d, md)
                (estado["ok"] if n else estado["vacios"]).append(d)
            except BaseException as e:  # noqa: BLE001
                estado["errores"].append((o, e))
                log_error(f"{o} -> {d}\n{traceback.format_exc()}")
            estado["i"] = i + 1

    def cada():
        if not prog.cancelado:
            prog.texto.set(estado["texto"])
        prog.barra["value"] = estado["i"]

    def fin():
        prog.cerrar()
        hechos = len(estado["ok"]) + len(estado["vacios"])
        partes = [f"Se convirtieron {hechos} de {total} archivos en:\n{carpeta}"]
        if prog.cancelado and estado["i"] < total:
            partes.append(f"Cancelado: quedaron {total - estado['i']} sin convertir.")
        if estado["vacios"]:
            partes.append("Quedaron vacíos (¿PDF escaneado?):\n" + "\n".join(f"• {d.name}" for d in estado["vacios"][:6]))
        if estado["errores"]:
            partes.append(
                f"Con error ({len(estado['errores'])}):\n"
                + "\n".join(f"• {o.name}: {type(e).__name__}" for o, e in estado["errores"][:6])
                + f"\nDetalle en: {LOG_FILE}"
            )
        mensaje = "\n\n".join(partes)
        if hechos:
            if messagebox.askyesno(APP_NAME, mensaje + "\n\n¿Abrir la carpeta?", parent=root):
                _abrir(carpeta)
        else:
            messagebox.showerror(APP_NAME, mensaje, parent=root)
        root.quit()

    _en_segundo_plano(root, trabajo, fin, cada)
    root.mainloop()
    return 2 if estado["errores"] else 0


def _abrir(ruta: Path):
    try:
        os.startfile(str(ruta))  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> int:
    if len(sys.argv) < 2:
        from tkinter import messagebox

        root = _preparar_tk()
        messagebox.showinfo(
            APP_NAME,
            "Haz click derecho sobre uno o varios archivos y elige\n\"Convertir a Markdown\".",
            parent=root,
        )
        return 1

    rutas = recolectar(sys.argv[1])
    if rutas is None:
        return 0  # otro proceso se encarga de este archivo

    from tkinter import messagebox

    root = _preparar_tk()
    origenes = [Path(r).resolve() for r in rutas]
    faltan = [o for o in origenes if not o.is_file()]
    origenes = [o for o in origenes if o.is_file()]
    if faltan and not origenes:
        messagebox.showerror(APP_NAME, "No se encontró:\n" + "\n".join(str(f) for f in faltan[:6]), parent=root)
        return 1
    try:
        if len(origenes) == 1:
            return flujo_individual(root, origenes[0])
        return flujo_lote(root, origenes)
    finally:
        try:
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log_error(traceback.format_exc())
        raise
