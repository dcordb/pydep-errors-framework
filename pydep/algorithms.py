from typing import Sequence
from pydep.versions import VersionMapping
from pydep.costs import CostFunction
from pydep.tests import TestRunner
from pydep.deps import Dependency
from pydep import opts


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
        for v in cur_dep.spec_versions():
            pinned[cur_dep] = v
            self._run(p + 1, pinned)
            pinned.pop(cur_dep)
