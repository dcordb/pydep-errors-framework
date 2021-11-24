from pydep.tests import DockerPyRunner
from pydep.depsmgr import Pip
from typing import List
from pathlib import Path
from pylatex.labelref import Label
from pylatex.table import Table, Tabular
from pylatex import Command


def get_mapping(
    path: Path,
    extras: List[str],
    img_basename: str,
    top_level: bool = True,
    min_year: int = 2015,
):
    pytag = "3.9-slim"
    depsmgr = Pip(extras)

    runner = DockerPyRunner(path, depsmgr, [], img_basename, pytag)
    mapping = runner.init_deps_mapping(top_level=top_level, cache_min_year=min_year)

    return mapping


def make_table(caption: str, label: str):
    spec = "|l|c|"
    table = Table()
    center = Command("centering")

    tabular = Tabular(spec)
    table.append(center)
    table.append(tabular)
    table.add_caption(caption)
    table.append(Label(label))

    tabular.add_hline()
    tabular.add_row(["Dependencias", "Versiones"])

    return table


def gen_table_fastapi():
    path = Path("~/projects/fastapi").expanduser()
    extras = ["test", "doc", "dev", "all"]
    mapping = get_mapping(path, extras, "fastapi")

    caption = (
        "Número de versiones de cada una de las dependencias declaradas de fastapi."
    )
    label = "table:fastapi"
    table = make_table(caption, label)

    p = 1
    for dep in mapping:
        table[1].add_hline()
        versions = len(dep.spversions)
        table[1].add_row(dep.name, versions)

        p *= versions

    print(f"Product fastapi = {p}, number of versions = {len(mapping)}")

    table[1].add_hline()
    table.generate_tex("fastapi")


def gen_table_flit():
    path = Path("~/projects/flit").expanduser()
    extras = ["test"]
    mapping = get_mapping(path, extras, "flit")

    caption = "Número de versiones de cada una de las dependencias declaradas de flit."
    label = "table:flit"
    table = make_table(caption, label)

    p = 1
    for dep in mapping:
        table[1].add_hline()
        versions = len(dep.spversions)
        table[1].add_row(dep.name, versions)

        p *= versions

    print(f"Product flit = {p}, number of versions = {len(mapping)}")

    table[1].add_hline()
    table.generate_tex("flit")


if __name__ == "__main__":
    gen_table_fastapi()
    gen_table_flit()
