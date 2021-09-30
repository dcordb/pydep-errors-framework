from typing import List, Mapping
from src.tests import Test
from src.rels import Version
from src.deps import DepsGraph, Dependency

class Algorithm:
    def __init__(self, graph: DepsGraph, tests: List[Test]) -> None:
        self.graph = graph
        self.tests = tests

    def run(self) -> Mapping[Dependency, Version]:
        '''
        Run the algorithm, it returns a mapping of each dependency to the
        selected version.
        '''

        raise NotImplementedError

