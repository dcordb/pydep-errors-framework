from dataclasses import dataclass
from typing import List, Mapping, Sequence
from pathlib import Path
from pydep.versions import VersionRange, VersionMapping
from pydep.deps import Dependency


class Test:
    """Abstract base class for Tests"""

    def run(self, pinned_vers: VersionMapping) -> bool:
        raise NotImplementedError


@dataclass
class VirtualTest(Test):
    """
    A virtual test:
        `true_when` holds 'conditions' that tell whether to return True or False for
        this virtual test.
    """

    true_when: Sequence[Mapping[Dependency, VersionRange]]

    def run(self, pinned_vers: VersionMapping) -> bool:
        for conditions in self.true_when:
            for dep, range in conditions.items():
                cur_ver = pinned_vers[dep]

                if range.min > cur_ver or cur_ver > range.max:
                    break

            else:
                return True

        return False


@dataclass
class PytestDirTest(Test):
    directory: Path


class TestRunner:
    def __init__(self, tests: Sequence[Test]) -> None:
        self.tests = tests

    def run_all(self, pinned_vers: VersionMapping) -> List[bool]:
        raise NotImplementedError


class LinearRunner(TestRunner):
    def run_all(self, pinned_vers: VersionMapping) -> List[bool]:
        return [test.run(pinned_vers) for test in self.tests]
