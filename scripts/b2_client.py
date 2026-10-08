"""Private interactive local demonstration. No passwords/tokens printed or saved."""
import argparse
from getpass import getpass

import boto3
import httpx

from backend.app.auth import AWS_CONFIG, REGION, settings
from scripts.aws_b2 import TAGS, USERS


def run(action, username, url):
    config = settings()
    client = boto3.Session(profile_name="airwise", region_name=REGION).client("cognito-idp", config=AWS_CONFIG)
    if action == "set-password":
        pool = client.describe_user_pool(UserPoolId=config["pool_id"])["UserPool"]
        if pool.get("UserPoolTags") != TAGS:
            raise RuntimeError("Unexpected user pool ownership")
        password = getpass("New synthetic-user password (16+ chars, upper/lower/number/symbol): ")
        if password != getpass("Confirm password: "):
            raise RuntimeError("Passwords differ")
        client.admin_set_user_password(UserPoolId=config["pool_id"], Username=username, Password=password, Permanent=True)
        print("Password set privately.")
        return
    password = getpass(f"Cognito password for {username}: ")
    token = client.initiate_auth(ClientId=config["client_id"], AuthFlow="USER_PASSWORD_AUTH",
                                AuthParameters={"USERNAME": username, "PASSWORD": password})["AuthenticationResult"]["AccessToken"]
    del password
    with httpx.Client(base_url=url, headers={"Authorization": "Bearer " + token}, timeout=45) as api:
        def call(method, path, body=None):
            response = api.request(method, path, json=body)
            if response.status_code != 200:
                raise RuntimeError(f"API status {response.status_code}; response body withheld")
            return response.json()
        if username == "synthetic-admin":
            result = api.get("/inputs")
            if result.status_code == 409:
                fixture = call("GET", "/repair-fixture")
                confirmed = call("POST", "/inputs", {"expected_revision": None, "input": fixture})
            elif result.status_code == 200:
                confirmed = result.json()
            else:
                raise RuntimeError("Cannot inspect input")
            draft = call("POST", "/draft-plans", confirmed["input"])
            approved = call("POST", f"/draft-plans/{draft['id']}/approve")
            print(f"Administrator approved version {approved['plan_version']}")
        else:
            teacher_id = next(t for u, _, t in USERS if u == username)
            assignments = call("GET", f"/teachers/{teacher_id}/assignments")
            if assignments["needs_review"]:
                raise RuntimeError("Current plan needs administrator review")
            version = assignments["plan_version"]
            call("POST", f"/approved-plans/{version}/acknowledgements")
            activity = next(a for a in assignments["assignments"] if a["placement"]["period_id"] == "Mon-2")
            call("PUT", f"/approved-plans/{version}/activities/{activity['activity_id']}/report",
                 {"status": "COMPLETED", "note": "Synthetic demonstration implemented"})
            print(f"Teacher acknowledged {version}; separately reported COMPLETED for {activity['activity_id']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["set-password", "demo"])
    parser.add_argument("--username", choices=[u for u, _, _ in USERS], required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8002")
    args = parser.parse_args()
    if args.url not in ("http://127.0.0.1:8002", "http://localhost:8002"):
        parser.error("Only the loopback B2 server is permitted")
    try:
        run(args.action, args.username, args.url)
    except Exception as error:
        print(f"Private demo stopped: {type(error).__name__}; no secret output")
        raise SystemExit(1)
