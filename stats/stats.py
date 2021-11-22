from pydep import algorithms
from pydep.parser import parse_virtual_config
from pydep import costs
from pydep import opts
from pydep.tests import LinearRunner
from faker import Faker
from packaging.version import Version
import random
import logging
from pylatex.labelref import Label
from pylatex.table import Tabular, Table
from pylatex import Command

Faker.seed(0)
random.seed(0)

logger = logging.getLogger(__name__)
handler = logging.FileHandler("stats.log", mode="w")
handler.setFormatter(
    logging.Formatter(fmt="{levelname} ({module}:{lineno}): {message}", style="{")
)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def gen_version() -> str:
    dots = random.randint(2, 7)

    ans = str(random.randint(0, 100))
    for _ in range(dots - 1):
        ans += f".{random.randint(0, 100)}"

    return ans


def generate(deps: int, t: int) -> dict:
    f = Faker()

    dp = {}
    for _ in range(deps):
        name = f.unique.word()
        v = random.randint(4, 20)
        vers = [gen_version() for _ in range(v)]

        dp[name] = {"versions": vers, "specifier": "", "iniver": random.choice(vers)}

    dt = {"true_when": []}
    for _ in range(t):
        tmp = {}
        for dep, val in dp.items():
            x = random.choice(val["versions"])
            y = random.choice(val["versions"])

            if Version(x) > Version(y):
                x, y = y, x

            tmp[dep] = [x, y]

        dt["true_when"].append(tmp)

    ans = {"dependencies": dp, "tests": [dt]}
    return ans


ITS = [15, 40, 80, 150, 500, 700, 1000, 3000, 5000]


def run(total: int, deps: int, t: int):
    tsets = [generate(random.randint(2, deps), t) for _ in range(total)]

    import json

    for te in tsets:
        logger.debug(json.dumps(te, indent=4))

    res = {}

    for name in algorithms.AlgorithmsAvailable:
        algo = getattr(algorithms, name.value)
        res[algo.desc_name] = {}

        for it in ITS:
            successes = 0
            ssum = 0

            for tset in tsets:
                ldeps, tests, inivers = parse_virtual_config(tset)

                mapping = {}
                for dep, ver in zip(ldeps, inivers):
                    mapping[dep] = ver

                solver = algo(
                    ldeps,
                    LinearRunner(tests),
                    costs.Sum(costs.version_to_float),
                    opts.Max(),
                    inimapping=mapping,
                    iterations=it,
                )

                try:
                    resp = solver.run()
                    ssum += resp[0]
                except opts.NotSolutionException:
                    continue

                successes += 1

            res[algo.desc_name][it] = {
                "succ_sum": ssum,
                "successes": successes,
                "total": len(tsets),
            }

            if not successes:
                continue

            avg = ssum / successes

            logger.debug(
                f"algo = {name.value}, it = {it}, avg_succ = {avg:.3e}, successes = {successes}, total = {len(tsets)}"
            )

    return res


def it_vs_algos_table(caption: str, label: str):
    spec = "|l" + "|c" * len(data) + "|"
    label = Label(label)
    table = Table()
    center = Command('centering')

    tabular = Tabular(spec)

    table.append(center)
    table.append(tabular)
    table.add_caption(caption)
    table.append(label)

    dbox = Command("diagbox", arguments=["Iters.", "Algos."])

    tabular.add_hline()
    tabular.add_row([dbox] + list(data))

    return table


def gen_table_percent(data: dict):
    tpercent = it_vs_algos_table(
        "Porciento de proyectos con solución encontrada.", "table:percent"
    )
    tavg = it_vs_algos_table(
        "Promedio de la puntuación obtenida de todos los proyectos.", "table:avg"
    )

    for it in ITS:
        rowpp = []
        rowavg = []
        for itersd in data.values():
            d = itersd[it]
            successes, total = d["successes"], d["total"]
            rowpp.append("{:.2f}".format(100.0 * successes / total))

            ssum = d["succ_sum"]

            if successes:
                rowavg.append("{:.4e}".format(ssum / successes))

            else:
                rowavg.append("0")

        tpercent[1].add_hline()
        tpercent[1].add_row([it] + rowpp, strict=True)

        tavg[1].add_hline()
        tavg[1].add_row([it] + rowavg, strict=True)

    tpercent[1].add_hline()
    tavg[1].add_hline()

    tpercent.generate_tex("percent")
    tavg.generate_tex("avg")


if __name__ == "__main__":
    data = run(15, 20, 10)
    gen_table_percent(data)
