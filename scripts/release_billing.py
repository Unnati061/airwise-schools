"""One bounded read-only account billing pass; never prints account/credit IDs."""
import json
from datetime import datetime, timedelta, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

CONFIG = Config(connect_timeout=4, read_timeout=12, retries={"total_max_attempts": 1})


def failure(error):
    return {"status": "UNAVAILABLE", "error_class": type(error).__name__,
            "error_code": error.response["Error"]["Code"] if isinstance(error, ClientError) else None}


def inspect():
    session = boto3.Session(profile_name="airwise", region_name="ap-southeast-2")
    result = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "ACCOUNT, NOT PROJECT"}
    try:
        identity = session.client("sts", config=CONFIG).get_caller_identity()
    except Exception as error:
        result["authentication"] = failure(error)
        print(json.dumps(result)); return
    result["authentication"] = "PASSED; ACCOUNT REDACTED"
    now = datetime.now(timezone.utc)
    try:
        # Billing is a global service; no application region/account is changed.
        response = session.client("billing", config=CONFIG).get_credits(
            accountId=identity["Account"], startDate=now - timedelta(days=364), payerAccountFlag=False)
        result["credits"] = [{k: c.get(k) for k in (
            "creditType", "initialAmount", "remainingAmount", "estimatedAmount", "endDate",
            "creditStatus", "applicableProductNames")} for c in response.get("credits", [])]
    except Exception as error:
        result["credits"] = failure(error)
    try:
        response = session.client("ce", config=CONFIG).get_cost_and_usage(
            TimePeriod={"Start": now.strftime("%Y-%m-01"), "End": now.strftime("%Y-%m-%d")},
            Granularity="MONTHLY", Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "RECORD_TYPE"}])
        result["cost"] = {"through_utc_exclusive": now.strftime("%Y-%m-%d"),
                          "results": response["ResultsByTime"],
                          "truncated": bool(response.get("NextPageToken")),
                          "limitation": "Delayed account-wide cost by charge type, not live gross/project spend or a final bill. No extra pages requested."}
    except Exception as error:
        result["cost"] = failure(error)
    print(json.dumps(result, default=str))


if __name__ == "__main__":
    inspect()
