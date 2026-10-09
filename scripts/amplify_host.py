"""Manual static hosting; keep presigned upload URLs out of logs/manifests."""
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
import zipfile

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]
REGION = 'ap-southeast-2'
NAME = 'airwise-schools-web-a1f7411817'
API_ID = 'lbckjkbfb4'
API_URL = 'https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com'
MANIFEST = ROOT / 'work/aws-hosting.json'
LIMITS = Config(connect_timeout=4, read_timeout=15, retries={'total_max_attempts': 1})


def deploy():
    if MANIFEST.exists() and json.loads(MANIFEST.read_text()).get('created'):
        print('Partial hosting resources recorded; inspect before resuming', flush=True)
        raise SystemExit(1)
    step = 'preflight'
    record = {'region': REGION, 'name': NAME, 'created': []}
    def save(**values):
        record.update(values)
        MANIFEST.write_text(json.dumps(record, indent=2))
    try:
        session = boto3.Session(profile_name='airwise', region_name=REGION)
        step = 'authentication'
        session.client('sts', config=LIMITS).get_caller_identity()
        amplify = session.client('amplify', config=LIMITS)
        gateway = session.client('apigatewayv2', config=LIMITS)
        step = 'list_existing_amplify_apps'
        for page in amplify.get_paginator('list_apps').paginate():
            if any(app['name'] == NAME for app in page['apps']):
                raise RuntimeError('Hosting name collision; refusing overwrite')
        step = 'read_existing_api_cors'
        api = gateway.get_api(ApiId=API_ID)
        if api['ApiEndpoint'] != API_URL:
            raise RuntimeError('Unexpected API endpoint')
        old_cors = api['CorsConfiguration']
        if old_cors['AllowOrigins'] != ['http://127.0.0.1:5173']:
            raise RuntimeError('Inspect unexpected existing CORS before changing it')
        dist = ROOT / 'frontend/dist'
        scripts = ''.join(p.read_text() for p in (dist / 'assets').glob('*.js'))
        if API_URL not in scripts or '5gq58g4sp2o7ic7grg8k7cld2' not in scripts:
            raise RuntimeError('Build lacks expected public API/Cognito configuration')
        archive = ROOT / 'work/airwise-hosted-web.zip'
        if archive.exists():
            raise RuntimeError('Hosting artifact already exists; inspect before packaging')
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as target:
            for file in sorted(dist.rglob('*')):
                if file.is_file():
                    if file.suffix == '.map':
                        raise RuntimeError('Unexpected source map')
                    target.write(file, file.relative_to(dist).as_posix())
        save(archive=str(archive), size=archive.stat().st_size,
             sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), previous_cors=old_cors)
        step = 'create_app'
        app = amplify.create_app(name=NAME, platform='WEB', enableBranchAutoBuild=False,
            tags={'Project': 'AirWiseSchools', 'Packet': 'Hosting', 'Purpose': 'Frontend'})['app']
        record['created'].append('amplify_app')
        save(app_id=app['appId'], domain=app['defaultDomain'])
        step = 'create_branch'
        amplify.create_branch(appId=app['appId'], branchName='main', stage='PRODUCTION',
                              enableAutoBuild=False, tags={'Project': 'AirWiseSchools', 'Packet': 'Hosting'})
        record['created'].append('main_branch')
        origin = 'https://main.' + app['defaultDomain']
        save(origin=origin)
        step = 'create_deployment'
        deployment = amplify.create_deployment(appId=app['appId'], branchName='main')
        save(job_id=deployment['jobId'])
        step = 'single_artifact_upload'
        # A presigned URL is a secret; never persist it or include errors containing it.
        request = Request(deployment['zipUploadUrl'], data=archive.read_bytes(), method='PUT',
                          headers={'Content-Type': 'application/zip'})
        with urlopen(request, timeout=30) as response:
            if response.status not in (200, 201):
                raise RuntimeError('Artifact upload rejected')
        step = 'start_deployment'
        amplify.start_deployment(appId=app['appId'], branchName='main', jobId=deployment['jobId'])
        step = 'wait_deployment'
        for _ in range(60):
            status = amplify.get_job(appId=app['appId'], branchName='main', jobId=deployment['jobId'])['job']['summary']['status']
            save(job_status=status)
            if status == 'SUCCEED':
                break
            if status in ('FAILED', 'CANCELLED'):
                raise RuntimeError('Hosting deployment failed')
            time.sleep(3)
        else:
            raise RuntimeError('Deployment did not finish within bounded observation window')
        step = 'exact_cors_update'
        cors = {**old_cors, 'AllowOrigins': [*old_cors['AllowOrigins'], origin]}
        gateway.update_api(ApiId=API_ID, CorsConfiguration=cors)
        if gateway.get_api(ApiId=API_ID)['CorsConfiguration'] != cors:
            raise RuntimeError('CORS read-back mismatch')
        save(cors=cors, status='DEPLOYED_NOT_BROWSER_VERIFIED')
        print(json.dumps({'app_id': app['appId'], 'origin': origin, 'job_status': status,
                          'artifact_bytes': record['size'], 'created': record['created']}), flush=True)
    except Exception as error:
        code = error.response['Error']['Code'] if isinstance(error, ClientError) else None
        endpoint = urlsplit(getattr(error, 'kwargs', {}).get('endpoint_url', '')).hostname
        save(failure_step=step, error_type=type(error).__name__, error_code=code, endpoint_host=endpoint)
        print(json.dumps({'failure_step': step, 'error_type': type(error).__name__, 'error_code': code,
                          'endpoint_host': endpoint, 'created': record['created']}), flush=True)
        raise SystemExit(1) from None


if __name__ == '__main__':
    deploy()
