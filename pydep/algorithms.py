import enum
import random
from typing import Sequence

from pydep import opts
from pydep.costs import CostFunction
from pydep.deps import Dependency
from pydep.logs import stream_logger
from pydep.tests import TestRunner
from pydep.versions import VersionMapping

logger = stream_logger(__name__)


class AlgorithmsAvailable(str, enum.Enum):
    backtrack = "Backtrack"
    random = "Random"


class Algorithm:
    def __init__(
        self,
        deps: Sequence[Dependency],
        runner: TestRunner,
        cost_func: CostFunction,
        optimizer: opts.Optimizer,
    ) -> None:
        self.deps = deps
        self.runner = runner
        self.cost_func = cost_func
        self.optimizer = optimizer

    def run(self) -> opts.AlgorithmOutput:
        """
        Run the algorithm, it returns a mapping of each dependency to the
        selected version.
        """

        raise NotImplementedError


class Backtrack(Algorithm):
    def run(self):
        self._run(0, {})
        return self.optimizer.optimum

    def _run(self, p, pinned: VersionMapping):
        if p >= len(self.deps):
            if all(self.runner.run_all(pinned)):
                self.optimizer.relax(self.cost_func(pinned), pinned.copy())

            return

        cur_dep = self.deps[p]
        for v in cur_dep.spversions:
            pinned[cur_dep] = v
            self._run(p + 1, pinned)
            pinned.pop(cur_dep)


class Random(Algorithm):
    def __init__(
        self,
        deps: Sequence[Dependency],
        runner: TestRunner,
        cost_func: CostFunction,
        optimizer: opts.Optimizer,
        **kwargs,
    ) -> None:
        super().__init__(deps, runner, cost_func, optimizer)
        self.iterations = kwargs["iterations"]
        random.seed(0) # debugging only

    def run(self):
        logger.info("Starting Random algorithm")

        for it in range(self.iterations):
            logger.debug(f"On iteration {it}")

            pinned = {}
            for dep in self.deps:
                ver = random.choice(dep.spversions)
                pinned[dep] = ver

            if all(self.runner.run_all(pinned)):
                cost = self.cost_func(pinned)
                logger.debug(f"Succeded with cost={cost}")
                self.optimizer.relax(cost, pinned.copy())

        return self.optimizer.optimum
