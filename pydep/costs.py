from typing import Callable
from math import log
from packaging.version import Version
from pydep.versions import VersionMapping

BASE = 30


def version_to_float(version: Version) -> float:
    tup = version.release

    res = 0
    for d in tup:
        res = res * BASE + log(d)

    return res


class CostFunction:
    def __init__(self, callable: Callable[[Version], float]) -> None:
        self.version_to_float = callable

    def __call__(self, mapping: VersionMapping) -> float:
        raise NotImplementedError


class Sum(CostFunction):
    def __call__(self, mapping: VersionMapping) -> float:
        return sum(self.version_to_float(v) for v in mapping.values())
