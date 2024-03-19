from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Union, Optional, Literal

T = TypeVar('T')

@dataclass
class UserData:
    userId: Optional[int]
    prefixName: Optional[str]
    firstName: str
    lastName: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]

ExecuteResult = Union[
    tuple[Literal[True], T],
    tuple[Literal[False], str]
]

@dataclass
class BookData:
    bookId: Optional[int]
    image: Optional[bytes]
    title: str
    author: Optional[str]
    isbn10: Optional[str]
    isbn13: Optional[str]
    publication: Optional[str]
    description: Optional[str]

@dataclass
class BookBorrowHistoryData:
    historyId: int
    bookId: int
    bookTitle: str
    userId: int
    userName: str
    borrowed: datetime
    returned: Optional[datetime]

@dataclass
class BookBorrowReviewData:
    bookId: int
    userId: int
    bookTitle: str
    userName: str
    bookImage: Optional[bytes]

@dataclass
class BookReturnReviewData(BookBorrowReviewData):
    borrowed: datetime
