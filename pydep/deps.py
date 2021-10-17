from __future__ import annotations
from typing import List
from pydep.versions import VersionRel, Version

class Dependency:
    def __init__(
        self,
        name: str,
        versions: List[Version],
        hints: List[VersionRel],
        depends: List[str]
    ) -> None:
        self.name = name
        self.versions = sorted(versions)
        self.hints = hints
        self.depends = depends

    def __eq__(self, other: object) -> bool:
        if self.__class__ is other.__class__:
            return self.name == other.name
        raise NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}: {self.name}'

