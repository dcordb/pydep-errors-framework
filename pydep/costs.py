from typing import Tuple
from pydep.versions import VersionMapping


def tuple_to_int(tup: Tuple[int, ...]):
    res = 0
    for d in tup:
        res = res * 10 + d

    return res


class CostFunction:
    def __call__(self, mapping: VersionMapping) -> float:
        raise NotImplementedError


class Sum(CostFunction):
    def __call__(self, mapping: VersionMapping) -> float:
        return sum(tuple_to_int(v.release) for v in mapping.values())
