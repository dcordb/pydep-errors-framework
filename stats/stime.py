import logging
from multiprocessing import Event, Process, Value
import random
import sys
from collections import namedtuple

from pydep import algorithms
from pydep import opts
from stats import generate, prepare_algo, make_table

random.seed(0)

logger = logging.getLogger(__name__)
handler = logging.FileHandler("stime.log", mode="w")
handler.setFormatter(
    logging.Formatter(fmt="{levelname} ({module}:{lineno}): {message}", style="{")
)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

TESTS = 500
EPS = 1e-3
TIME_LIMIT = 5 * 60  # 5 mins
# deps = [ 5, 10, 15, 20, 25, 30, 40, 50, 80, 100 ]
# its = [100, 500, 1000, 1500, 3000, 5000]
deps = [10]
its = [5000]
Result = namedtuple("Result", ["found_sol", "time", "terminated"])


def run_algo(solver, found_sol):
    try:
        solver.run()
    except opts.NotSolutionException:
        return

    found_sol.value = 1


def run_stats():
    result = {}

    for num_deps in deps:
        case = generate(num_deps, TESTS)

        for it in its:
            for name in algorithms.AlgorithmsAvailable:
                algo = getattr(algorithms, name.value)
                solver = prepare_algo(algo, case, it)

                logger.info(
                    f"Running {algo.desc_name} with {num_deps} deps and {it} iterations"
                )

                found_sol = Value("i", 0)

                p = Process(target=run_algo, args=(solver, found_sol))
                p.start()

                tot_time = 0
                event = Event()
                term = False

                while p.is_alive() and tot_time + EPS < TIME_LIMIT:
                    event.wait(timeout=0.1)
                    tot_time += 0.1

                if p.is_alive():
                    logger.warning(f"Terminating {algo.desc_name}")
                    term = True
                    p.terminate()

                if found_sol.value:
                    logger.info("Found at least one solution")

                else:
                    logger.warning(
                        f"{algo.desc_name} terminated without finding a solution"
                    )

                mins, secs = int(tot_time // 60), round(tot_time % 60)
                mins = str(mins)
                secs = str(secs)

                if len(mins) < 2:
                    mins = "0" + mins

                if len(secs) < 2:
                    secs = "0" + secs

                fmt_time = f"{mins}:{secs}"

                logger.info(f"Executed {algo.desc_name}, took {fmt_time} units of time")
                logger.debug("-" * 100)

                if it not in result:
                    result[it] = {}

                if num_deps not in result[it]:
                    result[it][num_deps] = {}

                result[it][num_deps][algo.desc_name] = Result(
                    bool(found_sol.value), fmt_time, term
                )

    return result


def gen_tables():
    data = run_stats()
    algs = [key.value for key in algorithms.AlgorithmsAvailable]
    diagbox = ["Deps.", "Algos."]

    tables = []

    for it in its:
        caption = f"Tiempo de ejecución en a lo más {it} iteraciones."
        label = f"table:it_{it}"
        t = make_table(algs, diagbox, caption, label)
        tables.append(t)

    for it, table in zip(data, tables):
        for num_deps, value in data[it].items():
            row = []
            for _, result in value.items():
                if not result.found_sol:
                    row.append("NS")

                else:
                    row.append(result.time)

            table[1].add_hline()
            table[1].add_row([num_deps] + row)

        table[1].add_hline()

    for it, table in zip(its, tables):
        table.generate_tex(f"it_{it}")


if __name__ == "__main__":
    gen_tables()
