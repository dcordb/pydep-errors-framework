import copy
from typing import List

from packaging.specifiers import SpecifierSet

from pydep.versions import VersionMapping


class DepsManager:
    def cmd_init_pinned_deps(self) -> str:
        raise NotImplementedError

    def cmd_install_deps(self, mapping: VersionMapping) -> str:
        raise NotImplementedError


class Pip(DepsManager):
    def __init__(self, extras: List[str] = []) -> None:
        self.extras = extras

    def cmd_init_pinned_deps(self) -> str:
        what = ""

        if self.extras:
            what = f"[{','.join(self.extras)}]"

        return f"pip install .{what}"

    def cmd_install_deps(self, mapping: VersionMapping) -> str:
        deps = []

        for dep, ver in mapping.items():
            req = copy.copy(dep.org_req)
            req.specifier = SpecifierSet(f"=={ver}")
            req.marker = None
            deps.append(str(req))

        return f"pip install {' '.join(deps)}"
