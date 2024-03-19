CREATE DATABASE LMS_DB;

USE LMS_DB;

CREATE TABLE User (
    userId INT NOT NULL AUTO_INCREMENT,
    prefixName VARCHAR(16),
    firstName VARCHAR(32) NOT NULL,
    lastName VARCHAR(32) NOT NULL,
    email VARCHAR(64),
    phone VARCHAR(16),
    address VARCHAR(128),
    PRIMARY KEY (userId)
) ENGINE=InnoDB;

CREATE TABLE Book (
    bookId INT NOT NULL AUTO_INCREMENT,
    image MEDIUMBLOB,
    title VARCHAR(64) NOT NULL,
    author VARCHAR(64),
    isbn13 VARCHAR(13),
    isbn10 VARCHAR(10),
    publication VARCHAR(64),
    description VARCHAR(1024),
    PRIMARY KEY (bookId)
) ENGINE=InnoDB;

CREATE TABLE BorrowHistory (
    historyId INT NOT NULL AUTO_INCREMENT,
    bookId INT NOT NULL,
    userId INT NOT NULL,
    borrowed DATETIME NOT NULL,
    returned DATETIME DEFAULT NULL,
    PRIMARY KEY (historyId),
    FOREIGN KEY (bookId) REFERENCES Book(bookId),
    FOREIGN KEY (userId) REFERENCES User(userId)
) ENGINE=InnoDB;

CREATE TABLE Borrow (
    bookId INT NOT NULL,
    userId INT NOT NULL,
    historyId INT NOT NULL,
    PRIMARY KEY (bookId),
    FOREIGN KEY (bookId) REFERENCES Book(bookId),
    FOREIGN KEY (userId) REFERENCES User(userId),
    FOREIGN KEY (historyId) REFERENCES BorrowHistory(historyId)
) ENGINE=InnoDB;
