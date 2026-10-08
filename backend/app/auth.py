import json
import os
from functools import lru_cache
from pathlib import Path

import boto3
import botocore.session
from botocore.config import Config
from botocore.credentials import DeferredRefreshableCredentials
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from .durable_store import DynamoStore
from .workflow import Workflow
from .workflow_contracts import Actor

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "work" / "aws-b2.json"
REGION = "ap-southeast-2"
AWS_CONFIG = Config(connect_timeout=5, read_timeout=15, retries={"mode": "standard", "total_max_attempts": 2})
bearer = HTTPBearer(auto_error=False)


@lru_cache
def settings():
    if os.environ.get("AIRWISE_RUNTIME") == "lambda":
        config = {"region": os.environ.get("AWS_REGION"), "table": os.environ.get("AIRWISE_TABLE"),
                  "pool_id": os.environ.get("AIRWISE_POOL_ID", ""), "client_id": os.environ.get("AIRWISE_CLIENT_ID")}
        if config["region"] != REGION or config["table"] != "airwise-b2-data-a1f7411817" or not config["pool_id"].startswith(REGION + "_") or not config["client_id"]:
            raise HTTPException(503, "Unexpected deployed resource configuration")
        return config
    if not CONFIG.exists():
        raise HTTPException(503, "B2 resources are not configured; authentication remains required")
    config = json.loads(CONFIG.read_text())
    if config["region"] != REGION or config["profile"] != "airwise" or not config["pool_id"].startswith(REGION + "_"):
        raise HTTPException(503, "Unexpected B2 resource configuration")
    return config


def runtime_client(config, service="dynamodb"):
    if os.environ.get("AIRWISE_RUNTIME") == "lambda":
        limits = Config(connect_timeout=2, read_timeout=3 if service == "dynamodb" else 18,
                        retries={"total_max_attempts": 1})
        return boto3.Session(region_name=REGION).client(service, config=limits)
    source = boto3.Session(profile_name="airwise", region_name=REGION).client("sts", config=AWS_CONFIG)
    def refresh():
        credentials = source.assume_role(RoleArn=config["runtime_role_arn"], RoleSessionName="airwise-local-b2", DurationSeconds=900)["Credentials"]
        return {"access_key": credentials["AccessKeyId"], "secret_key": credentials["SecretAccessKey"],
                "token": credentials["SessionToken"], "expiry_time": credentials["Expiration"].isoformat()}
    session = botocore.session.get_session()
    session._credentials = DeferredRefreshableCredentials(refresh_using=refresh, method="assume-role")
    session.set_config_variable("region", REGION)
    service_config = AWS_CONFIG if service == "dynamodb" else Config(connect_timeout=5, read_timeout=20, retries={"total_max_attempts": 1})
    return boto3.Session(botocore_session=session).client(service, config=service_config)


@lru_cache
def workflow():
    config = settings()
    return Workflow(DynamoStore(runtime_client(config), config["table"]))


@lru_cache
def key_client():
    issuer = f"https://cognito-idp.{REGION}.amazonaws.com/{settings()['pool_id']}"
    return jwt.PyJWKClient(issuer + "/.well-known/jwks.json", timeout=5)


def verify_token(token):
    config = settings()
    issuer = f"https://cognito-idp.{REGION}.amazonaws.com/{config['pool_id']}"
    try:
        key = key_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(token, key.key, algorithms=["RS256"], issuer=issuer,
                            options={"verify_aud": False, "require": ["exp", "iat", "iss", "sub", "token_use", "client_id"]})
        if claims["token_use"] != "access" or claims["client_id"] != config["client_id"]:
            raise jwt.InvalidTokenError()
        return claims
    except (jwt.PyJWTError, OSError):
        raise HTTPException(401, "Invalid or expired Cognito access token", headers={"WWW-Authenticate": "Bearer"}) from None


def identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), service: Workflow = Depends(workflow)) -> Actor:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Cognito access token required", headers={"WWW-Authenticate": "Bearer"})
    claims = verify_token(credentials.credentials)
    binding = service.store.read("IDENTITIES", claims["sub"])
    if not binding:
        raise HTTPException(403, "Identity is not assigned to this school")
    return Actor.model_validate(binding)
