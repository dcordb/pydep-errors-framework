from typing import List, Mapping
from pydep.tests import Test
from pydep.rels import Version
from pydep.deps import Dependency

class Algorithm:
    def __init__(self, deps: List[Dependency], tests: List[Test]) -> None:
        self.deps = deps
        self.tests = tests

    def run(self) -> Mapping[Dependency, Version]:
        '''
        Run the algorithm, it returns a mapping of each dependency to the
        selected version.
        '''

        raise NotImplementedError

