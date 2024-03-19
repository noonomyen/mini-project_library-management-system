from typing import Callable, Optional
from copy import copy

from PyQt6.QtWidgets import QLabel, QFileDialog, QWidget, QPushButton, QLineEdit, QPlainTextEdit, QCheckBox, QMessageBox
from PyQt6 import uic

from ..config import CONFIG
from ..isbn import ISBN, ISBN10, ISBN13
from ..lms_types import BookData

class BookEdit_UI(QWidget):
    lineEditTitle: QLineEdit
    lineEditAuthor: QLineEdit
    lineEditPublication: QLineEdit
    lineEditISBN10: QLineEdit
    lineEditISBN13: QLineEdit
    plainTextEditDescription: QPlainTextEdit
    pushButtonSave: QPushButton
    pushButtonSelectImage: QPushButton
    labelDescriptionCharacterCounting: QLabel
    labelFileName: QLabel

    ISBN_CheckBox: tuple[QCheckBox, QCheckBox]
    ISBN_LineEdit: tuple[QLineEdit, QLineEdit]

    ISBN10_CURRECT: list[bool] = [False]
    ISBN13_CURRECT: list[bool] = [False]

    Callback = Callable[[BookData, Optional[BookData]], bool]
    callback_func: Callback
    CallbackCloseEvent = Optional[Callable[["BookEdit_UI"], None]]
    _closeEvent: CallbackCloseEvent

    imageFileName: Optional[str] = None
    old_data: Optional[BookData]

    DESIGNER_FILE: str = "book-edit.ui"

    def __init__(self, callback_func: Callback, old_data: Optional[BookData] = None, _closeEvent: CallbackCloseEvent = None) -> None:
        super().__init__()
        uic.load_ui.loadUi(CONFIG.LMS.DESIGNER_FILES.joinpath(self.DESIGNER_FILE), self)

        self.ISBNCheck(self.lineEditISBN10, ISBN10, self.ISBN10_CURRECT)
        self.ISBNCheck(self.lineEditISBN13, ISBN13, self.ISBN13_CURRECT)
        self.plainTextEditDescription.textChanged.connect(self.DescriptionCharacterCounting)
        self.pushButtonSelectImage.clicked.connect(self.getFile)
        self.pushButtonSave.clicked.connect(self.pushButtonSaveClicked)

        self.labelFileName.setText("")

        self.callback_func = callback_func
        self._closeEvent = _closeEvent
        self.old_data = copy(old_data)

        if old_data is None:
            self.LoadBookEditData(BookData(None, None, "", "", "", "", "", ""))
        else:
            self.LoadBookEditData(old_data)

        self.lineEditTitle.returnPressed.connect(lambda: self.lineEditAuthor.setFocus())
        self.lineEditAuthor.returnPressed.connect(lambda: self.lineEditPublication.setFocus())
        self.lineEditPublication.returnPressed.connect(lambda: self.lineEditISBN10.setFocus())
        self.lineEditISBN10.returnPressed.connect(lambda: self.lineEditISBN13.setFocus())
        self.lineEditISBN13.returnPressed.connect(lambda: self.plainTextEditDescription.setFocus())

        self.show()

    def ISBNCheck(self, LineEdit: QLineEdit, ClassISBN: type[ISBN], LastCheck: list[bool]) -> None:
        def Generate_ISBNCheckAndConvertFromUpdate() -> None:
            text = LineEdit.text()
            if len(text) == ClassISBN.digit_length:
                try:
                    if ClassISBN(text).verify():
                        LineEdit.setStyleSheet(f"color: green;")
                        LastCheck[0] = True
                        return
                    else:
                        raise Exception()
                except:
                    LineEdit.setStyleSheet(f"color: red;")
            else:
                LineEdit.setStyleSheet(f"color: black;")

            LastCheck[0] = False

        LineEdit.textChanged.connect(Generate_ISBNCheckAndConvertFromUpdate)

    def DescriptionCharacterCounting(self) -> None:
        length = len(self.plainTextEditDescription.toPlainText())
        self.labelDescriptionCharacterCounting.setText(str(length))

        if length > 1024:
            self.plainTextEditDescription.setStyleSheet(f"color: red;")
        else:
            self.plainTextEditDescription.setStyleSheet(f"color: black;")

    def pushButtonSaveClicked(self) -> None:
        if self.lineEditTitle.text().strip() == "":
            QMessageBox.warning(self, "Warning !", "At least it must have a title.")
        else:
            if (self.lineEditISBN10.text().strip() != "") and (not self.ISBN10_CURRECT[0]):
                QMessageBox.warning(self, "Error", "ISBN-10 is incurract")
                return

            if (self.lineEditISBN13.text().strip() != "") and (not self.ISBN13_CURRECT[0]):
                QMessageBox.warning(self, "Error", "ISBN-13 is incurract")
                return

            self.hide()
            if self.callback_func is not None:
                try:
                    data = self.DumpBookEditData()
                except Exception as err:
                    QMessageBox.warning(self, "Error", str(err))
                    return

                if self.callback_func(data, self.old_data) and self._closeEvent is not None:
                    self._closeEvent(self)
            else:
                QMessageBox.critical(self, "Runtime Error", "No callback function !")

    def LoadBookEditData(self, instance: BookData) -> None:
        self.lineEditTitle.setText(instance.title if instance.title else "")
        self.lineEditAuthor.setText(instance.author if instance.author else "")
        self.lineEditPublication.setText(instance.publication if instance.publication else "")
        self.lineEditISBN10.setText(instance.isbn10 if instance.isbn10 else "")
        self.lineEditISBN13.setText(instance.isbn13 if instance.isbn13 else "")
        self.plainTextEditDescription.setPlainText(instance.description if instance.description else "")

    def DumpBookEditData(self) -> BookData:
        image: Optional[bytes] = None

        if self.imageFileName is not None:
            image = open(self.imageFileName, "rb").read()
        elif self.old_data is not None:
            image = self.old_data.image

        author = self.lineEditAuthor.text().strip()
        isbn10 = self.lineEditISBN10.text().strip()
        isbn13 = self.lineEditISBN13.text().strip()
        publication = self.lineEditPublication.text().strip()
        description = self.plainTextEditDescription.toPlainText().strip()

        return BookData(
            bookId=self.old_data.bookId if self.old_data is not None else None,
            image=image,
            title=self.lineEditTitle.text().strip(),
            author=(author if author != "" else None),
            isbn10=(isbn10 if isbn10 != "" else None),
            isbn13=(isbn13 if isbn13 != "" else None),
            publication=(publication if publication != "" else None),
            description=(description if description != "" else None)
        )

    def getFile(self) -> None:
        self.imageFileName = QFileDialog(self).getOpenFileName(filter="Image files (*.jpg *.jpeg *.png);;All Files (*)")[0]
        self.labelFileName.setText(self.imageFileName)
