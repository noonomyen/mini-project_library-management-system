import mysql.connector

from typing import Optional, Generator, Callable, Union
from datetime import datetime

from mysql.connector.abstracts import  MySQLConnectionAbstract, MySQLCursorAbstract
from mysql.connector.pooling import PooledMySQLConnection
from mysql.connector.types import RowType
from mysql.connector.errorcode import ER_DUP_ENTRY
from mysql.connector.errors import Error as MysqlError

from .config import CONFIG
from .lms_types import UserData, BookData, BookBorrowHistoryData, BookBorrowReviewData, BookReturnReviewData, ExecuteResult

class DBSession:
    connection: PooledMySQLConnection | MySQLConnectionAbstract

    cursor: MySQLCursorAbstract

    def init(self) -> None:
        self.connection = mysql.connector.connect(
            host=CONFIG.REMOTE.HOST,
            port=CONFIG.REMOTE.PORT,
            user=CONFIG.USER.USERNAME,
            password=CONFIG.USER.PASSWORD,
            database=CONFIG.REMOTE.DATABASE,
            ssl_disabled=False
        )

        self.cursor = self.connection.cursor(buffered=False)

    def addBook(self, data: BookData) -> ExecuteResult[Optional[int]]:
        try:
            self.cursor.execute(
                "INSERT INTO Book (image, title, author, isbn10, isbn13, publication, description) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (data.image, data.title, data.author, data.isbn10, data.isbn13, data.publication, data.description)
            )
            self.connection.commit()
            if self.cursor.rowcount > 0:
                return (True, None)
            else:
                return (False, str("No update"))
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

    def updateBook(self, data: BookData, old_data: Optional[BookData] = None) -> ExecuteResult[None]:
        if data.bookId is None:
            return False, "data.bookId is None"

        try:
            colvals: list[tuple[str, Union[str, int, bytes, None]]] = []

            if old_data is not None:
                if data.image != old_data.image: colvals.append(("image", data.image))
                if data.title != old_data.title: colvals.append(("title", data.title))
                if data.author != old_data.author: colvals.append(("author", data.author))
                if data.isbn10 != old_data.isbn10: colvals.append(("isbn10", data.isbn10))
                if data.isbn13 != old_data.isbn13: colvals.append(("isbn13", data.isbn13))
                if data.publication != old_data.publication: colvals.append(("publication", data.publication))
                if data.description != old_data.description: colvals.append(("description", data.description))
            else:
                colvals = [("image", data.image), ("title", data.title), ("author", data.author), ("isbn10", data.isbn10), ("isbn13", data.isbn13), ("publication", data.publication), ("description", data.description)]

            if len(colvals) > 0:
                self.cursor.execute("UPDATE Book SET " + (", ".join([f"{i[0]}=%s" for i in colvals])) + " WHERE bookId = %s", tuple([i[1] for i in colvals] + [data.bookId]))
                self.connection.commit()
            else:
                return (False, "No update")
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

        return (True, None)

    def _RowTypeToBookData(self, row: RowType) -> BookData:
        return BookData(
            bookId=row[0] if type(row[0]) is int else None,
            image=row[1] if type(row[1]) is bytes else None,
            title=row[2] if type(row[2]) is str else "Unknown Title",
            author=row[3] if type(row[3]) is str else None,
            isbn10=row[4] if type(row[4]) is str else None,
            isbn13=row[5] if type(row[5]) is str else None,
            publication=row[6] if type(row[6]) is str else None,
            description=row[7] if type(row[7]) is str else None
        )

    def getBook(self, bookId: int) -> ExecuteResult[Optional[BookData]]:
        try:
            self.cursor.execute("SELECT bookId, image, title, author, isbn10, isbn13, publication, description FROM Book WHERE bookId = %s LIMIT 1", (bookId, ))
            result = self.cursor.fetchone()

            if type(result) is tuple:
                data = self._RowTypeToBookData(result)
            else:
                return (True, None)
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

        return (True, data)

    def removeBook(self, bookId: int) -> ExecuteResult[None]:
        try:
            self.cursor.execute("DELETE FROM Borrow WHERE bookId = %s", (bookId, ))
            self.cursor.execute("DELETE FROM BorrowHistory WHERE bookId = %s", (bookId, ))
            self.cursor.execute("DELETE FROM Book WHERE bookId = %s", (bookId, ))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                return (True, None)
            else:
                return (False, f"Not found book ID {bookId}")
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return False, str(err)

    def _listBookProcess(self, execute: Callable[[], Optional[Generator[MySQLCursorAbstract, None, None]]]) -> ExecuteResult[list[BookData]]:
        try:
            execute()
            result = self.cursor.fetchall()
            data: list[BookData] = []
            if type(result) is list:
                for row in result:
                    if type(row) is tuple:
                        data.append(self._RowTypeToBookData(row))
                return (True, data)
            else:
                return (False, str("Data process error"))
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

    def listBook(self) -> ExecuteResult[list[BookData]]:
        return self._listBookProcess(lambda: self.cursor.execute("SELECT bookId, image, title, author, isbn10, isbn13, publication, description FROM Book"))

    def clearBook(self) -> ExecuteResult[None]:
        try:
            self.cursor.execute("DELETE FROM Borrow")
            self.cursor.execute("DELETE FROM BorrowHistory")
            self.cursor.execute("DELETE FROM Book")
            self.connection.commit()
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return False, str(err)

        return (True, None)

    def searchBookByTitle(self, title: str) -> ExecuteResult[list[BookData]]:
        return self._listBookProcess(lambda: self.cursor.execute("SELECT bookId, image, title, author, isbn10, isbn13, publication, description FROM Book WHERE title LIKE %s", (f"%{title}%", )))

    def addUser(self, data: UserData) -> ExecuteResult[None]:
        try:
            self.cursor.execute(
                "INSERT INTO User (prefixName, firstName, lastName, email, phone, address) VALUES (%s, %s, %s, %s, %s, %s)",
                (data.prefixName, data.firstName, data.lastName, data.email, data.phone, data.address)
            )
            self.connection.commit()
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

        return (True, None)

    def removeUser(self, userId: int) -> ExecuteResult[None]:
        try:
            self.cursor.execute("DELETE FROM Borrow WHERE userId = %s", (userId, ))
            self.cursor.execute("DELETE FROM BorrowHistory WHERE userId = %s", (userId, ))
            self.cursor.execute("DELETE FROM User WHERE userId = %s", (userId, ))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                return (True, None)
            else:
                return (False, f"Not found user ID {userId}")
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

    def clearUser(self) -> ExecuteResult[None]:
        try:
            self.cursor.execute("DELETE FROM Borrow")
            self.cursor.execute("DELETE FROM BorrowHistory")
            self.cursor.execute("DELETE FROM User")
            self.connection.commit()
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

        return (True, None)

    def _RowTypeToUserData(self, row: RowType) -> UserData:
        return UserData(
            userId=(row[0] if type(row[0]) is int else None),
            prefixName=(row[1] if type(row[1]) is str else None),
            firstName=(row[2] if type(row[2]) is str else ""),
            lastName=(row[3] if type(row[3]) is str else ""),
            email=(row[4] if type(row[4]) is str else None),
            phone=(row[5] if type(row[5]) is str else None),
            address=(row[6] if type(row[6]) is str else None),
        )

    def getUser(self, userId: int) -> ExecuteResult[Optional[UserData]]:
        try:
            self.cursor.execute("SELECT userId, prefixName, firstName, lastName, email, phone, address FROM User WHERE userId = %s LIMIT 1", (userId, ))
            result = self.cursor.fetchone()

            if type(result) is tuple:
                data = self._RowTypeToUserData(result)
            else:
                return (True, None)
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

        return (True, data)

    def updateUser(self, data: UserData, old_data: Optional[UserData] = None) -> ExecuteResult[None]:
        if data.userId is None:
            return False, "data.userId is None"

        try:
            colvals: list[tuple[str, Union[str, None]]] = []

            if old_data is not None:
                if data.prefixName != old_data.prefixName: colvals.append(("prefixName", data.prefixName))
                if data.firstName != old_data.firstName: colvals.append(("firstName", data.firstName))
                if data.lastName != old_data.lastName: colvals.append(("lastName", data.lastName))
                if data.email != old_data.email: colvals.append(("email", data.email))
                if data.phone != old_data.phone: colvals.append(("phone", data.phone))
                if data.address != old_data.address: colvals.append(("address", data.address))
            else:
                colvals = [("prefixName", data.prefixName), ("firstName", data.firstName), ("lastName", data.lastName), ("email", data.email), ("phone", data.phone), ("address", data.address)]

            if len(colvals) > 0:
                self.cursor.execute("UPDATE User SET " + (", ".join([f"{i[0]}=%s" for i in colvals])) + " WHERE userId = %s", tuple([i[1] for i in colvals] + [data.userId]))
                self.connection.commit()
            else:
                return (False, "No update")
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return False, str(err)

        return (True, None)

    def _listUserProcess(self, execute: Callable[[], Optional[Generator[MySQLCursorAbstract, None, None]]]) -> ExecuteResult[list[UserData]]:
        try:
            execute()
            result = self.cursor.fetchall()
            data: list[UserData] = []
            if type(result) is list:
                for row in result:
                    if type(row) is tuple:
                        data.append(self._RowTypeToUserData(row))
                return (True, data)
            else:
                return (False, str("Data process error"))
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

    def listUser(self) -> ExecuteResult[list[UserData]]:
        return self._listUserProcess(lambda: self.cursor.execute("SELECT userId, prefixName, firstName, lastName, email, phone, address FROM User"))

    def searchUserByName(self, firstName: Optional[str], lastName: Optional[str]) -> ExecuteResult[list[UserData]]:
        sql = "SELECT userId, prefixName, firstName, lastName, email, phone, address FROM User WHERE "

        if firstName is not None and lastName is None:
            return self._listUserProcess(lambda: self.cursor.execute(sql + "firstName LIKE %s", (f"%{firstName}%", )))
        elif firstName is None and lastName is not None:
            return self._listUserProcess(lambda: self.cursor.execute(sql + "lastName LIKE %s", (f"%{lastName}%", )))
        else:
            return self._listUserProcess(lambda: self.cursor.execute(sql + "firstName LIKE %s AND lastName LIKE %s", (f"%{firstName}%", f"%{lastName}%")))

    def borrowBookGetReview(self, bookId: int, userId: int) -> ExecuteResult[BookBorrowReviewData]:
        try:
            self.cursor.execute("SELECT Book.bookId, User.userId, Book.title, User.prefixName, User.firstName, User.lastName, Book.image FROM Book, User WHERE Book.bookId = %s AND User.userId = %s", (bookId, userId))
            result = self.cursor.fetchall()
            if type(result) is list:
                for row in result:
                    if type(row) is tuple:
                        name = ""
                        if type(row[3]) is str: name += row[3] + "."
                        if type(row[4]) is str: name += row[4]
                        if type(row[5]) is str: name += " " + row[5]
                        return (True, BookBorrowReviewData(
                            bookId=(row[0] if type(row[0]) is int else 0),
                            userId=(row[1] if type(row[1]) is int else 0),
                            bookTitle=(row[2] if type(row[2]) is str else ""),
                            userName=name,
                            bookImage=(row[6] if type(row[6]) is bytes else b"")
                        ))
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

        return (False, "Not found User or Book.")

    def returnBookGetReview(self, bookId: int) -> ExecuteResult[BookReturnReviewData]:
        try:
            self.cursor.execute(
                "SELECT Borrow.bookId, Borrow.userId, Book.title, User.prefixName, User.firstName, User.lastName, Book.image, BorrowHistory.borrowed " +
                "FROM Borrow " +
                "INNER JOIN Book ON Borrow.bookId = Book.bookId " +
                "INNER JOIN User ON Borrow.userId = User.userId " +
                "INNER JOIN BorrowHistory ON Borrow.historyId = BorrowHistory.historyId " +
                "WHERE Borrow.bookId = %s AND BorrowHistory.returned IS NULL", (bookId, ))
            result = self.cursor.fetchone()
            if type(result) is tuple:
                name = ""
                if type(result[3]) is str: name += result[3] + "."
                if type(result[4]) is str: name += result[4]
                if type(result[5]) is str: name += " " + result[5]
                return (True, BookReturnReviewData(
                    bookId=(result[0] if type(result[0]) is int else 0),
                    userId=(result[1] if type(result[1]) is int else 0),
                    bookTitle=(result[2] if type(result[2]) is str else ""),
                    userName=name,
                    bookImage=(result[6] if type(result[6]) is bytes else b""),
                    borrowed=(result[7] if type(result[7]) is datetime else datetime.fromtimestamp(0))
                ))
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

        return (False, "Not found this book.")

    def borrowBook(self, bookId: int, userId: int) -> ExecuteResult[None]:
        try:
            self.cursor.execute("INSERT INTO BorrowHistory (bookId, userId, borrowed) VALUES (%s, %s, %s)", (bookId, userId, datetime.now()))
            self.cursor.execute("INSERT INTO Borrow (bookId, userId, historyId) VALUES (%s, %s, %s)", (bookId, userId, self.cursor.lastrowid))
            self.connection.commit()
            return (True, None)
        except MysqlError as err:
            self.connection.rollback()
            if err.errno == ER_DUP_ENTRY:
                return (False, "This book has been borrowed.\n\n" + str(err))
            return (False, str(err))
        except Exception as err:
            return False, str(err)

    def returnBook(self, bookId: int) -> ExecuteResult[None]:
        try:
            self.cursor.execute("UPDATE BorrowHistory SET returned = %s WHERE historyId = (SELECT historyId FROM Borrow WHERE bookId = %s)", (datetime.now(), bookId))
            rowcount = self.cursor.rowcount
            self.cursor.execute("DELETE FROM Borrow WHERE bookId = %s", (bookId, ))
            rowcount += self.cursor.rowcount
            self.connection.commit()
            if rowcount > 0:
                return (True, None)
            else:
                return (False, f"This book ID was not found in the borrowing list.")
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return False, str(err)

    def _RowTypeToBorrowHistory(self, row: RowType) -> BookBorrowHistoryData:
        name = ""
        if type(row[4]) is str: name += row[4] + "."
        if type(row[5]) is str: name += row[5]
        if type(row[6]) is str: name += row[6]

        return BookBorrowHistoryData(
            historyId=(row[0] if type(row[0]) is int else 0),
            bookId=(row[1] if type(row[1]) is int else 0),
            bookTitle=(row[2] if type(row[2]) is str else ""),
            userId=(row[3] if type(row[3]) is int else 0),
            userName=name,
            borrowed=(row[7] if type(row[7]) is datetime else datetime.fromtimestamp(0)),
            returned=(row[8] if type(row[8]) is datetime else None)
        )

    def _listBorrowHistoryProcess(self, execute: Callable[[], Optional[Generator[MySQLCursorAbstract, None, None]]]) -> ExecuteResult[list[BookBorrowHistoryData]]:
        try:
            execute()
            result = self.cursor.fetchall()
            data: list[BookBorrowHistoryData] = []
            if type(result) is list:
                for row in result:
                    if type(row) is tuple:
                        data.append(self._RowTypeToBorrowHistory(row))
                return (True, data)
            else:
                return (False, str("Data process error"))
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

    def listBorrowHistory(self) -> ExecuteResult[list[BookBorrowHistoryData]]:
        sql = (
            "SELECT BorrowHistory.historyId, BorrowHistory.bookId, Book.title, BorrowHistory.userId, User.prefixName, User.firstName, User.lastName, BorrowHistory.borrowed, BorrowHistory.returned " +
            "FROM BorrowHistory " +
            "INNER JOIN Book ON BorrowHistory.bookId = Book.bookId " +
            "INNER JOIN User ON BorrowHistory.userId = User.userId"
        )
        return self._listBorrowHistoryProcess(lambda: self.cursor.execute(sql))

    def searchBorrowHistoryByBookOrUserId(self, bookId: Optional[int], userId: Optional[int], borrowing: Optional[bool] = None, returned: Optional[bool] = None) -> ExecuteResult[list[BookBorrowHistoryData]]:
        sql = (
            "SELECT BorrowHistory.historyId, BorrowHistory.bookId, Book.title, BorrowHistory.userId, User.prefixName, User.firstName, User.lastName, BorrowHistory.borrowed, BorrowHistory.returned " +
            "FROM BorrowHistory " +
            "INNER JOIN Book ON BorrowHistory.bookId = Book.bookId " +
            "INNER JOIN User ON BorrowHistory.userId = User.userId " +
            "WHERE "
        )

        sql2 = ""
        values: Union[tuple[int], tuple[int, int], tuple] = ()

        if bookId is not None and userId is None:
            sql2 = "BorrowHistory.bookId = %s"
            values = (bookId, )
        elif bookId is None and userId is not None:
            sql2 = "BorrowHistory.userId = %s"
            values = (userId, )
        elif bookId is not None and userId is not None:
            sql2 = "BorrowHistory.bookId = %s AND BorrowHistory.userId = %s"
            values = (bookId, userId)
        else:
            sql2 = ""

        if borrowing is True:
            sql2 = (" AND " if sql2 != "" else "") + "BorrowHistory.returned IS NULL"
        elif returned is True:
            sql2 = (" AND " if sql2 != "" else "") + "BorrowHistory.returned IS NOT NULL"

        return self._listBorrowHistoryProcess(lambda: self.cursor.execute(sql + sql2, values))

    def updateBorrowHistory(self, data: BookBorrowHistoryData, old_data: Optional[BookBorrowHistoryData] = None) -> ExecuteResult[None]:
        if data.userId is None:
            return False, "data.userId is None"

        try:
            colvals: list[tuple[str, Union[int, datetime, None]]] = []

            if old_data is not None:
                if data.bookId != old_data.bookId: colvals.append(("bookId", data.bookId))
                if data.userId != old_data.userId: colvals.append(("userId", data.userId))
                if data.borrowed != old_data.borrowed: colvals.append(("borrowed", data.borrowed))
                if data.returned != old_data.returned: colvals.append(("returned", data.returned))
            else:
                colvals = [("bookId", data.bookId), ("userId", data.userId), ("borrowed", data.borrowed), ("returned", data.returned)]
            if len(colvals) > 0:
                if old_data is not None and old_data.returned is None and data.returned is not None:
                    self.cursor.execute("DELETE FROM Borrow WHERE bookId = %s", (old_data.bookId, ))
                elif old_data is not None and old_data.returned is not None and data.returned is None:
                    self.cursor.execute("INSERT INTO Borrow (bookId, userId, historyId) VALUES (%s, %s, %s)", (data.bookId, data.userId, data.historyId))
                self.cursor.execute("UPDATE BorrowHistory SET " + (", ".join([f"{i[0]}=%s" for i in colvals])) + " WHERE historyId = %s", tuple([i[1] for i in colvals] + [data.historyId]))
                self.connection.commit()
            else:
                return (False, "No update")
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return False, str(err)

        return (True, None)

    def removeBorrowHistory(self, historyId: int) -> ExecuteResult[None]:
        try:
            self.cursor.execute("DELETE FROM Borrow WHERE historyId = %s", (historyId, ))
            self.cursor.execute("DELETE FROM BorrowHistory WHERE historyId = %s", (historyId, ))
            self.connection.commit()
            if self.cursor.rowcount > 0:
                return (True, None)
            else:
                return (False, f"Not found history ID {historyId}")
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

    def _getOneCountResult(self, execute: Callable[[], Optional[Generator[MySQLCursorAbstract, None, None]]]) -> ExecuteResult[int]:
        try:
            execute()
            result = self.cursor.fetchone()
            if type(result) is tuple and type(result[0]) is int:
                return (True, result[0])
            return (True, -1)
        except MysqlError as err:
            self.connection.rollback()
            return (False, str(err))
        except Exception as err:
            return (False, str(err))

    def getBookCount(self) -> ExecuteResult[int]:
        return self._getOneCountResult(lambda: self.cursor.execute("SELECT COUNT(*) FROM Book"))

    def getUserCount(self) -> ExecuteResult[int]:
        return self._getOneCountResult(lambda: self.cursor.execute("SELECT COUNT(*) FROM User"))

    def getBorrowingCount(self) -> ExecuteResult[int]:
        return self._getOneCountResult(lambda: self.cursor.execute("SELECT COUNT(*) FROM Borrow"))

    def getReturnedCount(self) -> ExecuteResult[int]:
        return self._getOneCountResult(lambda: self.cursor.execute("SELECT COUNT(*) FROM BorrowHistory WHERE returned IS NOT NULL"))

    def getAllTimeBorrowedCount(self) -> ExecuteResult[int]:
        return self._getOneCountResult(lambda: self.cursor.execute("SELECT COUNT(*) FROM BorrowHistory"))

    def close(self):
        self.cursor.close()
        self.connection.close()

Session = DBSession()
