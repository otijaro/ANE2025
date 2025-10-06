from pathlib import Path

# Ruta de destino para guardar canvas.py
output_path = Path("h_simulador/ui/canvas.py")

# Cargar el archivo original
with open("h_simulador_python_ane_sprint1.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Buscar la clase CanvasWidget y extraer su contenido completo
canvas_lines = []
inside_canvas = False
indent_level = None

for line in lines:
    if line.strip().startswith("class CanvasWidget("):
        inside_canvas = True
        indent_level = len(line) - len(line.lstrip())
    if inside_canvas:
        canvas_lines.append(line)
        # Detectar fin de clase por indentación
        if line.strip() == "" and len(canvas_lines) > 10:
            next_index = lines.index(line) + 1
            if next_index < len(lines):
                next_line = lines[next_index]
                if len(next_line.strip()) > 0 and len(next_line) - len(next_line.lstrip()) <= indent_level:
                    break

# Guardar el contenido extraído en canvas.py
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    f.writelines(canvas_lines)

# Confirmar resultado
print(f"Archivo canvas.py creado con {len(canvas_lines)} líneas.")