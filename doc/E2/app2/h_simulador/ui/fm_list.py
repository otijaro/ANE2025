from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from ..controller import SceneController

class FMListWidget(QtWidgets.QWidget):
    COL_NOMBRE=0; COL_F=1; COL_P=2; COL_D=3; COL_FSPL=4

    def __init__(self, controller: SceneController, parent=None):
        super().__init__(parent)
        self.controller = controller; self._updating = False
        lay = QtWidgets.QVBoxLayout(self); self.setLayout(lay)

        title = QtWidgets.QLabel("Emisoras (doble clic para editar)")
        title.setStyleSheet("color:#d1e8ff; font-weight:bold;")
        lay.addWidget(title)

        self.table = QtWidgets.QTableWidget(0,5,self)
        self.table.setHorizontalHeaderLabels(["Nombre","f (MHz)","P (kW)","d (km)","FSPL (dB)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked)
        lay.addWidget(self.table)

        self.table.cellChanged.connect(self._on_cell_changed)
        self.controller.sceneChanged.connect(self.refresh_table)
        self.controller.hudChanged.connect(self.refresh_table)
        self.refresh_table()

    def refresh_table(self):
        self._updating = True
        rows = self.controller.fspl_all_to_aircraft()
        self.table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            it0 = QtWidgets.QTableWidgetItem(r["nombre"]); it0.setData(QtCore.Qt.UserRole, r["id"])
            self.table.setItem(i, self.COL_NOMBRE, it0)
            it1 = QtWidgets.QTableWidgetItem(f"{r['f_MHz']:.3f}"); self.table.setItem(i, self.COL_F, it1)
            it2 = QtWidgets.QTableWidgetItem(f"{r['p_kW']:.3f}"); self.table.setItem(i, self.COL_P, it2)
            it3 = QtWidgets.QTableWidgetItem(f"{r['d_km']:.3f}"); it3.setFlags(it3.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(i, self.COL_D, it3)
            it4 = QtWidgets.QTableWidgetItem(f"{r['fspl_dB']:.2f}"); it4.setFlags(it4.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(i, self.COL_FSPL, it4)
        self._updating = False

    def _on_cell_changed(self, row:int, col:int):
        if self._updating: return
        id_item = self.table.item(row, self.COL_NOMBRE)
        if not id_item: return
        fm_id = id_item.data(QtCore.Qt.UserRole)
        try:
            if col == self.COL_NOMBRE:
                self.controller.update_fm_params(fm_id=fm_id, nombre=self.table.item(row,col).text().strip())
            elif col == self.COL_F:
                self.controller.update_fm_params(fm_id=fm_id, f_MHz=float(self.table.item(row,col).text()))
            elif col == self.COL_P:
                self.controller.update_fm_params(fm_id=fm_id, p_kW=float(self.table.item(row,col).text()))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Valor inválido", str(e))
        finally:
            self.refresh_table()
