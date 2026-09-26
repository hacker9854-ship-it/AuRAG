"""Unit tests for enterprise authentication, RBAC, and multi-tenant site scoping."""
import time
from unittest.mock import MagicMock
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt
from jwt.algorithms import RSAAlgorithm
import pytest
from fastapi import HTTPException

from backend.app.core.auth import (
    AppRole,
    UserProfile,
    claims_to_user_profile,
    get_current_user,
    require_roles,
    verify_entra_token,
)
from backend.app.core.tenant import ClearanceLevel, SiteContext, get_site_context


def test_site_context_clearance_hierarchy():
    ctx = SiteContext(clearance_level=ClearanceLevel.RESTRICTED)
    assert ctx.can_access_classification(ClearanceLevel.PUBLIC) is True
    assert ctx.can_access_classification(ClearanceLevel.INTERNAL) is True
    assert ctx.can_access_classification(ClearanceLevel.RESTRICTED) is True
    assert ctx.can_access_classification(ClearanceLevel.CONFIDENTIAL) is False

    # String case-insensitivity
    assert ctx.can_access_classification("internal") is True
    assert ctx.can_access_classification("confidential") is False

    # Unknown classification fails closed
    assert ctx.can_access_classification("UNKNOWN_TOP_SECRET") is False


def test_site_context_role_checks():
    ctx = SiteContext(roles=["PlantOperator", "ReliabilityEngineer"])
    assert ctx.has_role("PlantOperator") is True
    assert ctx.has_role("ComplianceOfficer") is False
    assert ctx.has_any_role("ComplianceOfficer", "PlantOperator") is True
    assert ctx.has_any_role("ComplianceOfficer", "KnowledgeAdmin") is False


def test_dev_mode_returns_default_identity():
    request = MagicMock()
    request.headers = {}
    request.state = MagicMock()

    user = get_current_user(request=request, authorization=None)
    assert user.user_id == "local-operator"
    assert "PlantOperator" in user.roles
    assert user.site_id == "plant-mumbai-01"


def test_dev_mode_honors_header_overrides():
    request = MagicMock()
    request.headers = {
        "X-User-ID": "eng-rahul",
        "X-Site-ID": "plant-jamnagar-02",
        "X-User-Roles": "ReliabilityEngineer,AutomationAdmin",
    }
    request.state = MagicMock()

    user = get_current_user(request=request, authorization=None)
    assert user.user_id == "eng-rahul"
    assert user.site_id == "plant-jamnagar-02"
    assert "ReliabilityEngineer" in user.roles
    assert "AutomationAdmin" in user.roles


def test_auth_enabled_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    request = MagicMock()
    request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request=request, authorization=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"] == "unauthorized"


def test_token_verification_with_test_jwt(monkeypatch):
    secret = "aurag-test-secret-32-chars-long!!"
    monkeypatch.setenv("TEST_JWT_SECRET", secret)

    payload = {
        "sub": "usr-12345",
        "email": "planner@plant.example.com",
        "name": "Jane Planner",
        "roles": ["MaintenancePlanner"],
        "site_id": "plant-mumbai-01",
        "organization_id": "aurag-corp",
        "clearance_level": "RESTRICTED",
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    claims = verify_entra_token(token)
    assert claims["sub"] == "usr-12345"
    assert claims["roles"] == ["MaintenancePlanner"]

    user = claims_to_user_profile(claims)
    assert user.user_id == "usr-12345"
    assert user.email == "planner@plant.example.com"
    assert user.has_role("MaintenancePlanner")
    assert user.site_id == "plant-mumbai-01"
    assert user.clearance_level == ClearanceLevel.RESTRICTED


def test_require_roles_dependency():
    user = UserProfile(
        user_id="op-1",
        roles=["PlantOperator"],
    )

    # Allowed role
    checker = require_roles(AppRole.PlantOperator)
    assert checker(current_user=user) is user

    # Disallowed role raises 403 Forbidden
    checker_admin = require_roles(AppRole.AutomationAdmin, AppRole.KnowledgeAdmin)
    with pytest.raises(HTTPException) as exc_info:
        checker_admin(current_user=user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error"] == "forbidden"


def test_rs256_entra_jwks_verification(monkeypatch):
    # Generate an ephemeral RSA key pair for testing RS256 JWKS validation
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    jwk_dict = RSAAlgorithm.to_jwk(public_key, as_dict=True)
    jwk_dict["kid"] = "test-key-id-1"

    monkeypatch.setattr(
        "backend.app.core.auth.fetch_jwks",
        lambda: {"keys": [jwk_dict]},
    )
    monkeypatch.setenv("ENTRA_CLIENT_ID", "aurag-api-client-id")
    # Ensure test secret isn't interfering with RS256
    monkeypatch.delenv("TEST_JWT_SECRET", raising=False)

    now = int(time.time())
    payload = {
        "sub": "entra-user-999",
        "email": "chief.engineer@plant.com",
        "roles": ["ReliabilityEngineer"],
        "site_id": "plant-mumbai-01",
        "aud": "aurag-api-client-id",
        "exp": now + 3600,
        "nbf": now - 60,
    }
    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key-id-1"},
    )

    claims = verify_entra_token(token)
    assert claims["sub"] == "entra-user-999"
    assert claims["roles"] == ["ReliabilityEngineer"]

    # Test expired token rejection
    expired_payload = dict(payload, exp=now - 100)
    expired_token = jwt.encode(
        expired_payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key-id-1"},
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_entra_token(expired_token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["error"] == "token_expired"


def test_security_headers_middleware():
    from starlette.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers


def test_chat_http_endpoint_auth_enforcement(monkeypatch):
    from starlette.testclient import TestClient
    from backend.app.main import app
    from backend.app.api import chat
    from backend.app.core.neo4j import get_session

    app.dependency_overrides[get_session] = lambda: MagicMock()

    try:
        monkeypatch.setenv("AUTH_ENABLED", "true")
        secret = "aurag-test-secret-32-chars-long!!"
        monkeypatch.setenv("TEST_JWT_SECRET", secret)

        client = TestClient(app)

        # 1. Missing token -> 401 Unauthorized
        resp_unauth = client.post("/api/chat", json={"query": "Test query"})
        assert resp_unauth.status_code == 401
        assert resp_unauth.json()["error"] == "unauthorized"

        # Mock answer_query and memory service for successful chat
        monkeypatch.setattr(
            chat,
            "answer_query",
            lambda _session, query, memory_context=None, session_id=None: {
                "user_query": query,
                "routed_agent": "copilot",
                "agent_response": "Authenticated response.",
                "citations": [],
                "graph_paths": [],
                "retrieved_context": [],
            },
        )

        class DummyMemory:
            def recall(self, *_args):
                return []

            def remember(self, **_kwargs):
                return True

        monkeypatch.setattr(chat, "get_memory_service", lambda: DummyMemory())

        # 2. Valid token -> 200 OK with authenticated site_id and user_id
        payload = {
            "sub": "operator-vikram",
            "roles": ["PlantOperator"],
            "site_id": "plant-mumbai-01",
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        resp_auth = client.post(
            "/api/chat",
            json={"query": "Test query"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_auth.status_code == 200
        data = resp_auth.json()
        assert data["user_id"] == "operator-vikram"
        assert data["site_id"] == "plant-mumbai-01"
        assert data["agent_response"] == "Authenticated response."
    finally:
        app.dependency_overrides.pop(get_session, None)


