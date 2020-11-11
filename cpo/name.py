
from abc import ABC
from typing import Optional

from .atomic import AtomicCounter

class NameGenerator:

    def __init__(self, _kind: str) -> None:
        self._kind = _kind
        self._occurs = AtomicCounter()

    def _gen_name(self, name: str) -> str:
        if name is None:
            return f'{self._kind}-{next(self._occurs)}'
        return name

    def _new_name(self, kind: Optional[str] = None) -> str:
        if kind is None:
            kind = self._kind
        return f'{kind}-{next(self._occurs)}'

class Named(ABC):

    def __init__(self):
        self._name: str = "<anonymous>"
        self._name_generator: Optional[NameGenerator] = None

    @property
    def name(self) -> str:
        return self._name

    def with_name(self, __name: str) -> str:
        self._name = __name
        return self._name

    @property
    def name_generator(self) -> NameGenerator:
        if self._name_generator is None:
            self._name_generator = NameGenerator('!?!?')
        return self._name_generator

    def set_name(self, name: str):
        self._name = self.name_generator._gen_name(name)

    def __str__(self) -> str:
        return self.name

