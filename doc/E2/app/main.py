
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
import sys

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()