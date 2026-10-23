"""Ejecuta los módulos de PrestaMatch en orden, compartiendo variables."""
from pathlib import Path
import os
import json
import traceback
import sys
from IPython.display import display

BASE = Path(__file__).resolve().parent
DATOS = BASE / "data"
SALIDA = BASE / "resultados"
NECESARIOS = ("solicitudes_train.csv", "solicitudes_test.csv", "comportamiento_bancario.csv")

def main():
    faltan = [nombre for nombre in NECESARIOS if not (DATOS / nombre).is_file()]
    if faltan:
        print("Faltan CSV oficiales en la carpeta data/: " + ", ".join(faltan))
        print("Descargalos de Kaggle y copialos a data/ sin renombrarlos.")
        return 2
    SALIDA.mkdir(exist_ok=True)
    os.chdir(DATOS)
    # Todos los módulos comparten las variables creadas previamente.
    entorno = {"__name__": "__main__", "display": display}
    modulos = sorted((BASE / "modulos").glob("*.ipynb"))
    for archivo in modulos:
        print("\n###", archivo.stem, "###", flush=True)
        cuaderno = json.loads(archivo.read_text(encoding="utf-8"))
        for numero, celda in enumerate(cuaderno["cells"], 1):
            if celda["cell_type"] != "code":
                continue
            codigo = "".join(celda["source"])
            try:
                exec(compile(codigo, f"{archivo.name}:celda_{numero}", "exec"), entorno)
            except Exception:
                print(f"ERROR: módulo {archivo.name}, celda {numero}", file=sys.stderr)
                traceback.print_exc()
                return 1
    for csv in DATOS.glob("submission*.csv"):
        destino = SALIDA / csv.name
        destino.write_bytes(csv.read_bytes())
    print("\nTerminado. Submissions generadas disponibles en resultados/.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
