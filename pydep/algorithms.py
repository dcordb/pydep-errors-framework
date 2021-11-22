import bisect
import enum
import logging
from math import exp
import random
from typing import Optional, Sequence

from pydep import opts
from pydep.costs import CostFunction
from pydep.deps import Dependency
from pydep.tests import TestRunner
from pydep.versions import VersionMapping

logger = logging.getLogger(__name__)
random.seed(0)  # debug


class AlgorithmsAvailable(str, enum.Enum):
    backtrack = "Backtrack"
    random = "Random"
    simann = "SimAnn"
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
    desc_name = "Backtracking"

    class StopBacktrack(Exception):
        pass

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
        try:
            self._run(0, {})
        except Backtrack.StopBacktrack:
            pass

        return self.optimizer.optimum

    def _run(self, p, pinned: VersionMapping):
        if p >= len(self.deps):
            if all(self.runner.run_all(pinned)):
                self.optimizer.relax(self.cost_func(pinned), pinned.copy())

            self.iterations -= 1

            if self.iterations <= 0:
                raise Backtrack.StopBacktrack()

            return

        cur_dep = self.deps[p]
        for v in cur_dep.spversions:
            pinned[cur_dep] = v
            self._run(p + 1, pinned)
            pinned.pop(cur_dep)


class Random(Algorithm):
    desc_name = "Randomized"

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


class SimAnn(Algorithm):
    desc_name = "SimAnn"

    def __init__(
        self,
        deps: Sequence[Dependency],
        runner: TestRunner,
        cost_func: CostFunction,
        optimizer: opts.Optimizer,
        **kwargs,
    ) -> None:
        super().__init__(deps, runner, cost_func, optimizer, **kwargs)
        self.inimapping: VersionMapping = kwargs["inimapping"]
        self.iterations = kwargs.get("iterations", 1000)
        self.prob_restart: float = kwargs.get("prob_restart", 0.1)
        self._delta = 1 if isinstance(self.optimizer, opts.Min) else -1

    def run(self):
        s = self.inimapping
        cur = self._delta * self.cost_func(s)

        if all(self.runner.run_all(s)):
            self.optimizer.relax(cur, s.copy())

        for x in range(self.iterations):
            temp = 2 - (x + 1) / self.iterations
            snew = self.random_neighbor(s)

            if snew is None or random.random() < self.prob_restart:
                logger.debug("Restarting")
                s = self.random_mapping(s)
                continue

            if not all(self.runner.run_all(snew)):
                continue

            logger.debug(f"{snew} is a factible state")

            new_cost = self._delta * self.cost_func(snew)
            self.optimizer.relax(new_cost, snew.copy())

            if self.prob(cur, new_cost, temp) >= random.random():
                s = snew
                cur = new_cost

        if self.optimizer.opt is not None:
            self.optimizer.opt *= self._delta

        return self.optimizer.optimum

    def prob(self, cur: float, new_cost: float, temp: float) -> float:
        if new_cost < cur:
            return 1

        return exp(-(new_cost - cur) / temp)

    def random_mapping(self, mapping: VersionMapping) -> VersionMapping:
        resp = mapping.copy()

        for dep in mapping:
            resp[dep] = random.choice(dep.spversions)

        return resp

    def random_neighbor(self, mapping: VersionMapping) -> Optional[VersionMapping]:
        vec = [bisect.bisect_left(dep.spversions, ver) for dep, ver in mapping.items()]

        cands = []
        for i, dep in enumerate(mapping):
            if vec[i] + 1 < len(dep.spversions):
                cands.append((dep, vec[i] + 1))

            if vec[i] > 0:
                cands.append((dep, vec[i] - 1))

        if not cands:
            return None

        target = random.choice(cands)

        rmap = mapping.copy()
        assert target[0] in rmap
        dep = target[0]
        rmap[dep] = dep.spversions[target[1]]

        return rmap


class PSO(Algorithm):
    desc_name = "PSO"

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
