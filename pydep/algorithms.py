import enum
import random
import bisect
from typing import Sequence, Optional

from pydep import opts
from pydep.costs import CostFunction
from pydep.deps import Dependency
from pydep.logs import stream_logger
from pydep.tests import TestRunner
from pydep.versions import VersionMapping

logger = stream_logger(__name__)
random.seed(0)  # debug


class AlgorithmsAvailable(str, enum.Enum):
    backtrack = "Backtrack"
    random = "Random"
    pso = "PSO"


class Algorithm:
    def __init__(
        self,
        deps: Sequence[Dependency],
        runner: TestRunner,
        cost_func: CostFunction,
        optimizer: opts.Optimizer,
        **kwargs,
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
        self.iterations = kwargs.get("iterations", 1000)

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


class PSO(Algorithm):
    def __init__(
        self,
        deps: Sequence[Dependency],
        runner: TestRunner,
        cost_func: CostFunction,
        optimizer: opts.Optimizer,
        **kwargs,
    ) -> None:
        super().__init__(deps, runner, cost_func, optimizer)
        self.inimapping: VersionMapping = kwargs["inimapping"]
        self.particles = kwargs.get("particles", 10)
        self.iterations = kwargs.get("iterations", 100)
        self.w = kwargs.get("w", 1)
        self.phi_p = kwargs.get("phi_p", 1)
        self.phi_g = kwargs.get("phi_g", 1)

    def run(self):
        inivec = [
            bisect.bisect_left(dep.spversions, ver)
            for dep, ver in self.inimapping.items()
        ]

        logger.debug("Computing initial vectors")

        xs = [inivec]
        for _ in range(self.particles - 1):
            x = []
            for dep in self.deps:
                x.append(random.uniform(0, len(dep.spversions) - 1))

            xs.append(x)

        p = []
        vs = []
        opt_cls = self.optimizer.__class__

        for x in xs:
            logger.debug(f"vec: {x}")

            v = []
            for dep in self.deps:
                lo, up = 0, len(dep.spversions) - 1
                v.append(random.uniform(-(up - lo), up - lo))

            logger.debug(f"speed = {v}")
            vs.append(v)

            mp = self.float_to_mapping(x)
            p.append(opt_cls())

            if all(self.runner.run_all(mp)):
                logger.debug(f"mapping = {mp.items()}")
                cost = self.cost_func(mp)
                logger.debug(f"tests succeeded, cost = {cost}")
                p[-1].relax(cost, x)
                self.optimizer.relax(cost, x)  # type: ignore

        logger.debug("Done initialization, starting algorithm")

        for _ in range(self.iterations):
            xsnew = []
            for i, x in enumerate(xs):
                for d in range(len(x)):
                    r_p = random.random()
                    r_g = random.random()

                    lo, up = (0, len(self.deps[d].spversions) - 1)
                    r = (lo, up)
                    delta_i = random.uniform(*r)
                    delta_glob = random.uniform(*r)

                    if p[i].mapping is not None:
                        delta_i = p[i].mapping[d] - x[d]

                    if self.optimizer.mapping is not None:
                        delta_glob = self.optimizer.mapping[d] - x[d]

                    vs[i][d] = (
                        self.w * vs[i][d]
                        + self.phi_p * r_p * delta_i
                        + self.phi_g * r_g * delta_glob
                    )

                newx = []
                for d, val in enumerate(x):
                    lo, up = (0, len(self.deps[d].spversions) - 1)
                    nx = val + vs[i][d]

                    if nx < lo - 0.5 or nx > up + 0.4:
                        nx = random.uniform(lo, up)

                    newx.append(nx)

                xsnew.append(newx)

                mp = self.float_to_mapping(newx)

                if all(self.runner.run_all(mp)):
                    cost = self.cost_func(mp)
                    logger.debug(f"tests succeeded, cost = {cost}")
                    p[i].relax(cost, newx)
                    self.optimizer.relax(cost, newx)  # type: ignore

            xs = xsnew

        cost, way = self.optimizer.optimum
        way = self.float_to_mapping(way)
        return cost, way

    def float_to_mapping(self, vec: Sequence[float]) -> VersionMapping:
        res = {}
        for i, x in enumerate(vec):
            dx = round(x)
            assert 0 <= dx < len(self.deps[i].spversions)
            res[self.deps[i]] = self.deps[i].spversions[dx]

        return res
