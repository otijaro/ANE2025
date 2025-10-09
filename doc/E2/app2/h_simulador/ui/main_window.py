from __future__ import annotations
import json
from PySide6 import QtCore, QtGui, QtWidgets

from ..models import Scene, Aircraft, FMTransmitter
from ..controller_qt import SceneController
from ..utils import UnitsConverter
from .canvas import CanvasWidget
from .stats import StatsWidget
from .fm_list import FMListWidget
from .hud import HUDWidget
from .dialogs import AddFmDialog

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("H.SimuladorPythonANE — Google Maps")

        # Configura la escena inicial y el controller
        scene = Scene(ancho_km=100.0, alto_km=60.0, frecuencia_Hz=100e6)
        avion = Aircraft(id="AVION1", nombre="Avión", x_km=50.0, y_km=30.0, h_km=2.0)
        fm1 = FMTransmitter(id="FM_1", nombre="FM_1", x_km=30.0, y_km=15.0, h_km=0.1, potencia_W=10e3, f_Hz=100e6)
        scene.entities.extend([avion, fm1])

        self.controller = SceneController(scene)
        self.controller.add_control_tower(5.0, 5.0, 0.05)

        self.units = UnitsConverter(km_to_px=10.0)

        # Crear Canvas (ahora con mapa)
        self.canvas = CanvasWidget(self.controller, self.units)
        self.setCentralWidget(self.canvas)

        # Añadir controles, como en el ejemplo anterior
        self.hud = HUDWidget(self.controller)
        dock_hud = QtWidgets.QDockWidget("HUD", self)
        dock_hud.setWidget(self.hud)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_hud)

        self.fm_list = FMListWidget(self.controller)
        dock_list = QtWidgets.QDockWidget("Listado de Emisoras", self)
        dock_list.setWidget(self.fm_list)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_list)

        self.stats = StatsWidget(self.controller)
        dock_stats = QtWidgets.QDockWidget("Estadísticas", self)
        dock_stats.setWidget(self.stats)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_stats)

        # Configurar menús y barra de herramientas (igual que antes)
        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self.resize(1200, 800)

    # --- acciones/menús/toolbar ---
    def _build_actions(self):
        self.act_save = QtGui.QAction("Guardar escena", self); self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.save_scene)

        self.act_load = QtGui.QAction("Cargar escena", self); self.act_load.setShortcut("Ctrl+O")
        self.act_load.triggered.connect(self.load_scene)

        self.act_reset = QtGui.QAction("Reiniciar (R)", self); self.act_reset.triggered.connect(self.controller.reset_scene)
        self.act_grid  = QtGui.QAction("Grilla (G)", self, checkable=True, checked=True); self.act_grid.triggered.connect(self.canvas.toggle_grid)
        self.act_propag = QtGui.QAction("Líneas de propagación", self, checkable=True, checked=True); self.act_propag.triggered.connect(self.canvas.toggle_propagation)
        self.act_propag_labels = QtGui.QAction("Etiquetas en líneas", self, checkable=True, checked=True); self.act_propag_labels.triggered.connect(self.canvas.toggle_propagation_labels)

        self.act_add_fm = QtGui.QAction("Agregar emisora…", self); self.act_add_fm.setShortcut("Ctrl+N")
        self.act_add_fm.triggered.connect(self._on_add_fm)

        self.act_add_tower = QtGui.QAction("Torre de control (fija)", self); self.act_add_tower.triggered.connect(self._on_add_tower)

    def _build_menu(self):
        m_file = self.menuBar().addMenu("&Archivo")
        m_file.addAction(self.act_save); m_file.addAction(self.act_load); m_file.addSeparator(); m_file.addAction(self.act_reset)

        m_view = self.menuBar().addMenu("&Ver")
        m_view.addAction(self.act_grid); m_view.addAction(self.act_propag); m_view.addAction(self.act_propag_labels)

        m_fm = self.menuBar().addMenu("&Emisoras"); m_fm.addAction(self.act_add_fm)
        m_insert = self.menuBar().addMenu("&Insertar"); m_insert.addAction(self.act_add_tower)

        m_help = self.menuBar().addMenu("A&yuda")
        about = QtGui.QAction("Acerca de", self); about.triggered.connect(self._show_about); m_help.addAction(about)

    def _build_toolbar(self):
        tb = self.addToolBar("Principal")
        tb.addAction(self.act_save); tb.addAction(self.act_load); tb.addSeparator()
        tb.addAction(self.act_reset); tb.addSeparator()
        tb.addAction(self.act_grid); tb.addAction(self.act_propag); tb.addAction(self.act_propag_labels); tb.addSeparator()
        tb.addAction(self.act_add_fm); tb.addAction(self.act_add_tower)

    # --- slots ---
    def _on_add_fm(self):
        dlg = AddFmDialog(self.controller.scene, self)
        vals = dlg.get_values()
        if not vals: return
        if not (0.0 <= vals["x_km"] <= self.controller.scene.ancho_km and 0.0 <= vals["y_km"] <= self.controller.scene.alto_km):
            QtWidgets.QMessageBox.warning(self, "Datos inválidos", "La posición debe estar dentro del área."); return
        if vals["f_MHz"] <= 0.0 or vals["p_kW"] <= 0.0:
            QtWidgets.QMessageBox.warning(self, "Datos inválidos", "Frecuencia y potencia deben ser > 0."); return
        self.controller.add_fm(nombre=vals["nombre"], x_km=vals["x_km"], y_km=vals["y_km"],
                               h_km=vals["h_km"], f_MHz=vals["f_MHz"], p_kW=vals["p_kW"])

    def _on_add_tower(self):
        if self.controller.has_control_tower():
            QtWidgets.QMessageBox.information(self, "Torre", "Ya hay una torre de control en la escena."); return
        cx = self.controller.scene.ancho_km - 5.0; cy = self.controller.scene.alto_km - 5.0
        self.controller.add_control_tower(cx, cy, 0.05)

    # --- persistencia ---
    def save_scene(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar escena", "escena.json", "JSON (*.json)")
        if not path: return
        try:
            with open(path,"w",encoding="utf-8") as f: json.dump(self.controller.scene.to_dict(), f, ensure_ascii=False, indent=2)
            QtWidgets.QMessageBox.information(self, "Guardar", "Escena guardada correctamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error al guardar", str(e))

    def load_scene(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Cargar escena", "escena.json", "JSON (*.json)")
        if not path: return
        try:
            with open(path,"r",encoding="utf-8") as f: data = json.load(f)
            self.controller.scene = Scene.from_dict(data)
            self.controller.sceneChanged.emit(); self.controller.hudChanged.emit()
            self.canvas.update(); QtWidgets.QMessageBox.information(self, "Cargar", "Escena cargada correctamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error al cargar", str(e))

    def _show_about(self):
        QtWidgets.QMessageBox.information(self, "Acerca de",
            "H.SimuladorPythonANE — Modular\n"
            "• Agregar emisoras 1 a 1\n"
            "• Torre de control fija\n"
            "• Líneas de propagación con etiquetas\n"
            "• Tabla editable (Nombre, f, P)\n"
            "• Estadística con pérdidas Avión y Torre\n"
            "• Guardar/Cargar escena (JSON)")
