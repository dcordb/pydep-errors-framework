import tomli
import typer
from typing import Optional
from typer import FileText
from pathlib import Path
from pydep.parser import parse_virtual_config
from pydep.algorithms import Backtrack
from pydep.tests import LinearRunner, DockerPyRunner, TestCmdsEnum
import pydep.tests as runners
from pydep.depsmgr import Pip
from pydep import costs
from pydep import opts

app = typer.Typer()


@app.command()
def virtual(testcase: FileText):
    d = tomli.loads(testcase.read())
    deps, tests = parse_virtual_config(d)

    solver = Backtrack(
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
    test_runner: TestCmdsEnum = typer.Argument(
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
):
    cmd = getattr(runners, test_runner)(test_cmd)

    args = [] if not extras else extras.split(",")
    depsmgr = Pip(args)

    if img_basename is None:
        img_basename = path.stem

    runner = DockerPyRunner(path, depsmgr, [cmd], img_basename, pytag)
    mapping = runner.init_deps_mapping()

    print(mapping)

    res = runner.run_all(mapping)
    print(res)


def entrypoint():
    app()
