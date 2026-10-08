import hashlib
import json
from pathlib import Path

from .evidence_contracts import PolicyExcerpt


def catalog():
    records = json.loads(Path(__file__).with_name("data").joinpath("policy_excerpts.json").read_text())
    for record in records:
        record["excerpt_sha256"] = hashlib.sha256(record["excerpt"].encode()).hexdigest()
        if record["document_sha256"] == "internal":
            record["document_sha256"] = record["excerpt_sha256"]
    return [PolicyExcerpt.model_validate(r) for r in records]
