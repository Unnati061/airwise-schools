"""Bounded updates of existing owned application resources, never create-only helpers."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
import zipfile

import boto3
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[1]
REGION = 'ap-southeast-2'
FUNCTION = 'airwise-app-api-a1f7411817'
BUCKET = 'airwise-smoke-artifacts-a1f7411817'
APP = 'd29v8cmldu93l3'
BASE_SHA = '43f0c6d1bcfaa051db9f8f45f0502202faeec9f4d4ab95d1941bf3e60e435469'
CONFIG = Config(connect_timeout=4, read_timeout=15, retries={'total_max_attempts': 1})
RECORD = ROOT / 'work/features-deployment.json'


def package():
    old = ROOT / 'work/airwise-app-d2.zip'
    target = ROOT / 'work/airwise-app-features.zip'
    if target.exists():
        raise RuntimeError('Feature archive already exists; inspect before replacing')
    if hashlib.sha256(old.read_bytes()).hexdigest() != BASE_SHA:
        raise RuntimeError('Base Linux ZIP does not match proven artifact')
    with zipfile.ZipFile(old) as source, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as result:
        for entry in source.infolist():
            if not entry.filename.startswith('backend/'):
                result.writestr(entry, source.read(entry))
        for file in sorted((ROOT / 'backend').rglob('*')):
            if file.is_file() and 'tests' not in file.parts and '__pycache__' not in file.parts and file.suffix in ('.py', '.json'):
                result.write(file, file.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        extracted = sum(e.file_size for e in archive.infolist())
        if archive.testzip() or extracted > 250 * 1024 * 1024:
            raise RuntimeError('Corrupt/oversized archive')
    record = {'base_sha256': BASE_SHA, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
              'archive': str(target), 'compressed_bytes': target.stat().st_size, 'uncompressed_bytes': extracted,
              'runtime': 'python3.12', 'architecture': 'x86_64', 'status': 'PREPARED'}
    RECORD.write_text(json.dumps(record, indent=2))
    print(json.dumps(record))


def update():
    record = json.loads(RECORD.read_text())
    if record['status'] != 'PREPARED':
        raise RuntimeError('Partial update exists; inspect rather than repeat upload/deploy')
    def save(**values):
        record.update(values); RECORD.write_text(json.dumps(record, indent=2))
    step = 'authentication'
    try:
        session = boto3.Session(profile_name='airwise', region_name=REGION)
        session.client('sts', config=CONFIG).get_caller_identity()
        lam = session.client('lambda', config=CONFIG)
        step = 'existing_lambda_preflight'
        config = lam.get_function_configuration(FunctionName=FUNCTION)
        assert config['Runtime'] == 'python3.12' and config['Architectures'] == ['x86_64']
        assert config['MemorySize'] == 1024 and config['Timeout'] == 28
        assert config['CodeSha256'] == base64.b64encode(bytes.fromhex(BASE_SHA)).decode()
        assert lam.list_tags(Resource=config['FunctionArn'])['Tags']['Project'] == 'AirWiseSchools'
        amp = session.client('amplify', config=CONFIG)
        app = amp.get_app(appId=APP)['app']
        assert app['name'] == 'airwise-schools-web-a1f7411817' and app['tags']['Project'] == 'AirWiseSchools'
        s3 = session.client('s3', config=Config(connect_timeout=4, read_timeout=60, retries={'total_max_attempts': 1}))
        step = 'artifact_upload_once'
        key = f"application/features/{record['sha256']}/airwise-app-features.zip"
        save(object_key=key)
        s3.put_object(Bucket=BUCKET, Key=key, Body=Path(record['archive']).read_bytes(),
                      ServerSideEncryption='AES256', ChecksumSHA256=base64.b64encode(bytes.fromhex(record['sha256'])).decode())
        save(status='UPLOADED')
        head = s3.head_object(Bucket=BUCKET, Key=key, ChecksumMode='ENABLED')
        assert head['ContentLength'] == record['compressed_bytes']
        assert head.get('ChecksumSHA256') == base64.b64encode(bytes.fromhex(record['sha256'])).decode()
        step = 'update_existing_lambda_code'
        lam.update_function_code(FunctionName=FUNCTION, S3Bucket=BUCKET, S3Key=key, RevisionId=config['RevisionId'])
        save(status='LAMBDA_UPDATING')
        for _ in range(20):
            current = lam.get_function_configuration(FunctionName=FUNCTION)
            if current['LastUpdateStatus'] == 'Successful':
                assert current['CodeSha256'] == base64.b64encode(bytes.fromhex(record['sha256'])).decode()
                break
            if current['LastUpdateStatus'] == 'Failed':
                raise RuntimeError('Lambda update failed')
            time.sleep(3)
        else:
            raise RuntimeError('Lambda update observation timed out')
        save(status='LAMBDA_UPDATED')
        step = 'static_archive'
        static = ROOT / 'work/airwise-web-features.zip'
        if static.exists():
            raise RuntimeError('Static archive exists; inspect')
        assert 'https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com' in ''.join(p.read_text() for p in (ROOT / 'frontend/dist/assets').glob('*.js'))
        with zipfile.ZipFile(static, 'w', zipfile.ZIP_DEFLATED) as archive:
            for file in sorted((ROOT / 'frontend/dist').rglob('*')):
                if file.is_file():
                    assert file.suffix != '.map'
                    archive.write(file, file.relative_to(ROOT / 'frontend/dist').as_posix())
        step = 'existing_amplify_deployment'
        deployment = amp.create_deployment(appId=APP, branchName='main')
        save(job_id=deployment['jobId'], status='HOSTING_UPLOAD_PENDING')
        # Never persist/print presigned URL or provider exception messages.
        with urlopen(Request(deployment['zipUploadUrl'], data=static.read_bytes(), method='PUT',
                             headers={'Content-Type': 'application/zip'}), timeout=30) as response:
            assert response.status in (200, 201)
        amp.start_deployment(appId=APP, branchName='main', jobId=deployment['jobId'])
        for _ in range(40):
            status = amp.get_job(appId=APP, branchName='main', jobId=deployment['jobId'])['job']['summary']['status']
            if status == 'SUCCEED': break
            if status in ('FAILED', 'CANCELLED'): raise RuntimeError('Hosting job failed')
            time.sleep(3)
        else: raise RuntimeError('Hosting observation timed out')
        save(status='DEPLOYED_NOT_BROWSER_VERIFIED', static_bytes=static.stat().st_size)
        print(json.dumps({'status': record['status'], 'job_id': record['job_id'], 'object_key': key,
                          'app_url': 'https://main.d29v8cmldu93l3.amplifyapp.com'}))
    except Exception as error:
        save(failure_step=step, error_class=type(error).__name__, status='STOPPED')
        print(json.dumps({'failure_step': step, 'error_class': type(error).__name__, 'status': 'STOPPED',
                          'archive': record['archive'], 'object_key': record.get('object_key')}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['package', 'update'])
    args = parser.parse_args()
    package() if args.action == 'package' else update()
