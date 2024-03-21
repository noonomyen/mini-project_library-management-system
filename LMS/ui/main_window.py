from typing import Callable, Optional, Any
from datetime import datetime

from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtWidgets import (
    QLabel, QAbstractItemView, QRadioButton, QInputDialog, QGroupBox, QHeaderView, QStackedWidget,
    QMessageBox, QStatusBar, QMenuBar, QMainWindow, QPushButton, QTableWidget, QLineEdit, QTableWidgetItem, QWidget
)
from PyQt6.QtGui import QIntValidator, QPixmap, QCloseEvent
from PyQt6 import uic

from ..config import CONFIG
from ..db_session import Session
from ..ui import Login_UI, BookEdit_UI, UserEdit_UI, BorrowRecordEdit_UI
from ..lms_types import BookData, UserData, BookBorrowHistoryData, BookReturnReviewData, BookBorrowReviewData
from ..utils import exclude_range

class MainWindow_UI(QMainWindow):
    LoginForm: Login_UI
    BookEditForms: list[BookEdit_UI]
    UserEditForms: list[UserEdit_UI]
    BorrowRecordEditForms: list[BorrowRecordEdit_UI]
    closeEventOld: Callable[[QCloseEvent], None]

    labelUsername: QLabel

    stackedWidget: QStackedWidget

    Dashboard: QWidget
    labelD_BookCount: QLabel
    labelD_UserCount: QLabel
    labelD_BorrowingCount: QLabel
    labelD_AllTimeBorrowedCount: QLabel
    labelD_Datetime: QLabel
    DatetimeTimer: QTimer

    Borrowing: QWidget
    defaultBorrowingBookImage: QPixmap
    BorrowingCurrentBookId: Optional[int]
    BorrowingCurrentUserId: Optional[int]
    groupBoxB: QGroupBox
    lineEditB_BookID: QLineEdit
    lineEditB_UserID: QLineEdit
    pushButtonB_Review: QPushButton
    labelB_BookID: QLabel
    labelB_BookTitle: QLabel
    labelB_UserID: QLabel
    labelB_UserName: QLabel
    pushButtonB_Borrow: QPushButton
    labelB_Image: QLabel

    Returning: QWidget
    defaultReturningBookImage: QPixmap
    ReturningCurrentBookId: Optional[int]
    groupBoxR: QGroupBox
    lineEditR_BookID: QLineEdit
    pushButtonR_Review: QPushButton
    labelR_BookID: QLabel
    labelR_BookTitle: QLabel
    labelR_UserID: QLabel
    labelR_UserName: QLabel
    labelR_Borrowed: QLabel
    pushButtonR_Return: QPushButton
    labelR_Image: QLabel

    BorrowingManagement: QWidget
    currentSelectRecord: Optional[int]
    currentSelectRecordHistoryId: Optional[int]
    listBorrowingHistory: list[BookBorrowHistoryData]
    BWMGMTcurrentSelectRadioButton = 0
    radioButtonBWMGMT_All: QRadioButton
    radioButtonBWMGMT_WaitReturn: QRadioButton
    radioButtonBWMGMT_Returned: QRadioButton
    lineEditBWMGMT_BookID: QLineEdit
    lineEditBWMGMT_UserID: QLineEdit
    pushButtonBWMGMT_Refresh: QPushButton
    tableWidgetBWMGMT: QTableWidget

    BookManagement: QWidget
    currentSelectBook: Optional[int]
    currentSelectBookId: Optional[int]
    bookList: list[BookData]
    defaultBookImage: QPixmap
    lineEditBMGMT_Search: QLineEdit
    labelBMGMT_BookImage: QLabel
    tableWidgetBMGMT: QTableWidget
    pushButtonBMGMT_Refresh: QPushButton
    pushButtonBMGMT_Add: QPushButton
    pushButtonBMGMT_Edit: QPushButton
    pushButtonBMGMT_EditByID: QPushButton
    pushButtonBMGMT_Remove: QPushButton
    pushButtonBMGMT_ClearBook: QPushButton
    labelBMGMT_Title: QLabel
    labelBMGMT_bookId: QLabel
    labelBMGMT_Author: QLabel
    labelBMGMT_Publication: QLabel
    labelBMGMT_ISBN10: QLabel
    labelBMGMT_ISBN13: QLabel
    labelBMGMT_Description: QLabel

    UserManagement: QWidget
    userList: list[UserData]
    currentSelectUser: Optional[int]
    currentSelectUserId: Optional[int]
    tableWidgetUMGMT: QTableWidget
    pushButtonUMGMT_Add: QPushButton
    pushButtonUMGMT_Edit: QPushButton
    pushButtonUMGMT_EditByID: QPushButton
    pushButtonUMGMT_Remove: QPushButton
    pushButtonUMGMT_Refresh: QPushButton
    pushButtonUMGMT_ClearUser: QPushButton
    lineEditUMGMT_FirstName: QLineEdit
    lineEditUMGMT_LastName: QLineEdit

    pushButtonDashboard: QPushButton
    pushButtonBorrowing: QPushButton
    pushButtonReturning: QPushButton
    pushButtonBorrowingMGMT: QPushButton
    pushButtonBookMGMT: QPushButton
    pushButtonUserMGMT: QPushButton
    pushButtonLogout: QPushButton

    menubar: QMenuBar
    statusbar: QStatusBar

    DESIGNER_FILE: str = "main-window.ui"

    def __init__(self) -> None:
        super().__init__()
        uic.load_ui.loadUi(CONFIG.LMS.DESIGNER_FILES.joinpath(self.DESIGNER_FILE), self)

        self.LoginForm = Login_UI(self.init)
        self.LoginForm.open()

        self.BookEditForms = []
        self.UserEditForms = []
        self.BorrowRecordEditForms = []

        self.pushButtonDashboard.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButtonBorrowing.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButtonReturning.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.pushButtonBorrowingMGMT.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.pushButtonBookMGMT.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
        self.pushButtonUserMGMT.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(5))
        self.pushButtonLogout.clicked.connect(self.pushButtonLogoutClicked)

        self.pushButtonDashboard.clicked.connect(self.DashboardUpdate)
        self.pushButtonBorrowing.clicked.connect(self.Borrowing_ReviewClear)
        self.pushButtonReturning.clicked.connect(self.Returning_ReviewClear)
        self.pushButtonBorrowingMGMT.clicked.connect(self.BorrowingManagement_listRefresh)
        self.pushButtonBookMGMT.clicked.connect(self.BookManagement_listBookRefresh)
        self.pushButtonUserMGMT.clicked.connect(self.UserManagement_listUserRefresh)
        self.stackedWidget.setCurrentIndex(0)

        self.statusbar.showMessage(f"Version : {CONFIG.LMS.VERSION}")

        self.labelD_BookCount.setText("")
        self.labelD_UserCount.setText("")
        self.labelD_BorrowingCount.setText("")
        self.labelD_AllTimeBorrowedCount.setText("")

        self.pushButtonBMGMT_Add.clicked.connect(self.BookManagement_pushButton_addBook)
        self.defaultBookImage = self.labelBMGMT_BookImage.pixmap()

        self.lineEditBMGMT_Search.returnPressed.connect(self.BookManagement_listBookRefresh)
        self.pushButtonBMGMT_Refresh.clicked.connect(self.BookManagement_listBookRefresh)
        self.pushButtonBMGMT_Edit.clicked.connect(self.BookManagement_pushButton_editBook)
        self.pushButtonBMGMT_EditByID.clicked.connect(self.BookManagement_pushButton_editBookByID)
        self.pushButtonBMGMT_Remove.clicked.connect(self.BookManagement_pushButton_removeBook)
        self.pushButtonBMGMT_ClearBook.clicked.connect(self.BookManagement_pushButton_ClearBook)
        self.tableWidgetBMGMT.verticalHeader().setVisible(True)
        self.tableWidgetBMGMT.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidgetBMGMT.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidgetBMGMT.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidgetBMGMT.cellClicked.connect(self.BookManagement_SelectRow)
        self.tableWidgetBMGMT.cellDoubleClicked.connect(self.BookManagement_pushButton_editBook)
        _ = self.tableWidgetBMGMT.horizontalHeader()
        _.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(1, 6): _.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self.tableWidgetBMGMT.setStyleSheet("QTableWidget::item { padding: 0px 10px }")

        self.lineEditUMGMT_FirstName.returnPressed.connect(self.UserManagement_listUserRefresh)
        self.lineEditUMGMT_LastName.returnPressed.connect(self.UserManagement_listUserRefresh)
        self.pushButtonUMGMT_Add.clicked.connect(self.UserManagement_pushButton_addUser)
        self.pushButtonUMGMT_Edit.clicked.connect(self.UserManagement_pushButton_editUser)
        self.pushButtonUMGMT_EditByID.clicked.connect(self.UserManagement_pushButton_editUserById)
        self.pushButtonUMGMT_Remove.clicked.connect(self.UserManagement_pushButton_removeUser)
        self.pushButtonUMGMT_Refresh.clicked.connect(self.UserManagement_listUserRefresh)
        self.pushButtonUMGMT_ClearUser.clicked.connect(self.UserManagement_pushButton_ClearUser)
        self.tableWidgetUMGMT.cellClicked.connect(self.UserManagement_SelectRow)
        self.tableWidgetUMGMT.cellDoubleClicked.connect(self.UserManagement_pushButton_editUser)
        self.tableWidgetUMGMT.verticalHeader().setVisible(True)
        self.tableWidgetUMGMT.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidgetUMGMT.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidgetUMGMT.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        _ = self.tableWidgetUMGMT.horizontalHeader()
        for i in range(0, 5):  _.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        _.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tableWidgetUMGMT.setStyleSheet("QTableWidget::item { padding: 0px 10px }")

        self.installEventFilter(self)

        self.currentSelectBook = None
        self.currentSelectBookId = None
        self.bookList = []

        self.BookManagement_SetDisplayBook(BookData(None, None, "", "", "", "", "", ""))

        self.currentSelectUser = None
        self.currentSelectUserId = None
        self.userList = []

        self.lineEditB_BookID.setValidator(QIntValidator())
        self.lineEditB_UserID.setValidator(QIntValidator())
        self.lineEditB_BookID.returnPressed.connect(lambda: self.lineEditB_UserID.setFocus())
        self.lineEditB_UserID.returnPressed.connect(lambda: self.Borrowing_ReviewClicked())
        self.pushButtonB_Review.clicked.connect(self.Borrowing_ReviewClicked)
        self.pushButtonB_Borrow.clicked.connect(self.Borrowing_BorrowClicked)
        self.defaultBorrowingBookImage = self.labelB_Image.pixmap()
        self.Borrowing_ReviewClear()
        self.BorrowingCurrentBookId = None
        self.BorrowingCurrentUserId = None
        self.groupBoxB.hide()

        self.lineEditR_BookID.setValidator(QIntValidator())
        self.lineEditR_BookID.returnPressed.connect(self.Returning_ReviewClicked)
        self.pushButtonR_Review.clicked.connect(self.Returning_ReviewClicked)
        self.pushButtonR_Return.clicked.connect(self.Returning_ReturnClicked)
        self.defaultReturningBookImage = self.labelR_Image.pixmap()
        self.ReturningCurrentBookId = None
        self.groupBoxR.hide()

        self.lineEditR_BookID.setValidator(QIntValidator())

        self.radioButtonBWMGMT_All.toggled.connect(lambda: self.BorrowingManagement_RadioButton(0))
        self.radioButtonBWMGMT_WaitReturn.toggled.connect(lambda: self.BorrowingManagement_RadioButton(1))
        self.radioButtonBWMGMT_Returned.toggled.connect(lambda: self.BorrowingManagement_RadioButton(2))
        self.radioButtonBWMGMT_All.toggled.connect(lambda: self.BorrowingManagement_listRefresh())
        self.radioButtonBWMGMT_WaitReturn.toggled.connect(lambda: self.BorrowingManagement_listRefresh())
        self.radioButtonBWMGMT_Returned.toggled.connect(lambda: self.BorrowingManagement_listRefresh())
        self.pushButtonBWMGMT_Refresh.clicked.connect(self.BorrowingManagement_listRefresh)
        self.lineEditBWMGMT_BookID.returnPressed.connect(lambda: self.lineEditBWMGMT_UserID.setFocus())
        self.lineEditBWMGMT_UserID.returnPressed.connect(self.BorrowingManagement_listRefresh)
        self.tableWidgetBWMGMT.cellClicked.connect(self.BorrowingManagement_SelectRow)
        self.tableWidgetBWMGMT.cellDoubleClicked.connect(self.BorrowingManagement_pushButton_edit)
        self.tableWidgetBWMGMT.verticalHeader().setVisible(True)
        self.tableWidgetBWMGMT.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidgetBWMGMT.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidgetBWMGMT.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        _ = self.tableWidgetBWMGMT.horizontalHeader()
        for i in exclude_range(0, 8, (2, 4)): _.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        for i in (2, 4): _.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self.tableWidgetBWMGMT.setStyleSheet("QTableWidget::item { padding: 0px 10px }")
        self.currentSelectRecord = None
        self.currentSelectRecordHistoryId = None
        self.listBorrowingHistory = []

        self.DatetimeTimer = QTimer()
        self.DatetimeTimer.timeout.connect(lambda: self.labelD_Datetime.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.DatetimeTimer.setInterval(500)
        self.DatetimeTimer.start()

        self.closeEventOld = self.closeEvent
        self.closeEvent = self.HookCloseEvent # type: ignore

    def init(self) -> None:
        self.LoginForm.close()
        self.labelUsername.setText(CONFIG.USER.USERNAME)
        self.show()
        self.DashboardUpdate()
        self.BookManagement_listBook()
        if len(self.bookList) > 0:
            self.BookManagement_SelectRow(0)
        self.UserManagement_listUser()
        self.BorrowingManagement_listBorrowHistory()

    def HookCloseEvent(self, a0: QCloseEvent) -> None:
        self.BookEditForm_Clear()
        self.UserEditForm_Clear()
        self.closeEventOld(a0)

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_F5:
                if self.stackedWidget.currentIndex() == 3:
                    self.BorrowingManagement_listRefresh()
                elif self.stackedWidget.currentIndex() == 4:
                    self.BookManagement_listBookRefresh()
                elif self.stackedWidget.currentIndex() == 5:
                    self.UserManagement_listUserRefresh()

        return super().eventFilter(obj, event)

    def DashboardUpdate(self) -> None:
        book_count = Session.getBookCount()
        if book_count[0]:
            self.labelD_BookCount.setText(str(book_count[1]))

        user_count = Session.getUserCount()
        if user_count[0]:
            self.labelD_UserCount.setText(str(user_count[1]))

        borrow_count = Session.getBorrowingCount()
        if borrow_count[0]:
            self.labelD_BorrowingCount.setText(str(borrow_count[1]))

        all_time_borrow_count = Session.getAllTimeBorrowedCount()
        if all_time_borrow_count[0]:
            self.labelD_AllTimeBorrowedCount.setText(str(all_time_borrow_count[1]))

    # ------------------------------------------------------------------

    def Borrowing_ReviewClicked(self) -> None:
        bookId = self.lineEditB_BookID.text().strip()
        userId = self.lineEditB_UserID.text().strip()

        if bookId == "" and userId == "":
            self.Borrowing_ReviewClear()
        elif bookId == "":
            QMessageBox.warning(self, "Warning", "Book ID should not be empty.")
        elif userId == "":
            QMessageBox.warning(self, "Warning", "User ID should not be empty.")
        else:
            self.Borrowing_ReviewClear()
            IntBookId = int(bookId)
            IntUserId = int(userId)
            result = Session.borrowBookGetReview(IntBookId, IntUserId)
            self.BorrowingCurrentBookId = (IntBookId if result[0] else None)
            self.BorrowingCurrentUserId = (IntUserId if result[0] else None)
            if result[0] == True:
                self.lineEditB_BookID.setText("")
                self.lineEditB_UserID.setText("")
                self.Borrowing_ReviewSetDisplay(result[1])
            else:
                QMessageBox.warning(self, "Error", result[1])

    def Borrowing_BorrowClicked(self) -> None:
        if self.BorrowingCurrentBookId and self.BorrowingCurrentUserId:
            result = Session.borrowBook(self.BorrowingCurrentBookId, self.BorrowingCurrentUserId)
            if result[0]:
                QMessageBox.information(self, "Borrowing Book", "Saved successfully.")
                self.Borrowing_ReviewClear()
            else:
                QMessageBox.warning(self, "Borrowing Book", "Failed to borrow this book.\n\n" + str(result[1]))

    def Borrowing_ReviewClear(self) -> None:
        self.groupBoxB.hide()
        self.labelB_BookID.setText("")
        self.labelB_BookTitle.setText("")
        self.labelB_UserID.setText("")
        self.labelB_UserName.setText("")
        self.labelB_Image.setPixmap(self.defaultBorrowingBookImage)

    def Borrowing_ReviewSetDisplay(self, data: BookBorrowReviewData) -> None:
        self.labelB_BookID.setText(str(data.bookId))
        self.labelB_BookTitle.setText(data.bookTitle)
        self.labelB_UserID.setText(str(data.userId))
        self.labelB_UserName.setText(data.userName)

        try:
            if data.bookImage:
                pixmap = QPixmap()
                pixmap.loadFromData(data.bookImage) # type: ignore
                self.labelB_Image.setPixmap(pixmap)
            else:
                self.labelB_Image.setPixmap(self.defaultBorrowingBookImage)
        except Exception as err:
            QMessageBox.critical(self, "Error", "Failed to load image of this book." + "\n\n" + str(err))

        self.groupBoxB.show()

    # ------------------------------------------------------------------

    def Returning_ReviewClicked(self) -> None:
        bookId = self.lineEditR_BookID.text().strip()

        if bookId == "":
            self.Returning_ReviewClear()
            QMessageBox.warning(self, "Warning", "Book ID should not be empty.")
        else:
            IntBookId = int(bookId)
            result = Session.returnBookGetReview(IntBookId)
            self.ReturningCurrentBookId = (IntBookId if result[0] else None)
            if result[0] == True:
                self.lineEditR_BookID.setText("")
                self.Returning_ReviewSetDisplay(result[1])
            else:
                QMessageBox.warning(self, "Error", result[1])

    def Returning_ReturnClicked(self) -> None:
        if self.ReturningCurrentBookId:
            result = Session.returnBook(self.ReturningCurrentBookId)
            if result[0]:
                QMessageBox.information(self, "Returning Book", "Saved successfully.")
                self.Returning_ReviewClear()
            else:
                QMessageBox.warning(self, "Returning Book", "Failed to borrow this book.\n\n" + str(result[1]))

    def Returning_ReviewClear(self) -> None:
        self.groupBoxR.hide()
        self.labelR_BookID.setText("")
        self.labelR_BookTitle.setText("")
        self.labelR_UserID.setText("")
        self.labelR_UserName.setText("")
        self.labelR_Borrowed.setText("")
        self.labelR_Image.setPixmap(self.defaultReturningBookImage)

    def Returning_ReviewSetDisplay(self, data: BookReturnReviewData) -> None:
        self.labelR_BookID.setText(str(data.bookId))
        self.labelR_BookTitle.setText(data.bookTitle)
        self.labelR_UserID.setText(str(data.userId))
        self.labelR_UserName.setText(data.userName)
        self.labelR_Borrowed.setText(str(data.borrowed))

        try:
            if data.bookImage:
                pixmap = QPixmap()
                pixmap.loadFromData(data.bookImage) # type: ignore
                self.labelR_Image.setPixmap(pixmap)
            else:
                self.labelR_Image.setPixmap(self.defaultReturningBookImage)
        except Exception as err:
            QMessageBox.critical(self, "Error", "Failed to load image of this book." + "\n\n" + str(err))

        self.groupBoxR.show()

    # ------------------------------------------------------------------

    def BorrowRecordEditForm_New(self, callback: BorrowRecordEdit_UI.Callback, data: BookBorrowHistoryData) -> None:
        instance = BorrowRecordEdit_UI(callback, data, self.BorrowRecordForm_Del)
        self.BorrowRecordEditForms.append(instance)

    def BorrowRecordForm_Del(self, instance: BorrowRecordEdit_UI) -> None:
        instance.close()
        self.BorrowRecordEditForms.remove(instance)

    def BorrowRecordForm_Clear(self) -> None:
        for instance in self.BorrowRecordEditForms:
            instance.close()

        self.BorrowRecordEditForms.clear()

    def BorrowingManagement_RadioButton(self, index: int) -> None:
        self.BWMGMTcurrentSelectRadioButton = index
        l = (self.radioButtonBWMGMT_All, self.radioButtonBWMGMT_WaitReturn, self.radioButtonBWMGMT_Returned)

        for idx, btn in enumerate(l):
            if index != idx:
                btn.setChecked(False)

    def BorrowingManagement_pushButton_edit(self) -> None:
        if self.currentSelectRecord is not None and self.currentSelectRecord < len(self.listBorrowingHistory):
            self.BorrowRecordEditForm_New(self.BorrowingManagement_edit, self.listBorrowingHistory[self.currentSelectRecord])

    def BorrowingManagement_edit(self, action: BorrowRecordEdit_UI.BorrowRecordEditAction, data: Optional[BookBorrowHistoryData], old_data: Optional[BookBorrowHistoryData]) -> bool:
        if action == BorrowRecordEdit_UI.BorrowRecordEditAction.SAVE and data is not None and old_data is not None:
            if data == old_data:
                return True

            result = Session.updateBorrowHistory(data, old_data)

            if result[0] == True:
                QMessageBox.information(self, "Update borrowing history", "Record updated successfully")
            else:
                QMessageBox.warning(self, "Update borrowing history", f"Failed to update record\n{result[1]}")
                return False

            self.BorrowingManagement_listRefresh()
            return True
        elif action == BorrowRecordEdit_UI.BorrowRecordEditAction.REMOVE:
            reply = QMessageBox.question(
                self, "Remove borrowing history", "Are you sure you want to delete this record?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.currentSelectRecord is not None and self.currentSelectRecordHistoryId is not None and self.currentSelectRecord < len(self.listBorrowingHistory):
                    result = Session.removeBorrowHistory(self.currentSelectRecordHistoryId)
                    if result[0] == True:
                        QMessageBox.information(self, "Remove borrowing history", "This record has been successfully removed.")
                    else:
                        QMessageBox.warning(self, "Error", f"Failed to remove this record\n\n{result[1]}")
                else:
                    QMessageBox.warning(self, "Warning", "Please select an item.")

                self.BorrowingManagement_listRefresh()
            return True
        else:
            return False

    def BorrowingManagement_SelectRow(self, row: Optional[int] = None) -> None:
        if row is not None:
            self.currentSelectRecord = row
            self.currentSelectRecordHistoryId = self.listBorrowingHistory[row].historyId
        else:
            row = self.tableWidgetBMGMT.currentRow()
            self.currentSelectRecordHistoryId = self.listBorrowingHistory[row].historyId
            try:
                self.currentSelectUser = row
            except Exception as err:
                QMessageBox.critical(self, "Error", str(err))

    def BorrowingManagement_listRefresh(self) -> None:
        bookId = self.lineEditBWMGMT_BookID.text().strip()
        userId = self.lineEditBWMGMT_UserID.text().strip()
        borrowing=self.radioButtonBWMGMT_WaitReturn.isChecked()
        returned=self.radioButtonBWMGMT_Returned.isChecked()
        if (bookId != "" or userId != "") or borrowing or returned:
            result = Session.searchBorrowHistoryByBookOrUserId(
                int(bookId) if bookId != "" else None,
                int(userId) if userId != "" else None,
                borrowing=borrowing,
                returned=returned
            )
            if result[0] == True:
                self.BorrowingManagement_listBorrowHistory(result[1])
            else:
                QMessageBox.warning(self, "Error", result[1])
        else:
            self.BorrowingManagement_listBorrowHistory()

    def BorrowingManagement_listBorrowHistory(self, data: Optional[list[BookBorrowHistoryData]] = None) -> None:
        self.tableWidgetBWMGMT.clearFocus()

        if data is None:
            list_result = Session.listBorrowHistory()

            if list_result[0] == True:
                data = list_result[1]
            else:
                QMessageBox.warning(self, "Error", list_result[1])
                return None

        self.listBorrowingHistory.clear()
        self.tableWidgetBWMGMT.setRowCount(len(data))

        if data:
            for row, record in enumerate(data):
                self.listBorrowingHistory.append(record)
                color = Qt.GlobalColor.green if record.returned else Qt.GlobalColor.red
                self.tableWidgetBWMGMT.setItem(row, 0, self.toTableWidgetItem(record.historyId, center=True))
                self.tableWidgetBWMGMT.setItem(row, 1, self.toTableWidgetItem(record.userId, center=True))
                self.tableWidgetBWMGMT.setItem(row, 2, self.toTableWidgetItem(record.userName))
                self.tableWidgetBWMGMT.setItem(row, 3, self.toTableWidgetItem(record.bookId, center=True))
                self.tableWidgetBWMGMT.setItem(row, 4, self.toTableWidgetItem(record.bookTitle))
                self.tableWidgetBWMGMT.setItem(row, 5, self.toTableWidgetItem(record.borrowed, center=True))
                self.tableWidgetBWMGMT.setItem(row, 6, self.toTableWidgetItem((record.returned if record.returned else "-"), center=True))
                self.tableWidgetBWMGMT.setItem(row, 7, self.toTableWidgetItem(("Returned" if record.returned else "Borrowing"), center=True, color=color))
        else:
            self.currentSelectRecord = None
            self.currentSelectRecordHistoryId = None

    # ------------------------------------------------------------------

    def BookEditForm_New(self, callback: BookEdit_UI.Callback, data: Optional[BookData] = None) -> None:
        instance = BookEdit_UI(callback, data, self.BookEditForm_Del)
        self.BookEditForms.append(instance)

    def BookEditForm_Del(self, instance: BookEdit_UI) -> None:
        instance.close()
        self.BookEditForms.remove(instance)

    def BookEditForm_Clear(self) -> None:
        for instance in self.BookEditForms:
            instance.close()

        self.BookEditForms.clear()

    def BookManagement_pushButton_addBook(self) -> None:
        self.BookEditForm_New(self.BookManagement_addBook)

    def BookManagement_addBook(self, data: BookData, _) -> bool:
        result = Session.addBook(data)

        if result[0] == True:
            QMessageBox.information(self, "Add book", "Book added successfully" + (f", ID is {result[1]}" if result[1] else ""))
        else:
            QMessageBox.warning(self, "Add book", f"Failed to add book\n{result[1]}")
            return False

        self.BookManagement_listBookRefresh()
        return True

    def BookManagement_pushButton_editBook(self) -> None:
        if self.currentSelectBook is not None and self.currentSelectBook < len(self.bookList):
            self.BookEditForm_New(self.BookManagement_editBook, self.bookList[self.currentSelectBook])

    def BookManagement_editBook(self, data: BookData, old_data: Optional[BookData]) -> bool:
        if data == old_data:
            return True

        result = Session.updateBook(data, old_data)

        if result[0] == True:
            QMessageBox.information(self, "Update book", "Book updated successfully")
        else:
            QMessageBox.warning(self, "Update book", f"Failed to update data\n{result[1]}")
            return False

        self.BookManagement_listBookRefresh()
        return True

    def BookManagement_pushButton_removeBook(self) -> None:
        reply = QMessageBox.question(
            self, "Remove book", "Are you sure you want to delete this book?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.currentSelectBook is not None and self.currentSelectBookId is not None and self.currentSelectBook < len(self.bookList):
                result = Session.removeBook(self.currentSelectBookId)
                if result[0] == True:
                    QMessageBox.information(self, "Remove book", "This book has been successfully removed.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to remove this book\n\n{result[1]}")
            else:
                QMessageBox.warning(self, "Warning", "Please select an item.")

            self.BookManagement_listBookRefresh()

    def BookManagement_pushButton_editBookByID(self) -> None:
        reply = QInputDialog.getText(self, "Edit by ID", "Book ID")
        if reply[1]:
            text = reply[0].strip()
            if text == "":
                QMessageBox.warning(self, "Error", "Book ID should not be empty.")
            else:
                result = Session.getBook(int(text))
                if result[0] == True:
                    if result[1] is None:
                        QMessageBox.information(self, "Result", f"Not Found, Book ID {text}")
                    else:
                        self.BookEditForm_New(self.BookManagement_editBook, result[1])
                else:
                    QMessageBox.warning(self, "Error", result[1])

        self.BookManagement_listBookRefresh()

    def BookManagement_listBookRefresh(self) -> None:
        title = self.lineEditBMGMT_Search.text().strip()
        if title != "":
            result = Session.searchBookByTitle(title)
            if result[0] == True:
                self.BookManagement_listBook(result[1])
            else:
                QMessageBox.warning(self, "Error", result[1])
        else:
            self.BookManagement_listBook()

        if len(self.bookList) > 0:
            if self.currentSelectBookId:
                select = self.bookList[0]
                for item in self.bookList:
                    if item.bookId == self.currentSelectBookId:
                        select = item
                        break

                self.BookManagement_SetDisplayBook(select)
        else:
            self.BookManagement_SetDisplayBook(BookData(None, None, "", "", "", "", "", ""))

    def BookManagement_listBook(self, data: Optional[list[BookData]] = None) -> None:
        self.tableWidgetBMGMT.clearFocus()

        if data is None:
            listbook_result = Session.listBook()

            if listbook_result[0] == True:
                data = listbook_result[1]
            else:
                QMessageBox.warning(self, "Error", listbook_result[1])
                return None

        self.bookList.clear()
        self.tableWidgetBMGMT.setRowCount(len(data))

        if data:
            for row, book in enumerate(data):
                self.bookList.append(book)
                self.tableWidgetBMGMT.setItem(row, 0, self.toTableWidgetItem(book.bookId, center=True))
                self.tableWidgetBMGMT.setItem(row, 1, self.toTableWidgetItem(book.title))
                self.tableWidgetBMGMT.setItem(row, 2, self.toTableWidgetItem(book.author))
                self.tableWidgetBMGMT.setItem(row, 3, self.toTableWidgetItem(book.publication))
                self.tableWidgetBMGMT.setItem(row, 4, self.toTableWidgetItem(book.isbn10))
                self.tableWidgetBMGMT.setItem(row, 5, self.toTableWidgetItem(book.isbn13))
        else:
            self.currentSelectBook = None
            self.currentSelectBookId = None

    def BookManagement_SelectRow(self, row: Optional[int] = None) -> None:
        if row is not None:
            self.currentSelectBook = row
            self.currentSelectBookId = self.bookList[row].bookId
            self.BookManagement_SetDisplayBook(self.bookList[row])
        else:
            row = self.tableWidgetBMGMT.currentRow()
            try:
                self.currentSelectBook = row
                self.currentSelectBookId = self.bookList[row].bookId
                self.BookManagement_SetDisplayBook(self.bookList[row])
            except Exception as err:
                QMessageBox.critical(self, "Error", str(err))

    def BookManagement_SetDisplayBook(self, data: BookData) -> None:
        try:
            if data.image:
                image = QPixmap()
                image.loadFromData(data.image) # type: ignore
                self.labelBMGMT_BookImage.setPixmap(image)
            else:
                self.labelBMGMT_BookImage.setPixmap(self.defaultBookImage)
        except Exception as err:
            QMessageBox.critical(self, "Error", str(err))
            return None

        self.labelBMGMT_bookId.setText(str(data.bookId) if data.bookId else "")
        self.labelBMGMT_Title.setText(data.title)
        self.labelBMGMT_Author.setText(data.author if data.author else "")
        self.labelBMGMT_Publication.setText(data.publication if data.publication else "")
        self.labelBMGMT_ISBN10.setText(data.isbn10 if data.isbn10 else "")
        self.labelBMGMT_ISBN13.setText(data.isbn13 if data.isbn13 else "")
        self.labelBMGMT_Description.setText(data.description if data.description else "")

    def BookManagement_pushButton_ClearBook(self) -> None:
        reply = QMessageBox.question(
            self, "Clear book", "Are you sure to clear book from database?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            result = Session.clearBook()
            if result[0] == True:
                QMessageBox.information(self, "Clear book", "All books have been successfully removed from the database.")
                self.BookManagement_listBookRefresh()
            else:
                QMessageBox.warning(self, "Clear book", "Failed to clear book from the database.\n\n" + result[1])

    # ------------------------------------------------------------------

    def UserEditForm_New(self, callback: UserEdit_UI.Callback, data: Optional[UserData] = None) -> None:
        instance = UserEdit_UI(callback, data, self.UserEditForm_Del)
        self.UserEditForms.append(instance)

    def UserEditForm_Del(self, instance: UserEdit_UI) -> None:
        instance.close()
        self.UserEditForms.remove(instance)

    def UserEditForm_Clear(self) -> None:
        for instance in self.UserEditForms:
            instance.close()

        self.UserEditForms.clear()

    def UserManagement_pushButton_addUser(self) -> None:
        self.UserEditForm_New(self.UserManagement_addUser)

    def UserManagement_addUser(self, data: UserData, _) -> bool:
        result = Session.addUser(data)

        if result[0] == True:
            QMessageBox.information(self, "Add user", "User added successfully" + (f", ID is {result[1]}" if result[1] else ""))
        else:
            QMessageBox.warning(self, "Add user", f"Failed to add user\n\n{result[1]}")
            return False

        self.UserManagement_listUserRefresh()
        return True

    def UserManagement_pushButton_editUser(self) -> None:
        if self.currentSelectUser is not None and self.currentSelectUser < len(self.userList):
            self.UserEditForm_New(self.UserManagement_editUser, self.userList[self.currentSelectUser])

    def UserManagement_editUser(self, data: UserData, old_data: Optional[UserData]) -> bool:
        if data == old_data:
            return True

        result = Session.updateUser(data, old_data)

        if result[0] == True:
            QMessageBox.information(self, "Update user", "User updated successfully")
        else:
            QMessageBox.warning(self, "Update user", f"Failed to update data\n\n{result[1]}")
            return False

        self.UserManagement_listUserRefresh()
        return True

    def UserManagement_pushButton_removeUser(self) -> None:
        reply = QMessageBox.question(
            self, "Remove user", "Are you sure you want to delete this user?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.currentSelectUser is not None and self.currentSelectUserId is not None and self.currentSelectUser < len(self.userList):
                result = Session.removeUser(self.currentSelectUserId)
                if result[0] == True:
                    QMessageBox.information(self, "Remove user", "This user has been successfully removed.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to remove this user\n\n{result[1]}")
            else:
                QMessageBox.warning(self, "Warning", "Please select an item.")

            self.UserManagement_listUserRefresh()

    def UserManagement_pushButton_editUserById(self) -> None:
        reply = QInputDialog.getText(self, "Edit by ID", "User ID")
        if reply[1]:
            text = reply[0].strip()
            if text == "":
                QMessageBox.warning(self, "Error", "User ID should not be empty.")
            else:
                result = Session.getUser(int(text))
                if result[0] == True:
                    if result[1] is None:
                        QMessageBox.information(self, "Result", f"Not Found, User ID {text}")
                    else:
                        self.UserEditForm_New(self.UserManagement_editUser, result[1])
                else:
                    QMessageBox.warning(self, "Error", result[1])

        self.UserManagement_listUserRefresh()

    def UserManagement_SelectRow(self, row: Optional[int] = None) -> None:
        if row is not None:
            self.currentSelectUser = row
            self.currentSelectUserId = self.userList[row].userId
        else:
            row = self.tableWidgetBMGMT.currentRow()
            try:
                self.currentSelectUser = row
                self.currentSelectUserId = self.userList[row].userId
            except Exception as err:
                QMessageBox.critical(self, "Error", str(err))

    def UserManagement_listUserRefresh(self) -> None:
        firstName = self.lineEditUMGMT_FirstName.text().strip()
        lastName = self.lineEditUMGMT_LastName.text().strip()
        if firstName != "" or lastName != "":
            result = Session.searchUserByName(
                firstName if firstName != "" else None,
                lastName if lastName != "" else None
            )
            if result[0] == True:
                self.UserManagement_listUser(result[1])
            else:
                QMessageBox.warning(self, "Error", result[1])
        else:
            self.UserManagement_listUser()

    def UserManagement_listUser(self, data: Optional[list[UserData]] = None) -> None:
        self.tableWidgetUMGMT.clearFocus()

        if data is None:
            result = Session.listUser()

            if result[0] == True:
                data = result[1]
            else:
                QMessageBox.warning(self, "Error", result[1])
                return None

        self.userList.clear()
        self.tableWidgetUMGMT.setRowCount(len(data))

        if data:
            for row, user in enumerate(data):
                self.userList.append(user)
                self.tableWidgetUMGMT.setItem(row, 0, self.toTableWidgetItem(user.userId, center=True))
                self.tableWidgetUMGMT.setItem(row, 1, self.toTableWidgetItem((user.prefixName + "." if user.prefixName else "") + user.firstName))
                self.tableWidgetUMGMT.setItem(row, 2, self.toTableWidgetItem(user.lastName))
                self.tableWidgetUMGMT.setItem(row, 3, self.toTableWidgetItem(user.email if user.email else ""))
                self.tableWidgetUMGMT.setItem(row, 4, self.toTableWidgetItem(user.phone if user.phone else ""))
                self.tableWidgetUMGMT.setItem(row, 5, self.toTableWidgetItem(user.address if user.address else ""))
        else:
            self.currentSelectUser = None
            self.currentSelectUserId = None

    def UserManagement_pushButton_ClearUser(self) -> None:
        reply = QMessageBox.question(
            self, "Clear user", "Are you sure to clear user from database?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            result = Session.clearUser()
            if result[0] == True:
                QMessageBox.information(self, "Clear user", "All users have been successfully removed from the database.")
                self.UserManagement_listUserRefresh()
            else:
                QMessageBox.warning(self, "Clear user", "Failed to clear user from the database.\n\n" + result[1])

    # ------------------------------------------------------------------

    def pushButtonLogoutClicked(self) -> None:
        reply = QMessageBox.question(
            self, "Logout ?", "Are you sure to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.BookEditForm_Clear()
            self.UserEditForm_Clear()
            self.BorrowRecordForm_Clear()
            Session.close()
            self.hide()
            self.LoginForm.open()

    # ------------------------------------------------------------------

    @staticmethod
    def toTableWidgetItem(text: Any, center: bool = False, color: Optional[Qt.GlobalColor] = None) -> QTableWidgetItem:
        item = QTableWidgetItem(str(text if text is not None else ""))
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if color:
            item.setForeground(color)
        return item
