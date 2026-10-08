"""One bounded in-region request, with no notices, credentials or response logging."""
import json
import re
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

MODEL = "amazon.nova-lite-v1:0"
REGION = "ap-southeast-2"


def probe():
    session = boto3.Session(profile_name="airwise", region_name=REGION)
    config = Config(connect_timeout=5, read_timeout=20, retries={"total_max_attempts": 1})
    availability = session.client("bedrock", config=config).get_foundation_model_availability(modelId=MODEL)
    print(json.dumps({k: availability.get(k) for k in ("authorizationStatus", "regionAvailability", "entitlementAvailability")}), flush=True)
    result = session.client("bedrock-runtime", config=config).converse(
        modelId=MODEL, messages=[{"role": "user", "content": [{"text": 'Return only {"ok":true} as JSON.'}]}],
        inferenceConfig={"maxTokens": 32, "temperature": 0})
    body = "".join(c.get("text", "") for c in result["output"]["message"]["content"])
    if body.strip().startswith("```json") and body.strip().endswith("```"):
        body = body.strip()[7:-3].strip()
    record = {"model": MODEL, "region": REGION, "stop_reason": result["stopReason"], "usage": result["usage"]}
    try:
        record["valid_json"] = json.loads(body) == {"ok": True}
    except ValueError:
        record["valid_json"] = False
    Path("work/bedrock-probe.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record))
    assert record["valid_json"] and result["stopReason"] == "end_turn"


if __name__ == "__main__":
    try:
        probe()
    except ClientError as error:
        print(json.dumps({"error": error.response["Error"]["Code"], "region": REGION, "model": MODEL,
                          "message": re.sub(r"\b\d{12}\b", "[REDACTED]", error.response["Error"]["Message"])}))
        raise SystemExit(1)
    except BotoCoreError as error:
        print(type(error).__name__)
        raise SystemExit(1)
