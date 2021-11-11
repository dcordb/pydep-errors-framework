import asyncio
from datetime import datetime
import json
from pathlib import Path
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
    def __init__(self, pyver: Version, loyear: int = 2018) -> None:
        self.pyver = pyver
        self.dir = Path(user_cache_dir(appname="pydep")) / str(self.pyver)
        self.loyear = loyear

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

    async def __make_versions_request(self, dep: str, check_cache: bool) -> List[str]:
        if check_cache and self.has(dep):
            return self.loads(dep)

        async with httpx.AsyncClient(
            base_url="https://pypi.org", follow_redirects=True
        ) as client:
            r = await client.get(f"/pypi/{dep}/json")

        releases = r.json()["releases"]

        ans = []
        for ver, data in releases.items():
            mxyear = 0
            for dict in data:
                upload_time = datetime.fromisoformat(dict["upload_time"])
                mxyear = max(mxyear, upload_time.year)

            if mxyear >= self.loyear:
                ans.append(ver)

        self.dumps(dep, ans)
        return ans

    def fetch_versions(
        self, deps: Sequence[str], check_cache: bool = True
    ) -> Dict[str, List[Version]]:
        logger.info("Fetching versions of installed dependencies...")

        tasks = [
            asyncio.ensure_future(self.__make_versions_request(dep, check_cache))
            for dep in deps
        ]

        loop = asyncio.get_event_loop()
        resp = loop.run_until_complete(asyncio.gather(*tasks))

        versions = {}
        for dep, res in zip(deps, resp):
            versions[dep] = list(map(Version, res))

        return versions


if __name__ == "__main__":
    versions_cache = VersionsCache(Version("3.9.7"))

    vers = versions_cache.fetch_versions(
        ["websockets", "packaging", "six", "toml"], check_cache=False
    )
