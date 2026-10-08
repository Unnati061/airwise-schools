"""Create only B2's private data/auth resources; never prints credentials."""
import argparse
import json
from pathlib import Path
import re
import secrets

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from backend.app.auth import AWS_CONFIG, REGION
from backend.app.durable_store import DynamoStore
from backend.app.workflow import SCHOOL

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "work" / "aws-b2.json"
TAGS = {"Project": "AirWiseSchools", "Packet": "B2", "Purpose": "SyntheticApprovalExecution"}
TABLE = "airwise-b2-data-a1f7411817"
POOL = "airwise-b2-users-a1f7411817"
ROLE = "airwise-b2-runtime-a1f7411817"
USERS = [("synthetic-admin", "administrator", None),
         ("synthetic-teacher-a", "teacher", "teacher-6-a"),
         ("synthetic-teacher-b", "teacher", "teacher-6-b")]


def deploy():
    if MANIFEST.exists():
        raise RuntimeError("B2 manifest exists; inspect partial resources before any retry")
    session = boto3.Session(profile_name="airwise", region_name=REGION)
    sts, ddb, cognito, iam = [session.client(name, config=AWS_CONFIG) for name in ("sts", "dynamodb", "cognito-idp", "iam")]
    print("Preflight: STS identity", flush=True)
    identity = sts.get_caller_identity()
    account = identity["Account"]
    if ":assumed-role/" not in identity["Arn"]:
        raise RuntimeError("Expected authenticated non-root assumed-role deployment identity")
    print("Preflight: source IAM role", flush=True)
    source_role = iam.get_role(RoleName=identity["Arn"].split("/")[1])["Role"]["Arn"]
    for client, method, args, missing in ((ddb, "describe_table", {"TableName": TABLE}, "ResourceNotFoundException"),
                                          (iam, "get_role", {"RoleName": ROLE}, "NoSuchEntity")):
        print(f"Preflight: {method}", flush=True)
        try:
            getattr(client, method)(**args)
        except ClientError as error:
            if error.response["Error"]["Code"] != missing:
                raise
        else:
            raise RuntimeError("Resource name collision; refusing overwrite")
    print("Preflight: Cognito user pools", flush=True)
    for page in cognito.get_paginator("list_user_pools").paginate(MaxResults=60):
        if any(p["Name"] == POOL for p in page["UserPools"]):
            raise RuntimeError("User pool name collision; refusing overwrite")
    record = {"region": REGION, "profile": "airwise", "table": TABLE, "pool_name": POOL, "role": ROLE, "created": []}
    def saved(kind, **values):
        record.update(values)
        record["created"].append(kind)
        MANIFEST.parent.mkdir(exist_ok=True)
        MANIFEST.write_text(json.dumps(record, indent=2))
        print(f"Created {kind}", flush=True)
    table = ddb.create_table(TableName=TABLE, AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"},
                            {"AttributeName": "sk", "AttributeType": "S"}],
                            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
                            BillingMode="PAY_PER_REQUEST", SSESpecification={"Enabled": True},
                            Tags=[{"Key": k, "Value": v} for k, v in TAGS.items()])["TableDescription"]
    saved("table")
    ddb.get_waiter("table_exists").wait(TableName=TABLE, WaiterConfig={"Delay": 3, "MaxAttempts": 30})
    pool = cognito.create_user_pool(PoolName=POOL, UserPoolTier="LITE", UserPoolTags=TAGS,
           AdminCreateUserConfig={"AllowAdminCreateUserOnly": True}, MfaConfiguration="OFF",
           AccountRecoverySetting={"RecoveryMechanisms": [{"Priority": 1, "Name": "admin_only"}]},
           UsernameConfiguration={"CaseSensitive": False},
           Policies={"PasswordPolicy": {"MinimumLength": 16, "RequireUppercase": True, "RequireLowercase": True,
                     "RequireNumbers": True, "RequireSymbols": True, "TemporaryPasswordValidityDays": 7}})["UserPool"]
    saved("user_pool", pool_id=pool["Id"])
    client = cognito.create_user_pool_client(UserPoolId=pool["Id"], ClientName="airwise-b2-local", GenerateSecret=False,
             ExplicitAuthFlows=["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
             PreventUserExistenceErrors="ENABLED", EnableTokenRevocation=True,
             AccessTokenValidity=15, IdTokenValidity=15, RefreshTokenValidity=1,
             TokenValidityUnits={"AccessToken": "minutes", "IdToken": "minutes", "RefreshToken": "days"})["UserPoolClient"]
    saved("app_client", client_id=client["ClientId"])
    store = DynamoStore(ddb, TABLE)
    for username, role, teacher_id in USERS:
        temporary = "Aa1!" + secrets.token_urlsafe(30)
        user = cognito.admin_create_user(UserPoolId=pool["Id"], Username=username, MessageAction="SUPPRESS",
                                        TemporaryPassword=temporary)["User"]
        del temporary
        sub = next(a["Value"] for a in user["Attributes"] if a["Name"] == "sub")
        store.transact([store.put("IDENTITIES", sub, {"sub": sub, "school_id": SCHOOL, "role": role, "teacher_id": teacher_id}, create=True)])
        saved(username)
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"AWS": source_role}, "Action": "sts:AssumeRole"}]}
    runtime_role = iam.create_role(RoleName=ROLE, AssumeRolePolicyDocument=json.dumps(trust),
                     Description="AirWise B2 local synthetic workflow; exact data table only",
                     Tags=[{"Key": k, "Value": v} for k, v in TAGS.items()])["Role"]
    saved("runtime_role", runtime_role_arn=runtime_role["Arn"])
    arn = f"arn:aws:dynamodb:{REGION}:{account}:table/{TABLE}"
    policy = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": "dynamodb:GetItem", "Resource": arn,
         "Condition": {"ForAllValues:StringEquals": {"dynamodb:LeadingKeys": [SCHOOL, "IDENTITIES"]}}},
        {"Effect": "Allow", "Action": "dynamodb:Query", "Resource": arn,
         "Condition": {"ForAllValues:StringEquals": {"dynamodb:LeadingKeys": [SCHOOL]}}},
        {"Effect": "Allow", "Action": "dynamodb:PutItem", "Resource": arn,
         "Condition": {"ForAllValues:StringEquals": {"dynamodb:LeadingKeys": [SCHOOL]},
                       "StringEquals": {"dynamodb:EnclosingOperation": "TransactWriteItems"}}}]}
    iam.put_role_policy(RoleName=ROLE, PolicyName="airwise-b2-table-runtime", PolicyDocument=json.dumps(policy))
    saved("runtime_policy")
    print("B2 provisioned; synthetic user passwords must be set privately before sign-in.")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        deploy()
    except ClientError as error:
        print(json.dumps({"error_code": error.response["Error"]["Code"],
                          "message": re.sub(r"\b\d{12}\b", "[REDACTED]", error.response["Error"]["Message"])}))
        raise SystemExit(1)
    except BotoCoreError as error:
        endpoint = getattr(error, "kwargs", {}).get("endpoint_url", "unavailable")
        print(f"AWS transport failure: {type(error).__name__}, endpoint {endpoint}; inspect recorded partial resources")
        raise SystemExit(1)
