from typing import Tuple, List
from packaging.version import Version
from packaging.specifiers import SpecifierSet
from pydep.deps import Dependency
from pydep.tests import VirtualTest
from pydep.versions import VersionRange

def parse_virtual_config(d: dict) -> Tuple[List[Dependency], VirtualTest]:
    deps = []
    for name, vals in d['dependencies'].items():
        vals['versions'] = list(map(Version, vals['versions']))
        vals['specifier'] = SpecifierSet(vals['specifier'])
        deps.append(Dependency(name, **vals))

    true_when = []
    for test in d['tests']:
        for cond in test['true_when']:
            for key in cond:
                x, y = map(Version, cond[key])
                cond[key] = VersionRange(x, y)

            true_when.append(cond)

    return deps, VirtualTest(true_when)

