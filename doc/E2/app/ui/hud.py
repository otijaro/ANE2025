from pathlib import Path

# Ruta de salida
output_path = Path("h_simulador/ui/hud.py")
output_path.parent.mkdir(parents=True, exist_ok=True)

# Contenido de la clase HUDWidget extraída del archivo original
hud_code = '''from PySide6 import QtCore, QtGui, QtWidgets
from core.entities import Aircraft, FMTransmitter
from core.controller import SceneController

class HUDWidget(QtWidgets.QWidget):
    def __init__(self, controller: SceneController, parent=None):
        super().__init__(parent)
        self.controller = controller

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Window, QtGui.QColor("#101826"))
        self.setPalette(pal)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.hud_label = QtWidgets.QLabel("HUD")
        self.hud_label.setStyleSheet("color: #d1e8ff; font-size: 14px;")
        self.hud_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.hud_text = QtWidgets.QLabel("")
        self.hud_text.setStyleSheet("color: #d1e8ff;")
        self.hud_text.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        layout.addWidget(self.hud_label)
        layout.addWidget(self.hud_text)

        self.update_hud()

        self.controller.sceneChanged.connect(self.update_hud)

    def update_hud(self):
        avion = self.controller.get_entity("AVION1")
        fm = self.controller.get_entity("FM_1")  # Usamos FM_1 como ejemplo

        if avion and fm:
            dist_km = self.controller.distance_km("AVION1", "FM_1")
            coords_avion = f"Avi\\u00f3n: ({avion.x_km:.2f} km, {avion.y_km:.2f} km)"
            coords_fm = f"FM_1: ({fm.x_km:.2f} km, {fm.y_km:.2f} km)"
            text = f\"\"\"{coords_avion}
{coords_fm}
Distancia entre AVION1 y FM_1: {dist_km:.2f} km\"\"\"
            self.hud_text.setText(text)
'''

# Guardar el archivo
output_path.write_text(hud_code, encoding="utf-8")
print(f"Archivo guardado en: {output_path}")