from dataclasses import dataclass
import enum
import logging
from pathlib import Path
from typing import Optional
from typing import List, Mapping, Sequence

import docker
import docker.api.build
import docker.errors
from packaging.requirements import Requirement
from packaging.version import Version
from pep517 import meta

from pydep.deps import Dependency
from pydep.depsmgr import DepsManager
from pydep.vercache import VersionsCache
from pydep.versions import VersionMapping, VersionRange

# taken from here: https://github.com/docker/docker-py/issues/2105#issuecomment-613685891
docker.api.build.process_dockerfile = lambda dockerfile, _: ("Dockerfile", dockerfile)  # type: ignore
logger = logging.getLogger(__name__)


class Test:
    """Abstract base class for Tests"""

    def run(self, pinned_vers: VersionMapping) -> bool:
        raise NotImplementedError


@dataclass
class VirtualTest(Test):
    """
    A virtual test:
        `true_when` holds 'conditions' that tell whether to return True or False for
        this virtual test.
    """

    true_when: Sequence[Mapping[Dependency, VersionRange]]

    def run(self, pinned_vers: VersionMapping) -> bool:
        for conditions in self.true_when:
            for dep, range in conditions.items():
                cur_ver = pinned_vers[dep]

                if range.min > cur_ver or cur_ver > range.max:
                    break

            else:
                return True

        return False


@dataclass
class TestCmd(Test):
    cmd: str


@dataclass
class PytestCmd(TestCmd):
    cmd: Optional[str] = None

    def __post_init__(self):
        if self.cmd is None:
            self.cmd = "pytest"

    def run(self):
        return self.cmd


class TestCmdsEnum(str, enum.Enum):
    pytest = "PytestCmd"


class TestRunner:
    def __init__(self, tests: Sequence[Test]) -> None:
        self.tests = tests

    def run_all(self, pinned_vers: VersionMapping) -> List[bool]:
        raise NotImplementedError


class LinearRunner(TestRunner):
    def run_all(self, pinned_vers: VersionMapping) -> List[bool]:
        return [test.run(pinned_vers) for test in self.tests]


class ExternalRunner(TestRunner):
    def __init__(
        self, project: Path, depsmgr: DepsManager, tests: Sequence[Test]
    ) -> None:
        super().__init__(tests)
        self.project = project
        self.depsmgr = depsmgr

    def init_deps_mapping(self) -> VersionMapping:
        raise NotImplementedError


class DockerPyRunner(ExternalRunner):
    def __init__(
        self,
        project: Path,
        depsmgr: DepsManager,
        tests: Sequence[TestCmd],
        img_basename: str,
        pytag: str,
    ) -> None:
        super().__init__(project, depsmgr, tests)

        self.img = f"python:{pytag}"
        self.img_basename = img_basename
        self.workdir = "/home/pydep/app"

    def _base_dockerfile(self) -> List[str]:
        return [
            f"FROM {self.img}",
            "RUN groupadd pydep && useradd -mg pydep pydep",
            "USER pydep",
            "ENV VIRTUAL_ENV=/home/pydep/.venv",
            "RUN python -m venv $VIRTUAL_ENV",
            "ENV PATH=$VIRTUAL_ENV/bin:$PATH",
            "RUN pip config set global.disable-pip-version-check true",
            f"COPY --chown=pydep:pydep . {self.workdir}/",
            f"WORKDIR {self.workdir}",
            f"ENV PYTHONPATH={self.workdir}",
        ]

    def init_deps_mapping(
        self, top_level=True, cache_min_year: int = 2018
    ) -> VersionMapping:
        logger.info("Initializing base dockerfile")

        dockerfile = self._base_dockerfile()

        dockerfile.append("RUN " + self.depsmgr.cmd_init_pinned_deps())
        dockerfile.append("CMD pip freeze")
        dfstr = "\n".join(dockerfile)
        logger.debug(dfstr)

        dockerclient = docker.from_env()
        img, _ = dockerclient.images.build(
            path=str(self.project),
            dockerfile=dfstr,
            rm=True,
            tag=f"pydep/{self.img_basename}",
        )  # type: ignore

        output = dockerclient.containers.run(img.id, remove=True).decode()  # type: ignore

        deps = []
        vers = []
        for line in output.split("\n"):
            if "==" not in line:
                continue

            name, ver = line.split("==", maxsplit=1)
            deps.append(name)
            vers.append(ver)

        pyver = (
            dockerclient.containers.run(
                img.id, remove=True, command="/bin/sh -c 'echo $PYTHON_VERSION'"
            )
            .decode()
            .rstrip()
        )  # type: ignore

        logger.info(f"Container is running on Python {pyver}")

        versions_cache = VersionsCache(Version(pyver), loyear=cache_min_year)
        versions = versions_cache.fetch_versions(deps)
        mapping = {}

        dist = meta.load(self.project)

        reqs = {}
        for line in dist.requires or []:
            req = Requirement(line)
            req.name = req.name.lower().replace("-", "_")
            reqs[req.name] = req

        for name, ver in zip(deps, vers):
            dep = Dependency(name, versions[name], Requirement(f"{name}=={ver}"))

            if top_level:
                norm_name = name.lower().replace("-", "_")

                if norm_name in reqs:
                    dep = Dependency(name, versions[name], reqs[norm_name])

                else:
                    continue

            mapping[dep] = Version(ver)

        return mapping

    def run_all(self, pinned_vers: VersionMapping) -> List[bool]:
        logger.info("Running tests")

        dockerfile = self._base_dockerfile()
        dockerfile.append("RUN " + self.depsmgr.cmd_install_deps(pinned_vers))
        dfstr = "\n".join(dockerfile)
        logger.debug(dfstr)

        dockerclient = docker.from_env()

        try:
            img, _ = dockerclient.images.build(
                path=str(self.project),
                dockerfile=dfstr,
                rm=True,
                tag=f"pydep/{self.img_basename}-runner",
            )  # type: ignore
        except docker.errors.BuildError as err:
            for line in err.build_log:
                if "stream" in line:  # temporal maybe?
                    logger.error(line["stream"])

            return [False] * len(self.tests)

        res = []
        for test in self.tests:
            cmd = test.run()  # type: ignore
            logger.debug(f"Running {cmd}")
            success = True

            try:
                dockerclient.containers.run(img.id, remove=True, command=cmd)
            except Exception as err:
                logger.warning(err)
                success = False

            res.append(success)

        return res
