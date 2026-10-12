"""Run inside the built image as its normal non-root user, on each architecture."""

import pulp

from optimizer.app import app
from optimizer.settings import OptimizerSettings


assert OptimizerSettings().solver == "highs"
assert app.test_client().get("/optimize/health").status_code == 200

for solver in (pulp.HiGHS(msg=False), pulp.COIN_CMD(msg=False)):
    assert solver.available(), f"{solver.name} is unavailable"
    problem = pulp.LpProblem("smoke", pulp.LpMinimize)
    value = problem.add_variable("value", lowBound=1, cat=pulp.LpInteger)
    problem += value
    result = problem.solve(solver)
    assert result.has_solution, f"{solver.name} did not find a solution"
    assert abs(value.varValue - 1) < 1e-6, f"{solver.name} returned {value.varValue}"
    print(f"{solver.name}: solved successfully")

print("API health and HiGHS default: OK")
