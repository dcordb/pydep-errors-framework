import tomli
import typer
from typer import FileText
from pydep.parser import parse_virtual_config

app = typer.Typer()


@app.command()
def virtual(testcase: FileText):
    d = tomli.loads(testcase.read())
    deps, test = parse_virtual_config(d)


def entrypoint():
    app()
