from typing import Tuple
from pydep.versions import VersionMapping


def tuple_to_int(tup: Tuple[int, ...]):
    res = 0
    for d in tup:
        res = res * 10 + d

    return res


class CostFunction:
    def __init__(self, mapping: VersionMapping) -> None:
        self.mapping = mapping

    def __call__(self) -> float:
        raise NotImplementedError


class Sum(CostFunction):
    def __call__(self) -> float:
        return sum(tuple_to_int(v.release) for v in self.mapping.values())
