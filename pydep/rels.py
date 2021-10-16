from dataclasses import dataclass
from typing import Tuple

Version = Tuple[int, ...]

@dataclass
class VersionRel:
    version: Version

class Eq(VersionRel):
    pass

class NotEq(VersionRel):
    pass

class LessThan(VersionRel):
    pass

class GreaterThan(VersionRel):
    pass

EQUIVS = {
    '==': Eq,
    '>=': GreaterThan,
    '<=': LessThan,
    '!=': NotEq
}

