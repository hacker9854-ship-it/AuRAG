"""Enterprise Authentication and Role-Based Access Control (RBAC).

Implements Microsoft Entra ID (OIDC) JWT validation with cached JWKS public
keys, industrial app roles, and multi-tenant site context propagation.

Industrial App Roles:
- PlantOperator: Read telemetry, view active work orders, query operational SOPs.
- MaintenancePlanner: Create, update, and schedule maintenance work orders.
- ReliabilityEngineer: Deep Root Cause Analysis (RCA), failure-chain graph traversal.
- ComplianceOfficer: Audit regulatory compliance packs (Factories Act, OISD, ISO).
- KnowledgeAdmin: Document ingestion, P&ID entity extraction review, re-indexing.
- AutomationAdmin: Configure automation triggers and policy bounds.
- Auditor: Read-only access to tamper-evident audit ledgers.
"""
import os
import time
from enum import Enum
from typing import Any, Callable

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from backend.app.core.tenant import ClearanceLevel, SiteContext


class AppRole(str, Enum):
    PlantOperator = "PlantOperator"
    MaintenancePlanner = "MaintenancePlanner"
    ReliabilityEngineer = "ReliabilityEngineer"
    ComplianceOfficer = "ComplianceOfficer"
    KnowledgeAdmin = "KnowledgeAdmin"
    AutomationAdmin = "AutomationAdmin"
    Auditor = "Auditor"


ALL_ROLES = {role.value for role in AppRole}


class UserProfile(BaseModel):
    user_id: str
    email: str | None = None
    name: str | None = None
    roles: list[str] = Field(default_factory=list)
    site_id: str = "plant-mumbai-01"
    organization_id: str = "aurag-industrial"
    clearance_level: ClearanceLevel = ClearanceLevel.INTERNAL

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)

    def to_site_context(self) -> SiteContext:
        return SiteContext(
            user_id=self.user_id,
            site_id=self.site_id,
            organization_id=self.organization_id,
            roles=self.roles,
            clearance_level=self.clearance_level,
            email=self.email,
            name=self.name,
        )


# Global JWKS cache: { "keys": [...], "expires_at": timestamp }
_JWKS_CACHE: dict[str, Any] = {}
_JWKS_CACHE_TTL_SECONDS = 86400  # 24 hours


def _get_env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


def is_auth_enabled() -> bool:
    return _get_env_bool("AUTH_ENABLED", default=False)


def get_tenant_id() -> str:
    return os.environ.get("ENTRA_TENANT_ID", "common")


def get_client_id() -> str:
    return os.environ.get("ENTRA_CLIENT_ID", "")


def get_jwks_uri() -> str:
    custom = os.environ.get("ENTRA_JWKS_URI")
    if custom:
        return custom
    tenant_id = get_tenant_id()
    return f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"


def fetch_jwks() -> dict:
    """Fetch and cache Microsoft Entra ID public key set."""
    now = time.time()
    if _JWKS_CACHE and _JWKS_CACHE.get("expires_at", 0) > now:
        return _JWKS_CACHE["data"]

    jwks_uri = get_jwks_uri()
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(jwks_uri)
            resp.raise_for_status()
            data = resp.json()
            _JWKS_CACHE["data"] = data
            _JWKS_CACHE["expires_at"] = now + _JWKS_CACHE_TTL_SECONDS
            return data
    except Exception as exc:
        # If cache exists even if expired, use as fallback
        if "data" in _JWKS_CACHE:
            return _JWKS_CACHE["data"]
        raise HTTPException(
            status_code=503,
            detail={"error": "identity_provider_unavailable", "detail": f"Failed to retrieve JWKS: {str(exc)}"},
        )


