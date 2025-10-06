from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from ..controller import SceneController

class HUDWidget(QtWidgets.QWidget):
    def __init__(self, controller: SceneController, parent=None):
        super().__init__(parent)
        self.controller = controller

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.text = QtWidgets.QLabel()
        self.text.setStyleSheet("color:#d1e8ff;")
        # ✅ Usa bandera de QtCore, no un int
        self.text.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(self.text)

        self.controller.sceneChanged.connect(self.update_hud)
        self.controller.hudChanged.connect(self.update_hud)
        self.update_hud()

    def update_hud(self):
        self.text.setTextFormat(QtCore.Qt.RichText)  # permitir HTML

        av = self.controller.get_aircraft()
        if not av:
            self.text.setText("<span style='color:#ff8080'>No hay avión en la escena.</span>")
            return

        rows = self.controller.fspl_all_to_aircraft()
        col_label = "#0549be"   # color de etiquetas
        col_val   = "#d66910"   # color de valores (CORREGIDO: sin '}' extra)

        if rows:
            nearest = min(rows, key=lambda r: r["d_km"])
            txt = (
                f"<div style='font-family:monospace'>"
                f"<span style='color:{col_label}'>Avión:</span> "
                f"<span style='color:{col_val}'>({av.x_km:.2f} km, {av.y_km:.2f} km, h={av.h_km:.2f} km)</span><br>"
                f"<span style='color:{col_label}'>Más cercana:</span> "
                f"<span style='color:{col_val}'>{nearest['nombre']} → d={nearest['d_km']:.2f} km, "
                f"f={nearest['f_MHz']:.2f} MHz, FSPL={nearest['fspl_dB']:.2f} dB</span>"
                f"</div>"
            )
        else:
            txt = (
                f"<div style='font-family:monospace'>"
                f"<span style='color:{col_label}'>Avión:</span> "
                f"<span style='color:{col_val}'>({av.x_km:.2f} km, {av.y_km:.2f} km, h={av.h_km:.2f} km)</span><br>"
                f"<span style='color:#ff8080'>Sin emisoras.</span>"
                f"</div>"
            )

        self.text.setText(txt)

