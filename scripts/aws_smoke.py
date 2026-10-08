"""Create an isolated private runtime spike; never update existing resources."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
import struct
import time
import uuid
import zipfile

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "work" / "aws-smoke.json"


def validate_plan(record):
    expected = {"profile": "airwise", "region": "ap-southeast-2", "runtime": "python3.12",
                "architecture": "x86_64", "memory_mb": 1024, "timeout_seconds": 30}
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("Configuration differs from the authorized smoke deployment")
    for key, prefix in (("bucket", "airwise-smoke-artifacts-"), ("role", "airwise-smoke-role-"),
                        ("function", "airwise-runtime-smoke-")):
        if not re.fullmatch(re.escape(prefix) + r"[a-f0-9]{10}", record[key]):
            raise ValueError("Unexpected resource name")
    if record["log_group"] != f"/aws/lambda/{record['function']}" or record["key"] != "runtime-smoke.zip":
        raise ValueError("Unexpected log group or object key")
    if record["uncompressed_bytes"] > 250 * 1024 * 1024:
        raise ValueError("Package too large")


def upload_inspected_zip(s3, archive, record):
    upload = s3.create_multipart_upload(Bucket=record["bucket"], Key=record["key"],
        ChecksumAlgorithm="SHA256", Metadata={"sha256": record["sha256"]})
    upload_id = upload["UploadId"]
    parts = []
    try:
        with archive.open("rb") as stream:
            while chunk := stream.read(5 * 1024 * 1024):
                number = len(parts) + 1
                checksum = base64.b64encode(hashlib.sha256(chunk).digest()).decode()
                response = s3.upload_part(Bucket=record["bucket"], Key=record["key"], UploadId=upload_id,
                    PartNumber=number, Body=chunk, ContentLength=len(chunk), ChecksumSHA256=checksum)
                parts.append({"PartNumber": number, "ETag": response["ETag"], "ChecksumSHA256": checksum})
                print(f"Uploaded verified part {number}", flush=True)
        s3.complete_multipart_upload(Bucket=record["bucket"], Key=record["key"], UploadId=upload_id,
                                    MultipartUpload={"Parts": parts})
    except Exception:
        # Only the incomplete upload created by this call is eligible for cancellation.
        try:
            s3.abort_multipart_upload(Bucket=record["bucket"], Key=record["key"], UploadId=upload_id)
        except (BotoCoreError, ClientError):
            print("Could not cancel this incomplete upload; inspect before cleanup", flush=True)
        raise


def prepare():
    source = ROOT / "work" / "airwise-lambda.zip"
    target = ROOT / "work" / "airwise-runtime-smoke.zip"
    if target.exists() or MANIFEST.exists():
        raise RuntimeError("Prepared smoke artifact or manifest exists; inspect before another run")
    with zipfile.ZipFile(source) as original:
        if original.testzip() is not None:
            raise RuntimeError("Corrupt source archive")
        for name in original.namelist():
            if name.endswith((".dll", ".pyd")):
                raise RuntimeError("Windows native binary in archive")
            if name.endswith(".so"):
                header = original.read(name)[:20]
                if header[:6] != b"\x7fELF\x02\x01" or struct.unpack("<H", header[18:20])[0] != 62:
                    raise RuntimeError(f"Not Linux ELF64 x86_64: {name}")
            if name.endswith(".dist-info/WHEEL"):
                tags = [line[5:] for line in original.read(name).decode().splitlines() if line.startswith("Tag: ")]
                if not any(tag.endswith("-any") or ("x86_64" in tag and
                           (tag.startswith("cp312-") or "-abi3-" in tag)) for tag in tags):
                    raise RuntimeError(f"Unexpected wheel compatibility: {name}: {tags}")
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as output:
            for item in original.infolist():
                content = ((ROOT / item.filename).read_bytes()
                           if item.filename == "backend/app/lambda_smoke.py" else original.read(item))
                output.writestr(item, content)
    with zipfile.ZipFile(target) as archive:
        total = sum(item.file_size for item in archive.infolist())
        if total > 250 * 1024 * 1024:
            raise RuntimeError("Extracted archive exceeds 250 MiB (no layers)")
    suffix = uuid.uuid4().hex[:10]
    record = {
        "profile": "airwise", "region": "ap-southeast-2", "runtime": "python3.12",
        "architecture": "x86_64", "memory_mb": 1024, "timeout_seconds": 30,
        "bucket": f"airwise-smoke-artifacts-{suffix}",
        "role": f"airwise-smoke-role-{suffix}", "function": f"airwise-runtime-smoke-{suffix}",
        "key": "runtime-smoke.zip", "archive": str(target),
        "compressed_bytes": target.stat().st_size, "uncompressed_bytes": total,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "created": [],
    }
    record["log_group"] = f"/aws/lambda/{record['function']}"
    validate_plan(record)
    MANIFEST.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


def deploy(resume_upload=False):
    record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate_plan(record)
    if record["created"] and not (resume_upload and record["created"] == ["bucket"]):
        raise RuntimeError("Previous creation recorded; do not overwrite or blindly retry")
    archive = Path(record["archive"])
    if hashlib.sha256(archive.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError("Artifact changed after validation")
    session = boto3.Session(profile_name="airwise", region_name="ap-southeast-2")
    config = Config(connect_timeout=5, read_timeout=30, retries={"mode": "standard", "total_max_attempts": 1},
                    request_checksum_calculation="when_required", response_checksum_validation="when_required",
                    s3={"addressing_style": "path"})
    print("Checking authenticated Sydney identity", flush=True)
    account = session.client("sts", config=config).get_caller_identity()["Account"]
    s3, iam, logs, lam = [session.client(name, config=config) for name in ("s3", "iam", "logs", "lambda")]
    # Refuse existing names before the first write, including the global bucket name.
    checks = [(iam.get_role, {"RoleName": record["role"]}, "NoSuchEntity"),
              (lam.get_function, {"FunctionName": record["function"]}, "ResourceNotFoundException")]
    if not resume_upload:
        checks.insert(0, (s3.head_bucket, {"Bucket": record["bucket"]}, "404"))
    for call, arguments, missing in checks:
        print(f"Checking name collision: {call.__name__}", flush=True)
        try:
            call(**arguments)
        except ClientError as error:
            if error.response["Error"]["Code"] != missing:
                raise
        else:
            raise RuntimeError("Name collision: refusing to change existing resource")
    if any(group["logGroupName"] == record["log_group"] for group in
           logs.describe_log_groups(logGroupNamePrefix=record["log_group"])["logGroups"]):
        raise RuntimeError("Log group already exists")
    tags = {"Project": "AirWiseSchools", "Purpose": "NativeRuntimeSmoke", "Packet": "A"}

    def saved(kind):
        record["created"].append(kind)
        MANIFEST.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"Created {kind}", flush=True)

    artifact_exists = False
    if resume_upload:
        print("Validating recorded Sydney bucket and missing artifact", flush=True)
        if record["created"] != ["bucket"]:
            raise RuntimeError("Resume is limited to the recorded bucket-only upload failure")
        if s3.get_bucket_location(Bucket=record["bucket"])["LocationConstraint"] != "ap-southeast-2":
            raise RuntimeError("Wrong bucket region")
        actual_tags = {item["Key"]: item["Value"] for item in s3.get_bucket_tagging(Bucket=record["bucket"])["TagSet"]}
        if actual_tags != tags:
            raise RuntimeError("Bucket ownership tags do not match this spike")
        try:
            existing = s3.head_object(Bucket=record["bucket"], Key=record["key"])
        except ClientError as error:
            if error.response["Error"]["Code"] != "404":
                raise
        else:
            if existing["ContentLength"] != record["compressed_bytes"] or existing.get("Metadata", {}).get("sha256") != record["sha256"]:
                raise RuntimeError("Existing artifact does not match inspected ZIP")
            artifact_exists = True
    else:
        s3.create_bucket(Bucket=record["bucket"], ObjectOwnership="BucketOwnerEnforced",
                         CreateBucketConfiguration={"LocationConstraint": "ap-southeast-2"})
        saved("bucket")
    s3.put_public_access_block(Bucket=record["bucket"], PublicAccessBlockConfiguration={
        name: True for name in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")})
    s3.put_bucket_tagging(Bucket=record["bucket"], Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in tags.items()]})
    s3.put_bucket_encryption(Bucket=record["bucket"], ServerSideEncryptionConfiguration={
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]})
    if not artifact_exists:
        print("Starting inspected ZIP upload", flush=True)
        upload_inspected_zip(s3, archive, record)
    print("Inspected ZIP available through S3", flush=True)
    role = iam.create_role(RoleName=record["role"], AssumeRolePolicyDocument=json.dumps({
        "Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"}]}), Tags=[{"Key": k, "Value": v} for k, v in tags.items()])
    saved("role")
    logs.create_log_group(logGroupName=record["log_group"], tags=tags)
    saved("log_group")
    logs.put_retention_policy(logGroupName=record["log_group"], retentionInDays=7)
    iam.put_role_policy(RoleName=record["role"], PolicyName="airwise-smoke-logging", PolicyDocument=json.dumps({
        "Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource": f"arn:aws:logs:ap-southeast-2:{account}:log-group:{record['log_group']}:log-stream:*"}]}))
    for attempt in range(12):
        try:
            lam.create_function(FunctionName=record["function"], Runtime="python3.12", Architectures=["x86_64"],
                Role=role["Role"]["Arn"], Handler="backend.app.lambda_smoke.handler",
                Code={"S3Bucket": record["bucket"], "S3Key": record["key"]},
                Timeout=30, MemorySize=1024, Tags=tags, Publish=False)
            break
        except ClientError as error:
            if error.response["Error"]["Code"] != "InvalidParameterValueException" or "cannot be assumed" not in str(error):
                raise
            if attempt == 11:
                raise
            time.sleep(5)
    saved("function")
    lam.get_waiter("function_active_v2").wait(FunctionName=record["function"], WaiterConfig={"Delay": 5, "MaxAttempts": 24})
    config = lam.get_function_configuration(FunctionName=record["function"])
    assert (config["Runtime"], config["Architectures"], config["MemorySize"], config["Timeout"]) == ("python3.12", ["x86_64"], 1024, 30)
    assert not config.get("Layers") and not config.get("VpcConfig", {}).get("VpcId")
    assert config["CodeSha256"] == base64.b64encode(bytes.fromhex(record["sha256"])).decode()
    print("Deployment active; ready for authenticated CLI invocation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "deploy", "resume-upload"])
    args = parser.parse_args()
    try:
        prepare() if args.action == "prepare" else deploy(resume_upload=args.action == "resume-upload")
    except ClientError as error:
        print(json.dumps({"aws_error_code": error.response["Error"]["Code"],
                          "message": re.sub(r"\b\d{12}\b", "[REDACTED]", error.response["Error"]["Message"])}))
        raise SystemExit(1)
    except BotoCoreError as error:
        print(json.dumps({"transport_error": type(error).__name__, "message": "AWS transport failed; no credentials displayed"}))
        raise SystemExit(1)
