from typing import Tuple
from math import log
from pydep.versions import VersionMapping

BASE = 30


def tuple_to_float(tup: Tuple[int, ...]) -> float:
    res = 0
    for d in tup:
        res = res * BASE + log(d)

    return res


class CostFunction:
    def __call__(self, mapping: VersionMapping) -> float:
        raise NotImplementedError


class Sum(CostFunction):
    def __call__(self, mapping: VersionMapping) -> float:
        return sum(tuple_to_float(v.release) for v in mapping.values())
