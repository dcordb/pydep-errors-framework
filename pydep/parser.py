from typing import Tuple, List
from packaging.version import Version
from packaging.specifiers import SpecifierSet
from pydep.deps import Dependency
from pydep.tests import VirtualTest
from pydep.versions import VersionRange


def parse_virtual_config(d: dict) -> Tuple[List[Dependency], List[VirtualTest]]:
    deps = []
    who = {}
    for name, vals in d["dependencies"].items():
        vals["versions"] = list(map(Version, vals["versions"]))
        vals["specifier"] = SpecifierSet(vals["specifier"])
        dep = Dependency(name, **vals)
        who[dep.name] = dep
        deps.append(dep)

    tests = []
    for test in d["tests"]:
        true_when = []
        for cond in test["true_when"]:
            dep_cond = {}
            for key in cond:
                x, y = map(Version, cond[key])
                dep_cond[who[key]] = VersionRange(x, y)

            true_when.append(dep_cond)

        tests.append(VirtualTest(true_when))

    return deps, tests
