from typing import Callable, Optional
from copy import copy

from PyQt6.QtWidgets import QWidget, QPushButton, QLineEdit, QMessageBox
from PyQt6 import uic

from ..config import CONFIG
from ..lms_types import UserData

class UserEdit_UI(QWidget):
    lineEditPrefixName: QLineEdit
    lineEditFirstName: QLineEdit
    lineEditLastName: QLineEdit
    lineEditEmail: QLineEdit
    lineEditPhone: QLineEdit
    lineEditAddress: QLineEdit
    pushButtonSave: QPushButton

    Callback = Callable[[UserData, Optional[UserData]], bool]
    callback_func: Callback
    _closeEvent: Optional[Callable[["UserEdit_UI"], None]]

    old_data: Optional[UserData]

    DESIGNER_FILE: str = "user-edit.ui"

    def __init__(self, callback_func: Callback, old_data: Optional[UserData] = None, _closeEvent: Optional[Callable[["UserEdit_UI"], None]] = None) -> None:
        super().__init__()
        uic.load_ui.loadUi(CONFIG.LMS.DESIGNER_FILES.joinpath(self.DESIGNER_FILE), self)

        self.pushButtonSave.clicked.connect(self.pushButtonSaveClicked)

        self.callback_func = callback_func
        self._closeEvent = _closeEvent
        self.old_data = copy(old_data)

        if old_data is None:
            self.LoadEditData(UserData(None, "", "", "", "", "", ""))
        else:
            self.LoadEditData(old_data)

        self.lineEditPrefixName.returnPressed.connect(lambda: self.lineEditFirstName.setFocus())
        self.lineEditFirstName.returnPressed.connect(lambda: self.lineEditLastName.setFocus())
        self.lineEditLastName.returnPressed.connect(lambda: self.lineEditEmail.setFocus())
        self.lineEditEmail.returnPressed.connect(lambda: self.lineEditPhone.setFocus())
        self.lineEditPhone.returnPressed.connect(lambda: self.lineEditAddress.setFocus())
        self.lineEditAddress.returnPressed.connect(lambda: self.pushButtonSave.setFocus())

        self.show()

    def pushButtonSaveClicked(self) -> None:
        if self.lineEditFirstName.text().strip() == "":
            QMessageBox.warning(self, "Warning", "First name should not be empty.")
        elif self.lineEditFirstName.text().strip() == "":
            QMessageBox.warning(self, "Warning", "Last name should not be empty.")
        else:
            self.hide()
            if self.callback_func is not None:
                try:
                    data = self.DumpEditData()
                except Exception as err:
                    QMessageBox.warning(self, "Error", str(err))
                    return

                if self.callback_func(data, self.old_data) and self._closeEvent is not None:
                    self._closeEvent(self)
            else:
                QMessageBox.critical(self, "Runtime Error", "No callback function !")

    def LoadEditData(self, instance: UserData) -> None:
        self.lineEditPrefixName.setText(instance.prefixName if instance.prefixName else "")
        self.lineEditFirstName.setText(instance.firstName if instance.firstName else "")
        self.lineEditLastName.setText(instance.lastName if instance.lastName else "")
        self.lineEditEmail.setText(instance.email if instance.email else "")
        self.lineEditPhone.setText(instance.phone if instance.phone else "")
        self.lineEditAddress.setText(instance.address if instance.address else "")

    def DumpEditData(self) -> UserData:
        prefixName = self.lineEditPrefixName.text().strip()
        firstName = self.lineEditFirstName.text().strip()
        lastName = self.lineEditLastName.text().strip()
        email = self.lineEditEmail.text().strip()
        phone = self.lineEditPhone.text().strip()
        address = self.lineEditAddress.text().strip()

        return UserData(
            userId=(self.old_data.userId if self.old_data else None),
            prefixName=(prefixName if prefixName != "" else None),
            firstName=(firstName),
            lastName=(lastName),
            email=(email if email != "" else None),
            phone=(phone if phone != "" else None),
            address=(address if address != "" else None)
        )
