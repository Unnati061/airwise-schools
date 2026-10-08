import pytest

from scripts.aws_smoke import validate_plan


def plan():
    return {"profile": "airwise", "region": "us-east-1", "runtime": "python3.12",
            "architecture": "x86_64", "memory_mb": 1024, "timeout_seconds": 30,
            "bucket": "airwise-smoke-artifacts-a1f7411817", "role": "airwise-smoke-role-a1f7411817",
            "function": "airwise-runtime-smoke-a1f7411817", "key": "runtime-smoke.zip",
            "log_group": "/aws/lambda/airwise-runtime-smoke-a1f7411817", "uncompressed_bytes": 190107573}


def test_authorized_config():
    validate_plan(plan())


@pytest.mark.parametrize("key,value", [("region", "eu-west-1"), ("architecture", "arm64"),
                                      ("bucket", "unrelated-bucket"), ("uncompressed_bytes", 262144001)])
def test_reject_config_drift_before_cloud_calls(key, value):
    config = plan()
    config[key] = value
    with pytest.raises(ValueError):
        validate_plan(config)
