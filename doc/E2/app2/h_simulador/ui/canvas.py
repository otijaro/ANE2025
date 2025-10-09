from __future__ import annotations
import math
from typing import Optional, Tuple
from PySide6 import QtCore, QtGui, QtWidgets

from ..controller_qt import SceneController
from ..models import FMTransmitter, Aircraft, ControlTower, Entity
from ..utils import frange, UnitsConverter

class CanvasWidget(QtWidgets.QWidget):
    requestHudUpdate = QtCore.Signal()

    def __init__(self, controller: SceneController, units: UnitsConverter, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.units = units
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self._show_grid = True
        self._show_propagation = True
        self._show_propagation_labels = True

        self._drag_entity_id: Optional[str] = None
        self._last_mouse_pos = QtCore.QPoint(0,0)

        self.controller.sceneChanged.connect(self.update)
        self.controller.hudChanged.connect(self.requestHudUpdate.emit)
        self._update_minimum_size()

    # ---- toggles
    def toggle_grid(self): self._show_grid = not self._show_grid; self.update()
    def toggle_propagation(self): self._show_propagation = not self._show_propagation; self.update()
    def toggle_propagation_labels(self): self._show_propagation_labels = not self._show_propagation_labels; self.update()

    def _update_minimum_size(self):
        w = int(self.controller.scene.ancho_km * self.units.km_to_px)
        h = int(self.controller.scene.alto_km * self.units.km_to_px)
        self.setMinimumSize(w+1, h+1)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_G: self.toggle_grid()
        elif event.key() == QtCore.Qt.Key_R: self.controller.reset_scene()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self); painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QtGui.QColor("#0b1020"))
        scene_w_px = int(self.controller.scene.ancho_km * self.units.km_to_px)
        scene_h_px = int(self.controller.scene.alto_km * self.units.km_to_px)
        scene_rect = QtCore.QRect(0,0,scene_w_px,scene_h_px)

        def world_to_screen_px(x_km: float, y_km: float) -> Tuple[int,int]:
            sx = int(round(x_km * self.units.km_to_px))
            sy = int(round(scene_h_px - y_km * self.units.km_to_px))
            return sx, sy

        # marco
        pen_scene = QtGui.QPen(QtGui.QColor("#8a9bb6")); pen_scene.setWidth(2)
        painter.setPen(pen_scene); painter.drawRect(scene_rect)

        # grilla
        if self._show_grid:
            grid_pen = QtGui.QPen(QtGui.QColor(255,255,255,40)); grid_pen.setWidth(1)
            painter.setPen(grid_pen)
            for xk in frange(0.0, self.controller.scene.ancho_km, 5.0):
                sx,_ = world_to_screen_px(xk, 0); painter.drawLine(sx,0,sx,scene_h_px)
            for yk in frange(0.0, self.controller.scene.alto_km, 5.0):
                _,sy = world_to_screen_px(0, yk); painter.drawLine(0,sy,scene_w_px,sy)

        # entidades
        av = self.controller.get_aircraft()
        for e in self.controller.scene.entities:
            sx, sy = world_to_screen_px(e.x_km, e.y_km)
            if isinstance(e, FMTransmitter): self._draw_fm(painter, sx, sy, e)
            elif isinstance(e, Aircraft):   self._draw_aircraft(painter, sx, sy, e)
            elif isinstance(e, ControlTower): self._draw_tower(painter, sx, sy, e)
            else: self._draw_generic(painter, sx, sy, e)

        # LOS FM→Avión
        if self._show_propagation and av:
            pen = QtGui.QPen(QtGui.QColor("#ff6347")); pen.setWidth(2)
            painter.setPen(pen)
            for fm in self.controller.get_all_fms():
                sx1, sy1 = world_to_screen_px(fm.x_km, fm.y_km)
                sx2, sy2 = world_to_screen_px(av.x_km, av.y_km)
                painter.drawLine(sx1, sy1, sx2, sy2)
                if self._show_propagation_labels:
                    midx = (sx1+sx2)//2; midy = (sy1+sy2)//2
                    d_km = math.hypot(fm.x_km - av.x_km, fm.y_km - av.y_km)
                    f_mhz = fm.f_Hz/1e6
                    fspl  = SceneController.compute_fspl_db(d_km, f_mhz)
                    self._draw_label(painter, midx, midy-16, f"{fm.nombre}: {d_km:.2f} km / {fspl:.1f} dB")

        painter.end()

    def world_to_screen_px(self, x_km: float, y_km: float) -> Tuple[int, int]:
        """Convierte coordenadas (km) a coordenadas en píxeles en el widget."""
        scene_w_px = int(self.controller.scene.ancho_km * self.units.km_to_px)
        scene_h_px = int(self.controller.scene.alto_km * self.units.km_to_px)
        sx = int(round(x_km * self.units.km_to_px))
        sy = int(round(scene_h_px - y_km * self.units.km_to_px))
        return sx, sy

    # helpers dibujo
    def _draw_label(self, painter: QtGui.QPainter, x:int, y:int, text:str, bg="#102a43"):
        metrics = painter.fontMetrics()
        w = metrics.horizontalAdvance(text)+10; h = metrics.height()+6
        rect = QtCore.QRect(x-w//2, y-h//2, w, h)
        painter.fillRect(rect, QtGui.QColor(bg))
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff")))
        painter.drawRect(rect)
        painter.drawText(rect, QtCore.Qt.AlignCenter, text)

    def _draw_fm(self, painter, x, y, e: FMTransmitter):
        r=10; painter.setBrush(QtGui.QColor("#f0a500"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffe08a"),2))
        painter.drawEllipse(QtCore.QPoint(x,y), r, r)
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"))); painter.drawText(x-22, y-16, e.nombre)

    def _draw_aircraft(self, painter, x, y, e: Aircraft):
        path = QtGui.QPainterPath()
        path.moveTo(x, y-14); path.lineTo(x-10, y+8); path.lineTo(x+10, y+8); path.closeSubpath()
        painter.fillPath(path, QtGui.QColor("#3fa9f5"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"))); painter.drawText(x-18, y-18, "Avión")

    def _draw_tower(self, painter, x, y, e: ControlTower):
        painter.setBrush(QtGui.QColor("#9aa5b1"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#e2e8f0"), 2))
        painter.drawRect(x-8, y-8, 16, 16)  # Rectángulo base de la torre
        painter.drawLine(x, y-8, x, y-24)  # Línea hacia arriba
        painter.drawLine(x, y-24, x-6, y-14)  # Soporte izquierdo
        painter.drawLine(x, y-24, x+6, y-14)  # Soporte derecho
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff")))
        painter.drawText(x-22, y-28, "Torre")


    def _draw_generic(self, painter, x, y, e: Entity):
        painter.setBrush(QtGui.QColor("#cccccc"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff")))
        painter.drawEllipse(QtCore.QPoint(x,y), 6, 6); painter.drawText(x-20, y-12, e.nombre)

    # --- arrastre ---
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.setFocus()
            self._last_mouse_pos = event.position().toPoint()
            clicked_id = self._hit_test(self._last_mouse_pos)
            if clicked_id:
                self._drag_entity_id = clicked_id

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._drag_entity_id:
            pos = event.position().toPoint()
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()
            self._last_mouse_pos = pos
            dx_km = dx / self.units.km_to_px
            dy_km = -dy / self.units.km_to_px
            e = self.controller.get_entity(self._drag_entity_id)
            if e:
                self.controller.set_position(e.id, e.x_km + dx_km, e.y_km + dy_km)



    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton: self._drag_entity_id = None

    def _hit_test(self, p: QtCore.QPoint):
        sel_radius_px = 14
        scene_h_px = int(self.controller.scene.alto_km * self.units.km_to_px)

        def world_to_screen_px(x_km: float, y_km: float):
            sx = int(round(x_km * self.units.km_to_px))
            sy = int(round(scene_h_px - y_km * self.units.km_to_px))
            return sx, sy

        for e in reversed(self.controller.scene.entities or []):
            # Permitimos torre
            sx, sy = world_to_screen_px(e.x_km, e.y_km)
            if abs(p.x()-sx) <= sel_radius_px and abs(p.y()-sy) <= sel_radius_px:
                return e.id
        return None


    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Fondo: Dibujamos imagen de mapa
        try:
            map_image = QtGui.QImage("path/to/your/map/image.png")
            painter.drawImage(0, 0, map_image)  # Dibujamos el mapa completo
        except Exception as e:
            print(f"Error al cargar la imagen del mapa: {e}")

        # Dibujo de las entidades (emisoras, torre, avión)
        for e in self.controller.scene.entities:
            sx, sy = self.world_to_screen_px(e.x_km, e.y_km)  # Calcula la posición correcta en píxeles
            if isinstance(e, FMTransmitter):
                self._draw_fm(painter, sx, sy, e)
            elif isinstance(e, Aircraft):
                self._draw_aircraft(painter, sx, sy, e)
            elif isinstance(e, ControlTower):
                self._draw_tower(painter, sx, sy, e)  # Aquí dibujamos la torre
            else:
                self._draw_generic(painter, sx, sy, e)

        # Líneas de propagación FM → Avión (con etiquetas por línea)
        av = self.controller.get_aircraft()
        if self._show_propagation and av:
            line_pen = QtGui.QPen(QtGui.QColor("#ff6347"))
            line_pen.setWidth(2)  # Un poco más gruesa para que se vea bien
            painter.setPen(line_pen)
            for fm in self.controller.get_all_fms():
                sx1, sy1 = self.world_to_screen_px(fm.x_km, fm.y_km)
                sx2, sy2 = self.world_to_screen_px(av.x_km, av.y_km)
                painter.drawLine(sx1, sy1, sx2, sy2)

                if self._show_propagation_labels:
                    # Etiqueta en el punto medio: distancia y FSPL
                    midx = (sx1 + sx2) // 2
                    midy = (sy1 + sy2) // 2
                    d_km = math.hypot(fm.x_km - av.x_km, fm.y_km - av.y_km)
                    f_mhz = fm.f_Hz / 1e6
                    fspl = SceneController.compute_fspl_db(d_km, f_mhz)
                    self._draw_label(painter, midx, midy - 16, f"{fm.nombre}: {d_km:.2f} km / {fspl:.1f} dB")

        painter.end()
