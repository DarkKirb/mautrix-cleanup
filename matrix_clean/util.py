from itertools import islice
from typing import Iterable, Iterator, TypeVar

T = TypeVar('T')

def batch(iterable: Iterable[T], n: int) -> Iterator[list[T]]:
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk:
            return
        yield chunk
