import json

from .auth import runtime_client, settings

MODEL = "amazon.nova-lite-v1:0"


def parse_json(text):
    text = text.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    return json.loads(text)


class NovaProvider:
    def generate(self, system, supplied, max_tokens=700):
        payload = json.dumps(supplied, sort_keys=True, separators=(",", ":"))
        if len(payload.encode()) > 14_000 or max_tokens > 700:
            raise ValueError("Model request exceeds budget")
        result = runtime_client(settings(), "bedrock-runtime").converse(
            modelId=MODEL, system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": payload}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0})
        usage = {k: int(v) for k, v in result.get("usage", {}).items() if k in ("inputTokens", "outputTokens", "totalTokens")}
        if result.get("stopReason") != "end_turn":
            return None, usage
        text = "".join(c.get("text", "") for c in result["output"]["message"]["content"])
        if len(text) > 12_000:
            return None, usage
        try:
            return parse_json(text), usage
        except ValueError:
            return None, usage
