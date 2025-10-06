from __future__ import annotations
import sys
from PySide6 import QtWidgets
from h_simulador.ui.main_window import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
