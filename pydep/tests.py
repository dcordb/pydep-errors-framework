from dataclasses import dataclass
from typing import List, Mapping
from pathlib import Path
from collections import namedtuple
from pydep.rels import Version
from pydep.deps import Dependency

class Test:
    def run(self, fixed_versions: Mapping[Dependency, Version]) -> bool:
        raise NotImplementedError

ValidInterval = namedtuple('ValidInterval', ['min', 'max'])

@dataclass
class VirtualTest(Test):
    '''
    A virtual test:
        `true_when` holds 'conditions' that tell whether to return True or False for
        this virtual test.
    '''

    true_when: List[Mapping[Dependency, ValidInterval]]

    def run(self, fixed_versions: Mapping[Dependency, Version]) -> bool:
        for conditions in self.true_when:
            for dep, interval in conditions.items():
                cur_ver = fixed_versions[dep]
                
                if interval.min > cur_ver or cur_ver > interval.max:
                    break

            else:
                return True

        return False

@dataclass
class PytestDirTest(Test):
    directory: Path

