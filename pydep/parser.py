from copy import deepcopy
from typing import Tuple, List
from packaging.version import Version
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from pydep.deps import Dependency
from pydep.tests import VirtualTest
from pydep.versions import VersionRange


def parse_virtual_config(
    d: dict,
) -> Tuple[List[Dependency], List[VirtualTest], List[Version]]:
    d = deepcopy(d)

    deps = []
    who = {}
    inivers = []
    for name, vals in d["dependencies"].items():
        vals["versions"] = list(map(Version, vals["versions"]))
        vals["specifier"] = SpecifierSet(vals["specifier"])
        vals["org_req"] = Requirement(f"{name}{vals['specifier']}")
        vals.pop("specifier")

        iniver = vals.pop("iniver")
        inivers.append(Version(iniver))
        assert inivers[-1] in vals["versions"]

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

    return deps, tests, inivers
