import asyncio
import json
from pathlib import Path
from typing import Dict, List, Sequence

from appdirs import user_cache_dir
import httpx
from packaging.version import Version

from pydep.logs import stream_logger

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

    async def __make_versions_request(self, dep: str, check_cache: bool) -> List[str]:
        logger.debug(f"fetching {dep}")

        if check_cache and self.has(dep):
            logger.debug(f"{dep} is on cache, returning...")
            return self.loads(dep)

        async with httpx.AsyncClient(
            base_url="https://pypi.org", follow_redirects=True
        ) as client:
            r = await client.get(f"/pypi/{dep}/json")

        ans = [version for version in r.json()["releases"]]
        self.dumps(dep, ans)

        logger.debug(f"done {dep}")
        return ans

    async def fetch_versions(
        self, deps: Sequence[str], check_cache: bool = True
    ) -> Dict[str, List[Version]]:
        tasks = [
            asyncio.ensure_future(self.__make_versions_request(dep, check_cache))
            for dep in deps
        ]

        resp = await asyncio.gather(*tasks)

        versions = {}
        for dep, res in zip(deps, resp):
            versions[dep] = list(map(Version, res))

        return versions


versions_cache = VersionsCache()


if __name__ == "__main__":
    vers = asyncio.run(
        versions_cache.fetch_versions(["httpx", "fastapi", "websockets"])
    )
    print(vers.keys())
