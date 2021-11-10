from __future__ import annotations
from typing import Sequence

from packaging.requirements import Requirement
from packaging.version import Version


class Dependency:
    def __init__(
        self, name: str, versions: Sequence[Version], org_req: Requirement
    ) -> None:
        self.name = name
        self.versions = sorted(versions)
        self.org_req = org_req

        # versions that conform to specifier
        self.spversions = [
            ver for ver in self.versions if ver in self.org_req.specifier
        ]

    def __eq__(self, other: object) -> bool:
        if self.__class__ is other.__class__:
            return self.name == other.name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} {self.name}"
