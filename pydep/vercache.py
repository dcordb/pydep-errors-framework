import asyncio
import concurrent.futures
import json
from pathlib import Path
import tempfile
from typing import Dict, List, Sequence

from appdirs import user_cache_dir
import docker
import docker.api.build
import docker.errors
import httpx
from packaging.version import Version

from pydep.logs import stream_logger

docker.api.build.process_dockerfile = lambda dockerfile, _: ("Dockerfile", dockerfile)  # type: ignore
logger = stream_logger(__name__)


class VersionsCache:
    def __init__(self) -> None:
        self.dir = Path(user_cache_dir(appname="pydep"))

        if not self.dir.exists():
            self.dir.mkdir(parents=True)

    def cached_deps(self) -> List[str]:
        return [d.stem for d in self.dir.iterdir()]

    def has(self, dep: str) -> bool:
        return (self.dir / dep).exists()

    def dumps(self, dep: str, versions: Sequence[str]) -> None:
        depdir = self.dir / dep

        with depdir.open("w") as fd:
            fd.write(json.dumps(versions))

    def loads(self, dep: str) -> List[str]:
        depdir = self.dir / dep

        with depdir.open() as fd:
            content = fd.read()

        return json.loads(content)

    async def __make_versions_request(
        self, dep: str, img: str, check_cache: bool, semaphore: asyncio.Semaphore
    ) -> List[str]:
        if check_cache and self.has(dep):
            return self.loads(dep)

        async with httpx.AsyncClient(
            base_url="https://pypi.org", follow_redirects=True
        ) as client:
            r = await client.get(f"/pypi/{dep}/json")

        ans = [version for version in r.json()["releases"]]

        async with semaphore:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                ans = await loop.run_in_executor(
                    pool, self._prune_bad_versions, dep, ans, img
                )

        self.dumps(dep, ans)
        return ans

    def fetch_versions(
        self, deps: Sequence[str], img: str, check_cache: bool = True, workers: int = 2
    ) -> Dict[str, List[Version]]:
        logger.info("Fetching versions of installed dependencies...")

        semaphore = asyncio.Semaphore(workers)

        tasks = [
            asyncio.ensure_future(
                self.__make_versions_request(dep, img, check_cache, semaphore)
            )
            for dep in deps
        ]

        loop = asyncio.get_event_loop()
        resp = loop.run_until_complete(asyncio.gather(*tasks))

        versions = {}
        for dep, res in zip(deps, resp):
            versions[dep] = list(map(Version, res))

        return versions

    def _prune_bad_versions(self, dep: str, versions: List[str], img: str) -> List[str]:
        logger.debug(f"Prunning bad versions of {dep}...")

        dockerfile = (
            f"FROM {img}",
            "RUN groupadd pydep && useradd -mg pydep pydep",
            "USER pydep",
            "ENV VIRTUAL_ENV=/home/pydep/.venv",
            "RUN python -m venv $VIRTUAL_ENV",
            "ENV PATH=$VIRTUAL_ENV/bin:$PATH",
            "RUN pip config set global.disable-pip-version-check true",
        )

        dfstr = "\n".join(dockerfile)
        dockerclient = docker.from_env()

        with tempfile.TemporaryDirectory() as tmpdir:
            img, _ = dockerclient.images.build(
                path=tmpdir,
                dockerfile=dfstr,
                rm=True,
                tag=f"pydep/singledep",
            )  # type: ignore

        vers = list(map(Version, versions))
        vers.sort()

        def good(p: int) -> bool:
            ver = vers[p]

            logger.debug(f"Installing {dep}=={ver}")
            cmd = f"pip install {dep}=={ver}"

            try:
                dockerclient.containers.run(img.id, remove=True, command=cmd)  # type: ignore
            except docker.errors.ContainerError as err:
                logger.warning(err)
                return False

            return True

        st, nd = 0, len(vers) - 1
        p = len(vers)

        while st <= nd:
            mid = (st + nd) // 2

            if good(mid):
                p = mid
                nd = mid - 1

            else:
                st = mid + 1

        return list(map(str, vers[p:]))


versions_cache = VersionsCache()

if __name__ == "__main__":
    vers = versions_cache.fetch_versions(
        ["websockets", "packaging", "six", "toml"], "python:3.9-slim", check_cache=False
    )
