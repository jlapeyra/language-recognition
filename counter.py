import collections
from typing import Any

class Counter(collections.Counter):
    __total = 0
    def total(self):
        return self.__total
    def __setitem__(self, __key: Any, __value: int) -> None:
        self.__total += __value - self[__key]
        return super().__setitem__(__key, __value)
