"""Guarded product update: proven Linux dependencies, existing resources only."""
import argparse
import base64
import hashlib
import json
import time
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile

import boto3

from . import update_features as deploy

ROOT = deploy.ROOT
BASE = "10d1de90053d6ac22e4b0c8ec90033cb2fe43e5d36b625455eb8a39b6c9363f9"
RECORD = ROOT / "work/product-deployment.json"
STATIC = ROOT / "work/airwise-web-product.zip"
SOURCE = ROOT / "work/airwise-app-release.zip"
TARGET = ROOT / "work/airwise-app-product.zip"


def preflight():
    stage = "authentication"
    try:
        session = boto3.Session(profile_name="airwise", region_name=deploy.REGION)
        session.client("sts", config=deploy.CONFIG).get_caller_identity()
        stage = "existing_resources"
        lam = session.client("lambda", config=deploy.CONFIG)
        current = lam.get_function_configuration(FunctionName=deploy.FUNCTION)
        assert current["CodeSha256"] == base64.b64encode(bytes.fromhex(BASE)).decode()
        assert current["Runtime"] == "python3.12" and current["Architectures"] == ["x86_64"]
        assert current["MemorySize"] == 1024 and current["Timeout"] == 28
        assert lam.list_tags(Resource=current["FunctionArn"])["Tags"]["Project"] == "AirWiseSchools"
        app = session.client("amplify", config=deploy.CONFIG).get_app(appId=deploy.APP)["app"]
        assert app["tags"]["Project"] == "AirWiseSchools"
        print("PASSED: authentication and owned existing Lambda/Amplify configuration; account redacted")
    except Exception as error:
        print(json.dumps({"status": "STOPPED", "step": stage, "error_class": type(error).__name__}))
        raise SystemExit(1) from None


def package():
    old, new = SOURCE, TARGET
    if new.exists() or RECORD.exists():
        raise RuntimeError("Product artifacts already exist; inspect, never overwrite")
    assert hashlib.sha256(old.read_bytes()).hexdigest() == BASE
    with ZipFile(old) as source, ZipFile(new, "w", ZIP_DEFLATED) as result:
        for entry in source.infolist():
            if not entry.filename.startswith("backend/"):
                result.writestr(entry, source.read(entry))
        for file in sorted((ROOT / "backend").rglob("*")):
            if file.is_file() and "tests" not in file.parts and "__pycache__" not in file.parts and file.suffix in (".py", ".json"):
                result.write(file, file.relative_to(ROOT).as_posix())
    with ZipFile(old) as source, ZipFile(new) as archive:
        size = sum(e.file_size for e in archive.infolist())
        assert archive.testzip() is None and size < 250 * 1024 * 1024
        native = 0
        for entry in source.infolist():
            if not entry.filename.startswith("backend/"):
                content = source.read(entry)
                assert archive.read(entry.filename) == content
                native += content.startswith(b"\x7fELF")
        assert native == 198
        assert any(n.startswith("THIRD_PARTY_NOTICES/") for n in archive.namelist())
        assert not any(n.endswith((".pyd", ".dll")) for n in archive.namelist())
    record = dict(base_sha256=BASE, sha256=hashlib.sha256(new.read_bytes()).hexdigest(), archive=str(new),
                  compressed_bytes=new.stat().st_size, uncompressed_bytes=size, elf_entries=native,
                  runtime="python3.12", architecture="x86_64", status="PREPARED")
    RECORD.write_text(json.dumps(record, indent=2))
    print(json.dumps(record))


def update(resume=False):
    deploy.BASE_SHA, deploy.RECORD, deploy.STATIC = BASE, RECORD, STATIC
    if not resume:
        deploy.update()
        return
    record = json.loads(RECORD.read_text())
    expected_key = f"application/features/{record['sha256']}/airwise-app-features.zip"
    assert record["status"] == "STOPPED" and record["failure_step"] == "artifact_upload_once"
    assert record["object_key"] == expected_key
    try:
        head = boto3.Session(profile_name="airwise", region_name=deploy.REGION).client(
            "s3", config=deploy.CONFIG).head_object(Bucket=deploy.BUCKET, Key=expected_key, ChecksumMode="ENABLED")
        verified = deploy.verify_existing_artifact(record, head)
        print(json.dumps({"existing_object_verified": verified, "bytes": head["ContentLength"]}), flush=True)
    except Exception as error:
        print(json.dumps({"status": "STOPPED", "step": "existing_object_verification",
                          "error_class": type(error).__name__, "existence": "UNKNOWN_OR_UNVERIFIED"}))
        raise SystemExit(1) from None
    deploy.update(existing_head=head)


