from typing import Callable
from itertools import cycle

from .errors import ISBNValueError

class ISBN:
    digit_length: int
    digits: str
    check_digit: str

    calc_check_digit: Callable[[], str]

    def __init__(self, chars: str) -> None: ...

    def set_digits(self, chars: str) -> None:
        chars_len = len(chars)
        if chars_len == self.digit_length:
            self.digits = chars[:-1]
            self.check_digit = chars[-1]
        elif chars_len == (self.digit_length - 1):
            self.digits = chars
            self.check_digit = self.calc_check_digit()
        else:
            raise ISBNValueError()

    def recalc_check_digit(self) -> None:
        self.check_digit = self.calc_check_digit()

    def verify(self) -> bool:
        return self.check_digit == self.calc_check_digit()

    def __str__(self) -> str:
        return self.digits + self.check_digit

class ISBN10(ISBN):
    digit_length = 10

    def __init__(self, chars: str) -> None:
        if type(chars) != str or not chars[:9].isnumeric() or (len(chars) == 10 and not chars[9].isnumeric() and chars[9] != "X"):
            raise ISBNValueError()

        self.set_digits(chars)

    def calc_check_digit(self) -> str:
        sum = 0
        for idx, digit in enumerate(self.digits):
            sum += (10 - idx) * (ord(digit) - 48)

        add = 11
        for i in range(11):
            if (sum + i) % 11 == 0:
                add = i

        if add == 10:
            return "X"
        return chr(add + 48)

class ISBN13(ISBN):
    digit_length = 13

    def __init__(self, chars: str) -> None:
        if type(chars) != str or not chars[:12].isnumeric():
            raise ISBNValueError()

        self.set_digits(chars)

    def calc_check_digit(self) -> str:
        sum = 0
        for mul, digit in zip(cycle((1, 3)), self.digits):
            sum += mul * (ord(digit) - 48)

        return chr(((10 - sum) % 10) + 48)
