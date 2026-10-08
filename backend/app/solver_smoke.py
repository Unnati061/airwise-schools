import json

from ortools.sat.python import cp_model


def run_smoke() -> dict:
    model = cp_model.CpModel()
    periods = [model.new_int_var(1, 3, f"activity_{i}") for i in range(3)]
    model.add_all_different(periods)
    model.minimize(sum(periods))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 42
    status = solver.solve(model)
    if status != cp_model.OPTIMAL:
        raise RuntimeError(f"Smoke model did not prove optimality: {solver.status_name(status)}")
    values = [solver.value(period) for period in periods]
    if sorted(values) != [1, 2, 3] or solver.objective_value != 6:
        raise RuntimeError("Smoke solution failed independent arithmetic checks")
    return {"status": solver.status_name(status), "periods": values, "objective": 6}


if __name__ == "__main__":
    print(json.dumps(run_smoke()))
