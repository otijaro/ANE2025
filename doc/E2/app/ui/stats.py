from pathlib import Path
import re

# Cargar el archivo original
with open("h_simulador_python_ane_sprint1.py", "r", encoding="utf-8") as f:
    original_code = f.read()

# Extraer la clase StatsWidget completa
pattern = r"(class StatsWidget\(.*?\n(?: {4}.*\n)+)"
match = re.search(pattern, original_code)
if match:
    stats_code = match.group(0)
else:
    raise ValueError("No se pudo encontrar la clase StatsWidget")

# Crear el archivo ui/stats.py y guardar la clase allí
Path("h_simulador/ui").mkdir(parents=True, exist_ok=True)
with open("h_simulador/ui/stats.py", "w", encoding="utf-8") as f:
    f.write("from PySide6 import QtWidgets, QtGui, QtCore\n")
    f.write("from h_simulador.core.entities import FMTransmitter\n")
    f.write("from typing import Optional\n\n")
    f.write(stats_code)

# Confirmar que se creó correctamente
print("Clase StatsWidget extraída y guardada en h_simulador/ui/stats.py")