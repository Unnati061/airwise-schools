from .main import health
from .solver_smoke import run_smoke


def handler(event, context):
    return {"health": health().model_dump(), "solver": run_smoke()}
