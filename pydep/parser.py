from typing import Tuple, List
from pydep.deps import Dependency
from pydep.tests import VirtualTest
from pydep.versions import EQUIVS, VersionRange

def str_to_int_tuple(s: str):
    return tuple(map(int, s.split('.')))

def str_to_rels(s: str):
    cls = EQUIVS[s[:2]]
    return cls(str_to_int_tuple(s[2:]))

def parse_virtual_config(d: dict) -> Tuple[List[Dependency], VirtualTest]:
    deps = []
    for name, vals in d['dependencies'].items():
        vals['versions'] = list(map(str_to_int_tuple, vals['versions']))
        vals['hints'] = list(map(str_to_rels, vals['hints']))
        deps.append(Dependency(name, **vals))

    true_when = []
    for test in d['tests']:
        for cond in test['true_when']:
            for key in cond:
                x, y = map(str_to_int_tuple, cond[key])
                cond[key] = VersionRange(x, y)

            true_when.append(cond)

    return deps, VirtualTest(true_when)

