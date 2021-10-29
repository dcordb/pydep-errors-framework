import tomli
import typer
from typer import FileText
from pydep.parser import parse_virtual_config
from pydep.algorithms import Backtrack
from pydep.tests import LinearRunner
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


def entrypoint():
    app()
