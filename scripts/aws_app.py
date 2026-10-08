"""Guarded Sydney application deployment. One upload attempt; record partial resources."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
import time
from urllib.request import urlopen

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]
REGION = 'ap-southeast-2'
NAME = 'airwise-app-api-a1f7411817'
ROLE = 'airwise-app-role-a1f7411817'
BUCKET = 'airwise-smoke-artifacts-a1f7411817'
MANIFEST = ROOT / 'work/aws-d2.json'
TAGS = {'Project': 'AirWiseSchools', 'Packet': 'D2', 'Purpose': 'ApplicationAPI'}
CONFIG = Config(connect_timeout=4, read_timeout=20, retries={'total_max_attempts': 1})


def route_definitions(app):
    for path, operations in app.openapi()['paths'].items():
        path = path.replace('{draft_id}', '{plan_id}')
        for method in operations:
            if method in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options'):
                yield {'RouteKey': f'{method.upper()} {path}', 'AuthorizationType': 'NONE' if path == '/health' else 'JWT'}


def absent(client, method, arguments, missing):
    try:
        getattr(client, method)(**arguments)
    except ClientError as error:
        if error.response['Error']['Code'] == missing:
            return
        raise
    raise RuntimeError('Resource collision: refusing overwrite')


def verify_object(s3, record, account):
    head = s3.head_object(Bucket=BUCKET, Key=record['key'], ChecksumMode='ENABLED', ExpectedBucketOwner=account)
    if head['ContentLength'] != record['compressed_bytes']:
        raise RuntimeError('S3 object size differs from package')
    evidence = {'size': head['ContentLength'], 'checksum_type': head.get('ChecksumType'),
                'custom_metadata_is_checksum': False, 'verified_full_checksum': None}
    if head.get('ChecksumType') == 'FULL_OBJECT':
        if head.get('ChecksumSHA256'):
            expected = base64.b64encode(bytes.fromhex(record['sha256'])).decode()
            if head['ChecksumSHA256'] != expected:
                raise RuntimeError('S3 SHA256 differs from package')
            evidence['verified_full_checksum'] = 'SHA256'
        elif head.get('ChecksumCRC64NVME'):
            from awscrt.checksums import crc64nvme
            crc = 0
            with Path(record['archive']).open('rb') as source:
                while block := source.read(1024 * 1024):
                    crc = crc64nvme(block, crc)
            expected = base64.b64encode(struct.pack('>Q', crc)).decode()
            if expected != head['ChecksumCRC64NVME']:
                raise RuntimeError('S3 CRC64 differs from package')
            evidence['verified_full_checksum'] = 'CRC64NVME'
    record['s3_verification'] = evidence
    print(json.dumps(evidence), flush=True)


def deploy(existing_object=False):
    package = json.loads((ROOT / 'work/d2-package.json').read_text())
    archive = Path(package['archive'])
    if hashlib.sha256(archive.read_bytes()).hexdigest() != package['sha256']:
        raise RuntimeError('Package changed after inspection')
    if package['uncompressed_bytes'] > 250 * 1024 * 1024:
        raise RuntimeError('Extracted package too large')
    record = {**package, 'region': REGION, 'function': NAME, 'role': ROLE, 'bucket': BUCKET,
              'key': f"application/d2/{package['sha256']}/airwise-app-d2.zip", 'created': []}
    if MANIFEST.exists() and json.loads(MANIFEST.read_text()).get('created'):
        raise RuntimeError('Partial deployment exists: inspect manifest/resources before resuming')
    def save(kind=None, **values):
        record.update(values)
        if kind:
            record['created'].append(kind)
        MANIFEST.write_text(json.dumps(record, indent=2))
        if kind:
            print('Created ' + kind, flush=True)
    session = boto3.Session(profile_name='airwise', region_name=REGION)
    clients = {name: session.client(name, config=CONFIG) for name in ('sts', 'iam', 'lambda', 'logs', 'apigatewayv2', 'dynamodb', 'cognito-idp')}
    identity = clients['sts'].get_caller_identity()
    if ':assumed-role/' not in identity['Arn']:
        raise RuntimeError('Expected existing temporary assumed-role deployment identity')
    account = identity['Account']
    local = json.loads((ROOT / 'work/aws-b2.json').read_text())
    if local['region'] != REGION or local['profile'] != 'airwise':
        raise RuntimeError('Existing region/profile configuration differs')
    table = clients['dynamodb'].describe_table(TableName=local['table'])['Table']
    if table['TableStatus'] != 'ACTIVE' or table['TableName'] != 'airwise-b2-data-a1f7411817':
        raise RuntimeError('Unexpected existing table')
    app_client = clients['cognito-idp'].describe_user_pool_client(UserPoolId=local['pool_id'], ClientId=local['client_id'])['UserPoolClient']
    if app_client.get('ClientSecret') or 'ALLOW_USER_PASSWORD_AUTH' not in app_client['ExplicitAuthFlows']:
        raise RuntimeError('Existing public Cognito client is incompatible')
    iam = clients['iam']
    policies = [iam.get_role_policy(RoleName=local['role'], PolicyName=name)['PolicyDocument']
                for name in ('airwise-b2-table-runtime', 'airwise-c-nova-lite')]
    allowed = {'dynamodb:GetItem', 'dynamodb:Query', 'dynamodb:PutItem', 'bedrock:InvokeModel'}
    for policy in policies:
        for statement in policy['Statement']:
            if statement['Effect'] != 'Allow' or statement['Action'] not in allowed or statement['Resource'] not in (
                    table['TableArn'], f'arn:aws:bedrock:{REGION}::foundation-model/amazon.nova-lite-v1:0'):
                raise RuntimeError('Existing runtime policy exceeds expected exact scope')
            if statement['Action'].startswith('dynamodb:') and not statement.get('Condition'):
                raise RuntimeError('Missing existing partition/transaction restrictions')
    absent(iam, 'get_role', {'RoleName': ROLE}, 'NoSuchEntity')
    absent(clients['lambda'], 'get_function', {'FunctionName': NAME}, 'ResourceNotFoundException')
    for page in clients['apigatewayv2'].get_paginator('get_apis').paginate():
        if any(api['Name'] == NAME for api in page['Items']):
            raise RuntimeError('HTTP API name collision')
    log_groups = [f'/aws/lambda/{NAME}', f'/aws/apigateway/{NAME}']
    for group in log_groups:
        found = clients['logs'].describe_log_groups(logGroupNamePrefix=group)['logGroups']
        if any(g['logGroupName'] == group for g in found):
            raise RuntimeError('Log group collision')
    if clients['lambda'].get_account_settings()['AccountLimit']['UnreservedConcurrentExecutions'] < 105:
        raise RuntimeError('Cannot reserve five executions without changing account quotas')
    s3 = session.client('s3', config=Config(connect_timeout=4, read_timeout=90,
        retries={'total_max_attempts': 1}, request_checksum_calculation='when_required',
        response_checksum_validation='when_required', s3={'addressing_style': 'path'}))
    if s3.get_bucket_location(Bucket=BUCKET, ExpectedBucketOwner=account)['LocationConstraint'] != REGION:
        raise RuntimeError('Artifact bucket region differs')
    if not all(s3.get_public_access_block(Bucket=BUCKET, ExpectedBucketOwner=account)['PublicAccessBlockConfiguration'].values()):
        raise RuntimeError('Artifact bucket public access is not fully blocked')
    save()
    if not existing_object:
        absent(s3, 'head_object', {'Bucket': BUCKET, 'Key': record['key'], 'ExpectedBucketOwner': account}, '404')
        print('One bounded S3 upload attempt', flush=True)
        try:
            with archive.open('rb') as source:
                s3.put_object(Bucket=BUCKET, Key=record['key'], Body=source,
                    ContentLength=record['compressed_bytes'], ExpectedBucketOwner=account,
                    ServerSideEncryption='AES256', IfNoneMatch='*',
                    ChecksumSHA256=base64.b64encode(bytes.fromhex(record['sha256'])).decode())
        except Exception as error:
            save(upload_status='UNKNOWN_OR_FAILED', upload_error_type=type(error).__name__,
                 upload_error_code=error.response['Error']['Code'] if isinstance(error, ClientError) else None)
            print(json.dumps({'console_upload_file': str(archive), 'bucket': BUCKET, 'key': record['key'],
                              'size': record['compressed_bytes'], 'sha256': record['sha256']}), flush=True)
            raise RuntimeError('Single upload failed; inspect/upload through console, no automatic retry') from None
    verify_object(s3, record, account)
    save(upload_status='VERIFIED')
    for group in log_groups:
        clients['logs'].create_log_group(logGroupName=group, tags=TAGS)
        save('log:' + group)
        clients['logs'].put_retention_policy(logGroupName=group, retentionInDays=7)
    trust = {'Version': '2012-10-17', 'Statement': [{'Effect': 'Allow', 'Principal': {'Service': 'lambda.amazonaws.com'}, 'Action': 'sts:AssumeRole'}]}
    role = iam.create_role(RoleName=ROLE, AssumeRolePolicyDocument=json.dumps(trust), Tags=[{'Key': k, 'Value': v} for k, v in TAGS.items()])['Role']
    save('execution_role')
    statements = [statement for policy in policies for statement in policy['Statement']]
    statements.append({'Effect': 'Allow', 'Action': ['logs:CreateLogStream', 'logs:PutLogEvents'],
        'Resource': f'arn:aws:logs:{REGION}:{account}:log-group:{log_groups[0]}:log-stream:*'})
    iam.put_role_policy(RoleName=ROLE, PolicyName='airwise-app-runtime', PolicyDocument=json.dumps({'Version': '2012-10-17', 'Statement': statements}))
    env = {'AIRWISE_RUNTIME': 'lambda', 'AIRWISE_TABLE': local['table'], 'AIRWISE_POOL_ID': local['pool_id'],
           'AIRWISE_CLIENT_ID': local['client_id'], 'AWS_EC2_METADATA_DISABLED': 'true'}
    for attempt in range(4):
        try:
            function = clients['lambda'].create_function(FunctionName=NAME, Runtime='python3.12', Architectures=['x86_64'],
                Role=role['Arn'], Handler='backend.app.lambda_app.handler', Code={'S3Bucket': BUCKET, 'S3Key': record['key']},
                Timeout=28, MemorySize=1024, Environment={'Variables': env}, Tags=TAGS)
            break
        except ClientError as error:
            if attempt == 3 or error.response['Error']['Code'] != 'InvalidParameterValueException' or 'cannot be assumed' not in error.response['Error']['Message']:
                raise
            time.sleep(5)
    save('application_lambda')
    clients['lambda'].put_function_concurrency(FunctionName=NAME, ReservedConcurrentExecutions=5)
    clients['lambda'].get_waiter('function_active_v2').wait(FunctionName=NAME, WaiterConfig={'Delay': 2, 'MaxAttempts': 30})
    configuration = clients['lambda'].get_function_configuration(FunctionName=NAME)
    expected = base64.b64encode(bytes.fromhex(record['sha256'])).decode()
    if configuration['CodeSha256'] != expected or configuration['Runtime'] != 'python3.12' or configuration['Architectures'] != ['x86_64']:
        raise RuntimeError('Deployed package/runtime mismatch')
    save(code_sha256_matches=True)
    gateway = clients['apigatewayv2']
    api = gateway.create_api(Name=NAME, ProtocolType='HTTP', Tags=TAGS, CorsConfiguration={
        'AllowOrigins': ['http://127.0.0.1:5173'], 'AllowMethods': ['GET', 'POST', 'PUT', 'OPTIONS'],
        'AllowHeaders': ['authorization', 'content-type'], 'MaxAge': 300})
    api_id = api['ApiId']
    save('http_api', api_id=api_id, api_url=api['ApiEndpoint'])
    authorizer = gateway.create_authorizer(ApiId=api_id, Name='airwise-cognito-access', AuthorizerType='JWT',
        IdentitySource=['$request.header.Authorization'], JwtConfiguration={
            'Audience': [local['client_id']], 'Issuer': f"https://cognito-idp.{REGION}.amazonaws.com/{local['pool_id']}"})
    integration = gateway.create_integration(ApiId=api_id, IntegrationType='AWS_PROXY', IntegrationUri=function['FunctionArn'],
        PayloadFormatVersion='2.0', TimeoutInMillis=30000)
    from backend.app.lambda_app import app
    for definition in route_definitions(app):
        arguments = dict(ApiId=api_id, Target='integrations/' + integration['IntegrationId'], **definition)
        if definition['AuthorizationType'] == 'JWT':
            arguments.update(AuthorizerId=authorizer['AuthorizerId'], AuthorizationScopes=['aws.cognito.signin.user.admin'])
        gateway.create_route(**arguments)
    clients['lambda'].add_permission(FunctionName=NAME, StatementId='airwise-http-api', Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com', SourceAccount=account, SourceArn=f'arn:aws:execute-api:{REGION}:{account}:{api_id}/*/*/*')
    gateway.create_stage(ApiId=api_id, StageName='$default', AutoDeploy=True, Tags=TAGS,
        DefaultRouteSettings={'ThrottlingBurstLimit': 10, 'ThrottlingRateLimit': 5.0},
        RouteSettings={key: {'ThrottlingBurstLimit': 1, 'ThrottlingRateLimit': 0.2} for key in ('POST /notice-analyses', 'GET /draft-plans/{plan_id}/explanation')},
        AccessLogSettings={'DestinationArn': f'arn:aws:logs:{REGION}:{account}:log-group:{log_groups[1]}',
            'Format': '{"requestId":"$context.requestId","route":"$context.routeKey","status":"$context.status","latency":"$context.integrationLatency"}'})
    save('http_stage', deployment_status='CREATED_NOT_WORKFLOW_VERIFIED')
    print(json.dumps({'api_url': api['ApiEndpoint'], 'function': NAME, 'role': ROLE, 'created': record['created']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--existing-object', action='store_true')
    args = parser.parse_args()
    try:
        deploy(args.existing_object)
    except Exception as error:
        print(re.sub(r'\d{12}', '[REDACTED]', str(error)), flush=True)
        raise SystemExit(1) from None
