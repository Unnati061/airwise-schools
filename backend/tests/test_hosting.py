import json
from unittest.mock import Mock

import pytest
from botocore.exceptions import ReadTimeoutError

from scripts import amplify_host


def test_partial_manifest_preserved_without_aws_calls(tmp_path, monkeypatch):
    manifest = tmp_path / 'hosting.json'
    original = {'created': ['amplify_app'], 'app_id': 'existing'}
    manifest.write_text(json.dumps(original))
    monkeypatch.setattr(amplify_host, 'MANIFEST', manifest)
    session = Mock()
    monkeypatch.setattr(amplify_host.boto3, 'Session', session)
    with pytest.raises(SystemExit):
        amplify_host.deploy()
    assert json.loads(manifest.read_text()) == original
    session.assert_not_called()


def test_timeout_records_stage_and_host_not_secret_url(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / 'hosting.json'
    monkeypatch.setattr(amplify_host, 'MANIFEST', manifest)
    session = Mock()
    session.client.return_value.get_caller_identity.side_effect = ReadTimeoutError(
        endpoint_url='https://sts.ap-southeast-2.amazonaws.com/?token=DO_NOT_RECORD')
    monkeypatch.setattr(amplify_host.boto3, 'Session', Mock(return_value=session))
    with pytest.raises(SystemExit):
        amplify_host.deploy()
    result = json.loads(manifest.read_text())
    assert result['failure_step'] == 'authentication'
    assert result['endpoint_host'] == 'sts.ap-southeast-2.amazonaws.com'
    assert result['created'] == []
    assert 'DO_NOT_RECORD' not in manifest.read_text() + capsys.readouterr().out
