from typing import Tuple
from pydep.versions import VersionMapping

AlgorithmOutput = Tuple[float, VersionMapping]


class NotSolutionException(Exception):
    pass


class Optimizer:
    def __init__(self) -> None:
        self.opt = None
        self.mapping = None

    def relax(self, cost: float, mapping: VersionMapping):
        raise NotImplementedError

    @property
    def optimum(self):
        if self.opt is None or self.mapping is None:
            raise NotSolutionException

        return self.opt, self.mapping


class Max(Optimizer):
    def relax(self, cost: float, mapping: VersionMapping):
        if self.opt is None or cost > self.opt:
            self.opt, self.mapping = cost, mapping


class Min(Optimizer):
    def relax(self, cost: float, mapping: VersionMapping):
        if self.opt is None or cost < self.opt:
            self.opt, self.mapping = cost, mapping
