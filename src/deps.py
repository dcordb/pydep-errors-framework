from dataclasses import dataclass
from typing import List, Mapping
from src.rels import VersionRel, Version

class Dependency:
    def __init__(
        self,
        name: str,
        versions: List[Version],
        hints: List[VersionRel]
    ) -> None:
        self.name = name
        self.versions = sorted(versions)
        self.hints = hints

    def __eq__(self, other: object) -> bool:
        if self.__class__ is other.__class__:
            return self.name == other.name
        raise NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}: {self.name}'

@dataclass
class DepsGraph:
    nodes: List[Dependency]
    adjs: Mapping[Dependency, List[Dependency]]

