import json
import platform
from importlib.metadata import version

from .main import health
from .solver_smoke import run_smoke


def handler(event, context):
    result = {
        "health": health().model_dump(), "solver": run_smoke(),
        "python": platform.python_version(), "architecture": platform.machine(),
        "dependencies": {name: version(name) for name in
                         ("ortools", "numpy", "pandas", "protobuf", "fastapi", "pydantic", "mangum")},
    }
    print(json.dumps(result))
    return result
