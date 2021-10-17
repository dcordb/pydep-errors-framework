from dataclasses import dataclass
from typing import List, Mapping
from pathlib import Path
from pydep.versions import Version, VersionRange
from pydep.deps import Dependency

class Test:
    def run(self, fixed_versions: Mapping[Dependency, Version]) -> bool:
        raise NotImplementedError

@dataclass
class VirtualTest(Test):
    '''
    A virtual test:
        `true_when` holds 'conditions' that tell whether to return True or False for
        this virtual test.
    '''

    true_when: List[Mapping[Dependency, VersionRange]]

    def run(self, fixed_versions: Mapping[Dependency, Version]) -> bool:
        for conditions in self.true_when:
            for dep, range in conditions.items():
                cur_ver = fixed_versions[dep]
                
                if range.min > cur_ver or cur_ver > range.max:
                    break

            else:
                return True

        return False

@dataclass
class PytestDirTest(Test):
    directory: Path

