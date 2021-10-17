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

class VersionRangeException(Exception): pass

@dataclass
class VersionRange:
    min: Version
    max: Version

    def __post_init__(self):
        if self.min > self.max:
            raise VersionRangeException('Not a valid version range')

