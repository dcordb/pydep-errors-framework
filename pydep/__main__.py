from pathlib import Path
from typing import Optional

import tomli
import typer
from typer import FileText

from pydep import costs
from pydep import opts
from pydep.algorithms import AlgorithmsAvailable
import pydep.algorithms as algos
from pydep.depsmgr import Pip
from pydep.logs import stream_logger
from pydep.parser import parse_virtual_config
from pydep.tests import DockerPyRunner, LinearRunner, TestCmdsEnum
import pydep.tests as runners
from pydep.vercache import versions_cache

logger = stream_logger(__name__)
app = typer.Typer()


@app.command()
def virtual(
    testcase: FileText,
    algorithm: AlgorithmsAvailable = typer.Option(
        AlgorithmsAvailable.backtrack.value, help="Algorithm to use"
    ),
):
    d = tomli.loads(testcase.read())
    deps, tests = parse_virtual_config(d)

    algo = getattr(algos, algorithm)

    solver = algo(
        deps, LinearRunner(tests), costs.Sum(costs.version_to_float), opts.Max()
    )
    resp = solver.run()

    print(resp)


@app.command()
def dockerpy(
    path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Path to the project to run.",
    ),
    test_runner: TestCmdsEnum = typer.Option(
        TestCmdsEnum.pytest.value, help="Test runner to run tests inside docker images."
    ),
    pytag: str = typer.Option("3.9-slim", help="Tag to use for the python image."),
    extras: Optional[str] = typer.Option(None, help="Extras to install with pip."),
    img_basename: Optional[str] = typer.Option(
        None,
        help="Base name of the created image(s), the default is the last componenth of PATH parameter.",
    ),
    test_cmd: Optional[str] = typer.Option(
        None, help="Cmd to override the test runner."
    ),
    bypass_ivers: bool = typer.Option(
        False, help="Bypass the check with the initial installed versions"
    ),
    algorithm: AlgorithmsAvailable = typer.Option(
        AlgorithmsAvailable.backtrack.value, help="Algorithm to use"
    ),
    iterations: int = typer.Option(
        100, help="Iterations to run the selected algorithm (if applies)"
    ),
):
    cmd = getattr(runners, test_runner)(test_cmd)

    args = [] if not extras else extras.split(",")
    depsmgr = Pip(args)

    if img_basename is None:
        img_basename = path.stem

    runner = DockerPyRunner(path, depsmgr, [cmd], img_basename, pytag)
    mapping = runner.init_deps_mapping()

    logger.debug(mapping)

    if not bypass_ivers:
        result = runner.run_all(mapping)

        if all(result):
            typer.secho("All tests passed with initial versions", fg=typer.colors.GREEN)
            return

    algo = getattr(algos, algorithm)

    solver = algo(
        list(mapping),
        runner,
        costs.Sum(costs.version_to_float),
        opts.Max(),
        iterations=iterations,
    )

    resp = solver.run()
    typer.echo(resp)


@app.command()
def update_versions(
    pytag: str = typer.Option("3.9-slim", help="Tag to use for the python image.")
):
    img = f"python:{pytag}"
    deps = versions_cache.cached_deps()
    versions_cache.fetch_versions(deps, img, check_cache=False)


def entrypoint():
    app()
