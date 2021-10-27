from typing import List
from pydep.versions import VersionMapping
from pydep.costs import CostFunction
from pydep.tests import Test
from pydep.deps import Dependency


class Algorithm:
    def __init__(
        self, deps: List[Dependency], tests: List[Test], cost_func: CostFunction
    ) -> None:
        self.deps = deps
        self.tests = tests
        self.cost_func = cost_func

    def run(self) -> VersionMapping:
        """
        Run the algorithm, it returns a mapping of each dependency to the
        selected version.
        """

        raise NotImplementedError
