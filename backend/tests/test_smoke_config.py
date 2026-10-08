import pytest
import base64
import hashlib

from scripts.aws_smoke import upload_inspected_zip, validate_plan


def plan():
    return {"profile": "airwise", "region": "ap-southeast-2", "runtime": "python3.12",
            "architecture": "x86_64", "memory_mb": 1024, "timeout_seconds": 30,
            "bucket": "airwise-smoke-artifacts-a1f7411817", "role": "airwise-smoke-role-a1f7411817",
            "function": "airwise-runtime-smoke-a1f7411817", "key": "runtime-smoke.zip",
            "log_group": "/aws/lambda/airwise-runtime-smoke-a1f7411817", "uncompressed_bytes": 190107573}


def test_authorized_config():
    validate_plan(plan())


@pytest.mark.parametrize("key,value", [("region", "us-east-1"), ("architecture", "arm64"),
                                      ("bucket", "unrelated-bucket"), ("uncompressed_bytes", 262144001)])
def test_reject_config_drift_before_cloud_calls(key, value):
    config = plan()
    config[key] = value
    with pytest.raises(ValueError):
        validate_plan(config)


def test_upload_preserves_bytes_and_supplies_part_checksums(tmp_path):
    content = b"x" * (5 * 1024 * 1024) + b"final"
    archive = tmp_path / "archive.zip"
    archive.write_bytes(content)
    received = []

    class Client:
        def create_multipart_upload(self, **kwargs):
            return {"UploadId": "owned-upload"}

        def upload_part(self, **kwargs):
            assert kwargs["UploadId"] == "owned-upload"
            assert kwargs["ContentLength"] == len(kwargs["Body"])
            assert kwargs["ChecksumSHA256"] == base64.b64encode(hashlib.sha256(kwargs["Body"]).digest()).decode()
            received.append(kwargs["Body"])
            return {"ETag": str(kwargs["PartNumber"])}

        def complete_multipart_upload(self, **kwargs):
            assert len(kwargs["MultipartUpload"]["Parts"]) == 2

    upload_inspected_zip(Client(), archive, {**plan(), "sha256": hashlib.sha256(content).hexdigest()})
    assert b"".join(received) == content


def test_failed_upload_cancels_only_its_own_incomplete_transfer(tmp_path):
    archive = tmp_path / "archive.zip"
    archive.write_bytes(b"fixture")
    cancelled = []

    class Client:
        def create_multipart_upload(self, **kwargs):
            return {"UploadId": "owned-upload"}

        def upload_part(self, **kwargs):
            raise RuntimeError("network failure")

        def abort_multipart_upload(self, **kwargs):
            cancelled.append(kwargs["UploadId"])

    with pytest.raises(RuntimeError, match="network failure"):
        upload_inspected_zip(Client(), archive, {**plan(), "sha256": "fixture"})
    assert cancelled == ["owned-upload"]
