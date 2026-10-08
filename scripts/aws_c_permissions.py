"""Add only in-region Nova Lite invocation to the owned B2 runtime role."""
import json

import boto3
from botocore.exceptions import ClientError

from backend.app.auth import AWS_CONFIG, REGION, settings
from backend.app.notice_provider import MODEL


def configure():
    config = settings()
    client = boto3.Session(profile_name="airwise", region_name=REGION).client("iam", config=AWS_CONFIG)
    role = client.get_role(RoleName=config["role"])["Role"]
    if role["Arn"] != config["runtime_role_arn"] or {t["Key"]: t["Value"] for t in role["Tags"]}.get("Project") != "AirWiseSchools":
        raise RuntimeError("Unexpected role ownership")
    policy = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "bedrock:InvokeModel",
              "Resource": f"arn:aws:bedrock:{REGION}::foundation-model/{MODEL}"}]}
    name = "airwise-c-nova-lite"
    try:
        existing = client.get_role_policy(RoleName=config["role"], PolicyName=name)["PolicyDocument"]
    except ClientError as error:
        if error.response["Error"]["Code"] != "NoSuchEntity":
            raise
    else:
        if existing != policy:
            raise RuntimeError("Policy collision; refusing overwrite")
        print("Exact scoped policy already present")
        return
    client.put_role_policy(RoleName=config["role"], PolicyName=name, PolicyDocument=json.dumps(policy))
    print("Added only airwise-c-nova-lite to the existing owned B2 runtime role; no cross-region or streaming permissions")


if __name__ == "__main__":
    try:
        configure()
    except Exception as error:
        print(f"Permission configuration failed: {type(error).__name__}; no success claimed")
        raise SystemExit(1)
