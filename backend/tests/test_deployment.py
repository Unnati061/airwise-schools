import boto3
import pytest
from fastapi.testclient import TestClient

from backend.app import auth, lambda_app


def test_lambda_environment_never_reads_local_profile(monkeypatch):
    monkeypatch.setenv('AIRWISE_RUNTIME', 'lambda')
    monkeypatch.setenv('AWS_REGION', 'ap-southeast-2')
    monkeypatch.setenv('AIRWISE_TABLE', 'airwise-b2-data-a1f7411817')
    monkeypatch.setenv('AIRWISE_POOL_ID', 'ap-southeast-2_test')
    monkeypatch.setenv('AIRWISE_CLIENT_ID', 'test-client')
    auth.settings.cache_clear()
    try:
        config = auth.settings()
        assert 'profile' not in config and 'runtime_role_arn' not in config
        class Session:
            def __init__(self, **kwargs):
                assert kwargs == {'region_name': 'ap-southeast-2'}
            def client(self, name, config):
                assert config.retries['total_max_attempts'] == 1
                return name
        monkeypatch.setattr(boto3, 'Session', Session)
        assert auth.runtime_client(config) == 'dynamodb'
        assert auth.runtime_client(config, 'bedrock-runtime') == 'bedrock-runtime'
    finally:
        auth.settings.cache_clear()


def test_deployed_surface_health_only_public(monkeypatch):
    def denied():
        from fastapi import HTTPException
        raise HTTPException(401, 'Authentication required')
    lambda_app.app.dependency_overrides[auth.identity] = denied
    try:
        with TestClient(lambda_app.app) as client:
            assert client.get('/health').json() == {'status': 'ok'}
            for endpoint in ('/auth/config', '/inputs', '/repair-fixture', '/me'):
                assert client.get(endpoint).status_code == 401
            for endpoint in ('/school', '/docs', '/openapi.json'):
                assert client.get(endpoint).status_code == 404
    finally:
        lambda_app.app.dependency_overrides.clear()


def test_lambda_payload_cap_precedes_adapter(monkeypatch):
    monkeypatch.setattr(lambda_app, 'adapter', lambda *args: pytest.fail('Oversized body reached app'))
    response = lambda_app.handler({'body': 'a' * 250001}, None)
    assert response['statusCode'] == 413


def test_gateway_route_plan_protects_entire_application():
    from scripts.aws_app import route_definitions
    routes = list(route_definitions(lambda_app.app))
    public = [r['RouteKey'] for r in routes if r['AuthorizationType'] == 'NONE']
    assert public == ['GET /health']
    assert all(r['AuthorizationType'] == 'JWT' for r in routes if r['RouteKey'] != 'GET /health')
    keys = {r['RouteKey'] for r in routes}
    assert {'GET /auth/config', 'POST /notice-analyses', 'POST /draft-plans',
            'POST /draft-plans/{plan_id}/approve', 'GET /approved-plans/{version}/review',
            'GET /draft-plans/{plan_id}/explanation'} <= keys
    assert not {'GET /school', 'GET /openapi.json', 'GET /docs'} & keys
