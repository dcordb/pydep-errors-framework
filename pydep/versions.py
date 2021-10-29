from dataclasses import dataclass
from packaging.version import Version
from typing import Dict
from pydep.deps import Dependency

VersionMapping = Dict[Dependency, Version]


class VersionRangeException(Exception):
    pass


@dataclass
class VersionRange:
    min: Version
    max: Version

    def __post_init__(self):
        if self.min > self.max:
            raise VersionRangeException("Not a valid version range")
