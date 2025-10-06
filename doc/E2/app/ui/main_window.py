from pathlib import Path

# Ruta de salida para el archivo main_window.py
output_path = Path("h_simulador/ui/main_window.py")

# Cargar el contenido del archivo original
with open("h_simulador_python_ane_sprint1.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extraer la clase MainWindow completa
start_index = None
end_index = None
for i, line in enumerate(lines):
    if "class MainWindow(QtWidgets.QMainWindow):" in line:
        start_index = i
    elif start_index is not None and line.strip().startswith("def main()"):
        end_index = i
        break

# Verificar que se encontró la clase
if start_index is not None and end_index is not None:
    main_window_lines = lines[start_index:end_index]
else:
    raise ValueError("No se pudo encontrar la clase MainWindow en el archivo original.")

# Guardar el contenido extraído en el nuevo archivo
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.writelines(main_window_lines)

print(f"Clase MainWindow extraída y guardada en {output_path}")