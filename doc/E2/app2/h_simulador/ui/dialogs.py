from __future__ import annotations
from PySide6 import QtWidgets
from ..models import Scene

class AddFmDialog(QtWidgets.QDialog):
    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar emisora")
        self.scene = scene
        form = QtWidgets.QFormLayout(self)

        self.ed_nombre = QtWidgets.QLineEdit("FM_1")
        self.ed_f = QtWidgets.QDoubleSpinBox(); self.ed_f.setRange(10.0, 10000.0); self.ed_f.setDecimals(3); self.ed_f.setValue(100.000)
        self.ed_p = QtWidgets.QDoubleSpinBox(); self.ed_p.setRange(0.001, 1000.0); self.ed_p.setDecimals(3); self.ed_p.setValue(10.000)
        self.ed_x = QtWidgets.QDoubleSpinBox(); self.ed_x.setRange(0.0, self.scene.ancho_km); self.ed_x.setDecimals(3); self.ed_x.setValue(self.scene.ancho_km*0.3)
        self.ed_y = QtWidgets.QDoubleSpinBox(); self.ed_y.setRange(0.0, self.scene.alto_km); self.ed_y.setDecimals(3); self.ed_y.setValue(self.scene.alto_km*0.25)
        self.ed_h = QtWidgets.QDoubleSpinBox(); self.ed_h.setRange(0.0, 10.0); self.ed_h.setDecimals(3); self.ed_h.setValue(0.100)

        form.addRow("Nombre:", self.ed_nombre)
        form.addRow("Frecuencia (MHz):", self.ed_f)
        form.addRow("Potencia (kW):", self.ed_p)
        form.addRow("X (km):", self.ed_x)
        form.addRow("Y (km):", self.ed_y)
        form.addRow("Altura (km):", self.ed_h)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_values(self):
        if self.exec() != QtWidgets.QDialog.Accepted: return None
        return {"nombre": self.ed_nombre.text().strip() or "FM",
                "f_MHz": float(self.ed_f.value()),
                "p_kW": float(self.ed_p.value()),
                "x_km": float(self.ed_x.value()),
                "y_km": float(self.ed_y.value()),
                "h_km": float(self.ed_h.value())}
