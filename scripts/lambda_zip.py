"""Docker-free Linux ZIP packaging and explicit existing-function deployment."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def package() -> Path:
    staging = ROOT / "work" / "lambda-package"
    if staging.exists():
        raise RuntimeError("Staging already exists; use a fresh checkout or review it before removal")
    staging.mkdir(parents=True)
    subprocess.run([
        sys.executable, "-m", "pip", "install", "--platform", "manylinux2014_x86_64",
        "--platform", "manylinux_2_28_x86_64", "--implementation", "cp",
        "--python-version", "3.12", "--only-binary=:all:", "--no-compile",
        "--target", str(staging), "-r", str(ROOT / "backend" / "requirements.txt"),
    ], check=True)
    shutil.copytree(ROOT / "backend", staging / "backend",
                    ignore=shutil.ignore_patterns("__pycache__", "tests", "*.txt"))
    archive = ROOT / "work" / "airwise-lambda.zip"
    size = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for path in sorted(staging.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                size += path.stat().st_size
                info = zipfile.ZipInfo(path.relative_to(staging).as_posix())
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                output.writestr(info, path.read_bytes())
    print(json.dumps({"zip": str(archive), "compressed_bytes": archive.stat().st_size,
                      "uncompressed_bytes": size, "native_runtime_tested": False}))
    if size > 250 * 1024 * 1024:
        raise RuntimeError("Package exceeds Lambda's 250 MiB extracted ZIP limit")
    return archive


def deploy(archive: Path) -> None:
    import boto3
    from botocore.config import Config

    config = Config(connect_timeout=5, read_timeout=15, retries={"max_attempts": 0})
    session = boto3.Session(region_name="us-east-1")
    if session.get_credentials() is None:
        raise RuntimeError("AWS credentials unavailable; no upload or runtime invocation performed")
    session.client("sts", config=config).get_caller_identity()
    target = os.environ.get("AIRWISE_LAMBDA_FUNCTION")
    if not target:
        raise RuntimeError("AIRWISE_LAMBDA_FUNCTION must name an existing dedicated smoke function")
    client = session.client("lambda", config=config)
    current = client.get_function_configuration(FunctionName=target)
    if current["Runtime"] != "python3.12" or current.get("Architectures") != ["x86_64"]:
        raise RuntimeError("Target must be Python 3.12 x86_64")
    if current["Handler"] != "backend.app.lambda_smoke.handler":
        raise RuntimeError("Target must use backend.app.lambda_smoke.handler")
    if archive.stat().st_size > 50 * 1024 * 1024:
        raise RuntimeError("ZIP exceeds direct upload limit; S3 deployment deferred")
    client.update_function_code(FunctionName=target, ZipFile=archive.read_bytes())
    client.get_waiter("function_updated_v2").wait(FunctionName=target)
    response = client.invoke(FunctionName=target, Payload=b"{}")
    payload = json.loads(response["Payload"].read())
    if response.get("FunctionError") or payload.get("solver", {}).get("status") != "OPTIMAL":
        raise RuntimeError(f"Lambda native smoke failed: {payload}")
    print(json.dumps({"aws_smoke": "passed", "result": payload}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--existing-zip", type=Path)
    args = parser.parse_args()
    os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
    try:
        result = args.existing_zip.resolve() if args.existing_zip else package()
        if not result.is_file():
            raise RuntimeError("ZIP archive does not exist")
        if args.deploy:
            deploy(result)
    except Exception as error:
        print(f"ZIP attempt blocked: {error}", file=sys.stderr)
        sys.exit(1)