def host_frontend():
    """A static-only correction; never upload/redeploy the application ZIP."""
    record = json.loads(RECORD.read_text())
    assert record["status"] == "DEPLOYED_NOT_BROWSER_VERIFIED"
    target = STATIC.with_stem(STATIC.stem + '-mobile')
    assert not target.exists()
    stage = "static_preflight"
    try:
        session = boto3.Session(profile_name="airwise", region_name=deploy.REGION)
        current = session.client("lambda", config=deploy.CONFIG).get_function_configuration(FunctionName=deploy.FUNCTION)
        assert current["CodeSha256"] == base64.b64encode(bytes.fromhex(record["sha256"])).decode()
        amp = session.client("amplify", config=deploy.CONFIG)
        app = amp.get_app(appId=deploy.APP)["app"]
        assert app["tags"]["Project"] == "AirWiseSchools" and app["name"] == "airwise-schools-web-a1f7411817"
        assets = ROOT / "frontend/dist"
        assert "https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com" in "".join(p.read_text() for p in (assets / "assets").glob("*.js"))
        with ZipFile(target, "w", ZIP_DEFLATED) as archive:
            for file in sorted(assets.rglob("*")):
                if file.is_file():
                    assert file.suffix != ".map"
                    archive.write(file, file.relative_to(assets).as_posix())
        stage = "static_upload_once"
        job = amp.create_deployment(appId=deploy.APP, branchName="main")
        record["previous_job_id"], record["job_id"] = record["job_id"], job["jobId"]
        RECORD.write_text(json.dumps(record, indent=2))
        with urlopen(Request(job["zipUploadUrl"], data=target.read_bytes(), method="PUT",
                             headers={"Content-Type": "application/zip"}), timeout=30) as response:
            assert response.status in (200, 201)
        stage = "static_deployment"
        amp.start_deployment(appId=deploy.APP, branchName="main", jobId=job["jobId"])
        for _ in range(40):
            status = amp.get_job(appId=deploy.APP, branchName="main", jobId=job["jobId"])["job"]["summary"]["status"]
            if status == "SUCCEED":
                break
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError("Hosting job failed")
            time.sleep(3)
        else:
            raise RuntimeError("Hosting observation timed out")
        record.update(status="DEPLOYED_NOT_BROWSER_VERIFIED", static_bytes=target.stat().st_size)
        RECORD.write_text(json.dumps(record, indent=2))
        print(json.dumps({"status": record["status"], "job_id": record["job_id"], "static_bytes": record["static_bytes"]}))
    except Exception as error:
        record.update(status="STOPPED", failure_step=stage, error_class=type(error).__name__)
        RECORD.write_text(json.dumps(record, indent=2))
        print(json.dumps({"status": "STOPPED", "step": stage, "error_class": type(error).__name__}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["package", "preflight", "update", "resume-existing", "host-frontend"])
    parser.add_argument("--release", choices=["product", "room"], default="product")
    args = parser.parse_args()
    action = args.action
    if args.release == "room":
        BASE = "d76e76084641e125d3b5cce57735078695a5299ed56cee05ca0e1d808521240e"
        RECORD = ROOT / "work/room-deployment.json"
        STATIC = ROOT / "work/airwise-web-room.zip"
        SOURCE = ROOT / "work/airwise-app-product.zip"
        TARGET = ROOT / "work/airwise-app-room.zip"
    if action == "package":
        package()
    elif action == "preflight":
        preflight()
    elif action == "host-frontend":
        host_frontend()
    else:
        update(resume=action == "resume-existing")
