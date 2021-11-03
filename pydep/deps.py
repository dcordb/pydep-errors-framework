from __future__ import annotations
from typing import List, Sequence
from packaging.version import Version
from packaging.specifiers import SpecifierSet


class Dependency:
    def __init__(
        self,
        name: str,
        versions: Sequence[Version],
        specifier: SpecifierSet = SpecifierSet(),
    ) -> None:
        self.name = name
        self.versions = sorted(versions)
        self.specifier = specifier

    def __eq__(self, other: object) -> bool:
        if self.__class__ is other.__class__:
            return self.name == other.name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} {self.name}"

    def spec_versions(self) -> List[Version]:
        """
        Returns a list of versions that conforms with the specifier
        """

        return [ver for ver in self.versions if ver in self.specifier]
