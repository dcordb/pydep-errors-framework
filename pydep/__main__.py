import tomli
import typer
from typer import FileText
from pathlib import Path
from pydep.parser import parse_virtual_config
from pydep.algorithms import Backtrack
from pydep.tests import PytestCmd, LinearRunner, DockerPyRunner
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
        help="Path to the project to run",
    ),
    extras: str = typer.Option("", help="Extras to install with pip"),
):
    cmd = PytestCmd("python -m pytest")

    args = [] if not extras else extras.split(",")
    depsmgr = Pip(args)

    runner = DockerPyRunner(path, depsmgr, [cmd], "3.9-slim")
    mapping = runner.init_deps_mapping()

    print(mapping)

    res = runner.run_all(mapping)
    print(res)


def entrypoint():
    app()
