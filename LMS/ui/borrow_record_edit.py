from typing import Callable, Optional
from enum import Enum
from copy import copy
from datetime import datetime

from PyQt6 import uic
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QWidget, QPushButton, QCheckBox, QDateTimeEdit, QLineEdit, QMessageBox

from ..config import CONFIG
from ..lms_types import BookBorrowHistoryData

class BorrowRecordEdit_UI(QWidget):
    lineEditUserID: QLineEdit
    lineEditBookID: QLineEdit
    dateTimeEditBorrowed: QDateTimeEdit
    dateTimeEditReturned: QDateTimeEdit
    checkBoxReturned: QCheckBox
    checkBoxUseCurrentTime: QCheckBox
    pushButtonSave: QPushButton
    pushButtonRemove: QPushButton

    class BorrowRecordEditAction(Enum):
        SAVE = 1
        REMOVE = 2

    Callback = Callable[[BorrowRecordEditAction, Optional[BookBorrowHistoryData], Optional[BookBorrowHistoryData]], bool]
    callback_func: Callback
    _closeEvent: Optional[Callable[["BorrowRecordEdit_UI"], None]]

    old_data: BookBorrowHistoryData

    DESIGNER_FILE: str = "borrow-record-edit.ui"

    def __init__(self, callback_func: Callback, old_data: BookBorrowHistoryData, _closeEvent: Optional[Callable[["BorrowRecordEdit_UI"], None]] = None) -> None:
        super().__init__()
        uic.load_ui.loadUi(CONFIG.LMS.DESIGNER_FILES.joinpath(self.DESIGNER_FILE), self)

        self.callback_func = callback_func
        self._closeEvent = _closeEvent
        self.old_data = copy(old_data)

        self.lineEditUserID.setValidator(QIntValidator())
        self.lineEditBookID.setValidator(QIntValidator())
        self.pushButtonSave.clicked.connect(self.pushButtonSaveClicked)
        self.pushButtonRemove.clicked.connect(self.pushButtonRemoveClicked)
        self.checkBoxUseCurrentTime.clicked.connect(self.checkbox_toggled)
        self.checkBoxReturned.clicked.connect(self.checkbox_toggled)
        self.lineEditUserID.returnPressed.connect(lambda: self.lineEditBookID.setFocus())

        self.LoadEditData(old_data)
        self.checkbox_toggled()
        self.show()

    def pushButtonSaveClicked(self) -> None:
        if self.lineEditUserID.text().strip() == "":
            QMessageBox.warning(self, "Warning", "User ID should not be empty.")
        elif self.lineEditBookID.text().strip() == "":
            QMessageBox.warning(self, "Warning", "Book ID should not be empty.")
        else:
            self.hide()
            if self.callback_func is not None:
                try:
                    data = self.DumpEditData()
                except Exception as err:
                    QMessageBox.warning(self, "Error", str(err))
                    return

                if self.callback_func(self.BorrowRecordEditAction.SAVE, data, self.old_data) and self._closeEvent is not None:
                    self._closeEvent(self)
            else:
                QMessageBox.critical(self, "Runtime Error", "No callback function !")

    def pushButtonRemoveClicked(self) -> None:
        self.hide()
        if self.callback_func is not None:
            if self.callback_func(self.BorrowRecordEditAction.REMOVE, None, None) and self._closeEvent is not None:
                self._closeEvent(self)
        else:
            QMessageBox.critical(self, "Runtime Error", "No callback function !")

    def checkbox_toggled(self):
        CurrentTimeChecked = self.checkBoxUseCurrentTime.isChecked()
        ReturnedChecked = self.checkBoxReturned.isChecked()

        if ReturnedChecked:
            self.dateTimeEditReturned.setEnabled(not CurrentTimeChecked)
            self.dateTimeEditReturned.setDateTime(datetime.now())
        else:
            self.dateTimeEditReturned.setEnabled(False)

    def LoadEditData(self, instance: BookBorrowHistoryData) -> None:
        self.lineEditUserID.setText(str(instance.userId))
        self.lineEditBookID.setText(str(instance.bookId))
        self.dateTimeEditBorrowed.setDateTime(instance.borrowed)

        if instance.returned:
            self.dateTimeEditReturned.setDateTime(instance.returned)

        self.checkBoxReturned.setChecked(instance.returned is not None)
        self.checkBoxUseCurrentTime.setChecked(False)

    def DumpEditData(self) -> BookBorrowHistoryData:
        userId = self.lineEditUserID.text().strip()
        bookId = self.lineEditBookID.text().strip()
        borrowed = self.dateTimeEditBorrowed.dateTime().toPyDateTime()
        returned = self.dateTimeEditReturned.dateTime().toPyDateTime() if self.checkBoxReturned.isChecked() else None

        return BookBorrowHistoryData(
            historyId=self.old_data.historyId,
            bookId=int(bookId),
            userId=int(userId),
            borrowed=borrowed,
            returned=returned,
            userName=self.old_data.userName,
            bookTitle=self.old_data.bookTitle
        )
