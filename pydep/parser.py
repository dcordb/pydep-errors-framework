from typing import Tuple, List
from pydep.deps import Dependency
from pydep.tests import VirtualTest, ValidInterval
from pydep import rels

def str_to_tuple(s: str):
    return tuple(s.split('.'))

def str_to_rels(s: str):
    cls = rels.EQUIVS[s[:2]]
    return cls(str_to_tuple(s[2:]))

def parse_virtual_config(d: dict) -> Tuple[List[Dependency], VirtualTest]:
    deps = []
    for name, vals in d['dependencies'].items():
        vals['versions'] = list(map(str_to_tuple, vals['versions']))
        vals['hints'] = list(map(str_to_rels, vals['hints']))
        deps.append(Dependency(name, **vals))

    true_when = []
    for test in d['tests']:
        for cond in test['true_when']:
            x, y = map(str_to_tuple, cond)
            true_when.append(ValidInterval(x, y))

    return deps, VirtualTest(true_when)

