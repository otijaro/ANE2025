from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from ..controller import SceneController

class StatsWidget(QtWidgets.QWidget):
    """Resumen global + pérdidas por emisora hacia Avión y Torre."""
    def __init__(self, controller: SceneController, parent=None):
        super().__init__(parent)
        self.controller = controller
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.label = QtWidgets.QLabel()
        # Cambia aquí el color (elige uno de alto contraste)
        # Ejemplos: #ffd166 (ámbar), #9ae6b4 (verde), #7aa2f7 (azulado)
        self.label.setStyleSheet("color:#0a0a04; font-family:monospace;")
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(self.label)

        self.controller.sceneChanged.connect(self.update_stats)
        self.controller.hudChanged.connect(self.update_stats)
        self.update_stats()

    def set_text_color(self, color_css: str):
        self.label.setStyleSheet(f"color:{color_css}; font-family:monospace;")

    '''def update_stats(self):
        overview = self.controller.stats_overview()
        if overview["count"] == 0:
            self.label.setText("No hay emisoras.")
            return
        best = overview["best_fm"]

        lines = []
        lines.append(f"N° emisoras: {overview['count']}")
        lines.append(f"Potencia total: {overview['p_total_kW']:.2f} kW")
        lines.append(f"FSPL min/avg/max (FM→Avión): {overview['fspl_min']:.2f} / {overview['fspl_avg']:.2f} / {overview['fspl_max']:.2f} dB")
        lines.append(f"Mejor FM→Avión: {best['nombre']} (d={best['d_km']:.2f} km, FSPL={best['fspl_dB']:.2f} dB)")
        lines.append("")

        rows_av = self.controller.fspl_all_to_aircraft()
        tower = self.controller.get_control_tower()
        rows_tw = self.controller.fspl_all_to_target(tower) if tower else []
        map_tw = {r["id"]: r for r in rows_tw} if rows_tw else {}

        if tower:
            lines.append("Por emisora (FM):       d_avión  FSPL_avión    d_torre  FSPL_torre   f(MHz)  P(kW)")
        else:
            lines.append("Por emisora (FM):       d_avión  FSPL_avión   f(MHz)  P(kW)")

        for r in rows_av:
            nombre = r["nombre"]; d_av = r["d_km"]; L_av = r["fspl_dB"]; fMHz = r["f_MHz"]; p_kW = r["p_kW"]
            if tower:
                tw = map_tw.get(r["id"])
                if tw:
                    d_tw = tw["d_km"]; L_tw = tw["fspl_dB"]
                    lines.append(f" - {nombre:<16}  {d_av:>6.2f}   {L_av:>10.2f}   {d_tw:>6.2f}   {L_tw:>10.2f}   {fMHz:>6.2f}  {p_kW:>5.2f}")
                else:
                    lines.append(f" - {nombre:<16}  {d_av:>6.2f}   {L_av:>10.2f}   {'--':>6}   {'--':>10}   {fMHz:>6.2f}  {p_kW:>5.2f}")
            else:
                lines.append(f" - {nombre:<16}  {d_av:>6.2f}   {L_av:>10.2f}   {fMHz:>6.2f}  {p_kW:>5.2f}")

        self.label.setText("\n".join(lines))'''
    def update_stats(self):
        overview = self.controller.stats_overview()
        lines = []
        if overview["count"] == 0:
            self.label.setText("No hay emisoras.")
            return
        
        best = overview["best_fm"]
        lines.append(f"N° emisoras: {overview['count']}")
        lines.append(f"Potencia total: {overview['p_total_kW']:.2f} kW")
        lines.append(f"FSPL min/avg/max (FM→Avión): {overview['fspl_min']:.2f} / {overview['fspl_avg']:.2f} / {overview['fspl_max']:.2f} dB")
        lines.append(f"Mejor FM→Avión: {best['nombre']} (d={best['d_km']:.2f} km, FSPL={best['fspl_dB']:.2f} dB)")
        lines.append("")  # espacio en blanco

        # Ahora muestra también FSPL hacia la Torre
        tower = self.controller.get_control_tower()
        if tower:
            rows_tw = self.controller.fspl_all_to_target(tower)
            for fm in rows_tw:
                lines.append(f" - {fm['nombre']} → d={fm['d_km']:.2f} km, FSPL a Torre={fm['fspl_dB']:.2f} dB")

        # Finaliza la impresión
        self.label.setText("\n".join(lines))
