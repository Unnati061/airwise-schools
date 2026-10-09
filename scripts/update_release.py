"""One-shot wording/notice update using the verified existing resource updater."""
import argparse
import hashlib
import json
from zipfile import ZipFile, ZIP_DEFLATED

from . import update_features as deploy

ROOT = deploy.ROOT
BASE = "4c8a9eb26fb8409f1608b72096d39de1509c5db3d31fa0937469e1294cf1d2c1"
RECORD = ROOT / "work/release-deployment.json"


def preflight():
    import boto3
    record = json.loads(RECORD.read_text())
    assert record['status'] == 'STOPPED' and record['failure_step'] == 'authentication' and not record.get('object_key')
    stage = 'authentication'
    try:
        session = boto3.Session(profile_name='airwise', region_name=deploy.REGION)
        session.client('sts', config=deploy.CONFIG).get_caller_identity()
        stage = 'existing_resources'
        lam = session.client('lambda', config=deploy.CONFIG)
        current = lam.get_function_configuration(FunctionName=deploy.FUNCTION)
        import base64
        assert current['CodeSha256'] == base64.b64encode(bytes.fromhex(BASE)).decode()
        assert current['Runtime'] == 'python3.12' and current['Architectures'] == ['x86_64']
        assert current['MemorySize'] == 1024 and current['Timeout'] == 28
        assert lam.list_tags(Resource=current['FunctionArn'])['Tags']['Project'] == 'AirWiseSchools'
        app = session.client('amplify', config=deploy.CONFIG).get_app(appId=deploy.APP)['app']
        assert app['tags']['Project'] == 'AirWiseSchools' and app['name'] == 'airwise-schools-web-a1f7411817'
        record['prior_failure'] = {'step': record.pop('failure_step'), 'error_class': record.pop('error_class')}
        record['status'] = 'PREPARED'
        RECORD.write_text(json.dumps(record, indent=2))
        print('PASSED: bounded read-only authentication and exact existing-resource preflight; account redacted')
    except Exception as error:
        print(json.dumps(dict(status='STOPPED', stage=stage, error_class=type(error).__name__)))
        raise SystemExit(1) from None


def package():
    old = ROOT / "work/airwise-app-features.zip"
    new = ROOT / "work/airwise-app-release.zip"
    if new.exists() or RECORD.exists():
        raise RuntimeError("Release artifacts exist; inspect, never overwrite")
    assert hashlib.sha256(old.read_bytes()).hexdigest() == BASE
    changed = "backend/app/message_preview.py"
    with ZipFile(old) as source, ZipFile(new, "w", ZIP_DEFLATED) as result:
        for entry in source.infolist():
            if entry.filename == changed:
                result.writestr(entry, (ROOT / changed).read_bytes())
            else:
                content = source.read(entry)
                if entry.filename.startswith("backend/") and entry.filename.endswith((".py", ".json")):
                    assert content.replace(b"\r\n", b"\n") == (ROOT / entry.filename).read_bytes().replace(b"\r\n", b"\n")
                result.writestr(entry, content)
        for path in sorted((ROOT / "docs/third_party").rglob("*")):
            if path.is_file() and ("backend" in path.relative_to(ROOT / "docs/third_party").parts or path.name == "manifest.json"):
                result.write(path, "THIRD_PARTY_NOTICES/" + path.relative_to(ROOT / "docs/third_party").as_posix())
        result.write(ROOT / "LICENSE", "THIRD_PARTY_NOTICES/ORIGINAL_CODE_MIT_LICENSE")
    with ZipFile(new) as archive:
        size = sum(e.file_size for e in archive.infolist())
        assert archive.testzip() is None and size < 250 * 1024 * 1024
    record = dict(base_sha256=BASE, sha256=hashlib.sha256(new.read_bytes()).hexdigest(), archive=str(new),
                  compressed_bytes=new.stat().st_size, uncompressed_bytes=size, runtime="python3.12",
                  architecture="x86_64", status="PREPARED")
    RECORD.write_text(json.dumps(record, indent=2))
    print(json.dumps(record))


def resume_existing():
    import boto3
    deploy.BASE_SHA, deploy.RECORD = BASE, RECORD
    deploy.STATIC = ROOT / 'work/airwise-web-release.zip'
    record = json.loads(RECORD.read_text())
    expected_key = f"application/features/{record['sha256']}/airwise-app-features.zip"
    assert record['object_key'] == expected_key
    try:
        head = boto3.Session(profile_name='airwise', region_name=deploy.REGION).client(
            's3', config=deploy.CONFIG).head_object(
                Bucket=deploy.BUCKET, Key=expected_key, ChecksumMode='ENABLED')
        checksum = deploy.verify_existing_artifact(record, head)
        print(json.dumps({'existing_object_verified': checksum, 'bytes': head['ContentLength']}), flush=True)
    except Exception as error:
        print(json.dumps({'status': 'STOPPED', 'step': 'existing_object_verification',
                          'error_class': type(error).__name__, 'existence': 'UNKNOWN_OR_UNVERIFIED'}))
        raise SystemExit(1) from None
    deploy.update(existing_head=head)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=["package", "preflight", "update", "resume-existing"])
    args = parser.parse_args()
    if args.action == "package":
        package()
    elif args.action == "preflight":
        preflight()
    elif args.action == 'resume-existing':
        resume_existing()
    else:
        deploy.BASE_SHA, deploy.RECORD = BASE, RECORD
        deploy.STATIC = ROOT / "work/airwise-web-release.zip"
        deploy.update()
