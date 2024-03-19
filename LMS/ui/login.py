from typing import Callable

from PyQt6.QtWidgets import QDialog, QMessageBox, QPushButton, QLineEdit, QLabel
from PyQt6 import uic

from ..config import CONFIG
from ..db_session import Session

class Login_UI(QDialog):
    lineEditUsername: QLineEdit
    lineEditPassword: QLineEdit

    labelVersion: QLabel
    labelConfig: QLabel

    pushButtonLogin: QPushButton

    callback: Callable

    DESIGNER_FILE: str = "login.ui"

    def __init__(self, callback: Callable) -> None:
        super().__init__()
        uic.load_ui.loadUi(CONFIG.LMS.DESIGNER_FILES.joinpath(self.DESIGNER_FILE), self)

        self.callback = callback

        self.lineEditUsername.setText(CONFIG.USER.USERNAME)
        self.lineEditPassword.setText(CONFIG.USER.PASSWORD)

        config_info: str

        if CONFIG.LMS.CONFIG_FILE is None:
            config_info = f"HOST:{CONFIG.REMOTE.HOST} PORT:{CONFIG.REMOTE.PORT} DATABASE:{CONFIG.REMOTE.DATABASE}"
        else:
            config_info = f"LOAD FROM {CONFIG.LMS.CONFIG_FILE.name}"

        self.labelVersion.setText(CONFIG.LMS.VERSION)
        self.labelConfig.setText(config_info)

        self.pushButtonLogin.clicked.connect(self.pushButtonLoginClicked)

    def pushButtonLoginClicked(self) -> None:
        CONFIG.USER.USERNAME = self.lineEditUsername.text()

        if CONFIG.USER.USERNAME == "":
            QMessageBox.warning(self, "Error", "Username cannot be empty")
            return

        CONFIG.USER.PASSWORD = self.lineEditPassword.text()

        try:
            Session.init()
            self.callback()
        except Exception as err:
            QMessageBox.warning(self, "Error", str(err))