def verify_entra_token(token: str) -> dict:
    """Verify an Entra ID OIDC token against cached JWKS and return claims."""
    # Check for test / mock tokens in test/dev environment
    mock_secret = os.environ.get("TEST_JWT_SECRET")
    if mock_secret:
        try:
            return jwt.decode(
                token,
                mock_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError:
            pass  # Fallback to RS256 JWKS verification

    try:
        unverified_headers = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "detail": f"Malformed token header: {str(exc)}"},
        )

    kid = unverified_headers.get("kid")
    if not kid:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "detail": "Missing 'kid' in token header"},
        )

    jwks = fetch_jwks()
    matching_key = None
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            matching_key = key
            break

    if not matching_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "detail": f"Unknown key identifier (kid: {kid})"},
        )

    try:
        public_key = RSAAlgorithm.from_jwk(matching_key)
        client_id = get_client_id()
        options = {"verify_aud": bool(client_id)}

        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=client_id if client_id else None,
            options=options,
        )
        return claims
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error": "token_expired", "detail": "Bearer token has expired"},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_token", "detail": f"Token verification failed: {str(exc)}"},
        )


def claims_to_user_profile(claims: dict, request: Request | None = None) -> UserProfile:
    """Transform raw OIDC claims into a structured UserProfile."""
    # Subject identity
    user_id = claims.get("oid") or claims.get("sub") or claims.get("upn") or "authenticated-user"
    email = claims.get("email") or claims.get("preferred_username")
    name = claims.get("name")

    # Roles: Entra ID places App Roles in the 'roles' array claim
    raw_roles = claims.get("roles", [])
    if isinstance(raw_roles, str):
        roles = [r.strip() for r in raw_roles.split(",") if r.strip()]
    else:
        roles = list(raw_roles)

    # If no explicit enterprise roles, default to basic PlantOperator
    if not roles:
        roles = [AppRole.PlantOperator.value]

    # Tenancy & Site attributes
    site_id = claims.get("site_id")
    if not site_id and request:
        site_id = request.headers.get("X-Site-ID")
    site_id = site_id or "plant-mumbai-01"

    org_id = claims.get("organization_id")
    if not org_id and request:
        org_id = request.headers.get("X-Organization-ID")
    org_id = org_id or "aurag-industrial"

    raw_clearance = claims.get("clearance_level", "INTERNAL").upper()
    try:
        clearance = ClearanceLevel(raw_clearance)
    except ValueError:
        clearance = ClearanceLevel.INTERNAL

    return UserProfile(
        user_id=user_id,
        email=email,
        name=name,
        roles=roles,
        site_id=site_id,
        organization_id=org_id,
        clearance_level=clearance,
    )


def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
) -> UserProfile:
    """FastAPI dependency to extract and verify the current authenticated caller.
    
    If AUTH_ENABLED is False and no Authorization header is provided, returns
    a default development identity for seamless local testing.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        claims = verify_entra_token(token)
        user = claims_to_user_profile(claims, request=request)
    elif is_auth_enabled():
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "detail": "Missing or invalid Authorization Bearer header"},
        )
    else:
        # Dev / local mode fallback identity
        dev_user_id = request.headers.get("X-User-ID", "local-operator")
        dev_site_id = request.headers.get("X-Site-ID", "plant-mumbai-01")
        dev_roles = [r.strip() for r in request.headers.get("X-User-Roles", "PlantOperator").split(",") if r.strip()]
        user = UserProfile(
            user_id=dev_user_id,
            email=f"{dev_user_id}@plant.internal",
            name="Plant Local Operator",
            roles=dev_roles,
            site_id=dev_site_id,
            organization_id="aurag-industrial",
            clearance_level=ClearanceLevel.INTERNAL,
        )

    # Store in request state for downstream handlers
    request.state.current_user = user
    request.state.site_context = user.to_site_context()
    return user


def require_roles(*allowed_roles: str | AppRole) -> Callable[[UserProfile], UserProfile]:
    """Dependency factory ensuring the authenticated user has at least one of the allowed roles."""
    expected = {r.value if isinstance(r, AppRole) else str(r) for r in allowed_roles}

    def role_checker(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        user_roles = set(current_user.roles)
        if not user_roles.intersection(expected):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "detail": f"Access denied. User '{current_user.user_id}' lacks required role from {sorted(list(expected))}",
                },
            )
        return current_user

    return role_checker
