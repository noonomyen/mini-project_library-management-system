from sys import argv

from PyQt6.QtWidgets import QApplication

from .config import CONFIG
from .args import argument_parser
from .ui import MainWindow_UI

def main() -> int:
    argument_parser()

    app = QApplication(argv)

    app.setApplicationDisplayName("Library Management System")
    app.setApplicationName("Library Management System")
    app.setApplicationVersion(CONFIG.LMS.VERSION)

    MainWindowForm = MainWindow_UI()

    return app.exec()
