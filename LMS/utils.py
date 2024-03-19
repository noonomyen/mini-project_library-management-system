from typing import Iterable, Any, Generator

def exclude_range(start: int, stop: int, exclude: Iterable[int], step: int = 1) -> Generator[int, Any, None]:
    i = start

    while i < stop:
        if i not in exclude:
            yield i

        i += step
