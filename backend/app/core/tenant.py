"""Multi-tenant site scoping and data clearance models.

Enforces zero-leakage plant boundaries across vector searches (Qdrant) and
knowledge graph queries (Neo4j). In heavy industry, operational SOPs, HAZOP
reviews, and RCA findings for Plant A must never be visible to unauthorized
personnel or cross-plant tenants.
"""
from enum import Enum
from typing import Sequence
from fastapi import Request
from pydantic import BaseModel, Field


class ClearanceLevel(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"


CLEARANCE_ORDER = {
    ClearanceLevel.PUBLIC: 0,
    ClearanceLevel.INTERNAL: 1,
    ClearanceLevel.RESTRICTED: 2,
    ClearanceLevel.CONFIDENTIAL: 3,
}


class SiteContext(BaseModel):
    """Encapsulates the tenant, site, user identity, and clearance level
    for an authenticated request."""
    user_id: str = "local-operator"
    site_id: str = "plant-mumbai-01"
    organization_id: str = "aurag-industrial"
    roles: list[str] = Field(default_factory=lambda: ["PlantOperator"])
    clearance_level: ClearanceLevel = ClearanceLevel.INTERNAL
    email: str | None = None
    name: str | None = None

    def can_access_classification(self, classification: str | ClearanceLevel) -> bool:
        """Verify whether the caller's clearance satisfies the document or node classification."""
        try:
            target_level = ClearanceLevel(classification.upper() if isinstance(classification, str) else classification)
        except ValueError:
            target_level = ClearanceLevel.CONFIDENTIAL  # Fail-closed for unknown classification
        
        user_rank = CLEARANCE_ORDER.get(self.clearance_level, 0)
        target_rank = CLEARANCE_ORDER.get(target_level, 3)
        return user_rank >= target_rank

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)

    def to_filter_dict(self) -> dict:
        """Returns structured metadata filters suitable for Qdrant payload filters
        and Neo4j WHERE clauses."""
        return {
            "site_id": self.site_id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "clearance_level": self.clearance_level.value,
        }


def get_site_context(request: Request) -> SiteContext:
    """FastAPI dependency to extract SiteContext from the request state or headers."""
    if hasattr(request.state, "site_context") and isinstance(request.state.site_context, SiteContext):
        return request.state.site_context

    # Dev/fallback behavior: check header overrides or use defaults
    site_id = request.headers.get("X-Site-ID", "plant-mumbai-01")
    user_id = request.headers.get("X-User-ID", "local-operator")
    org_id = request.headers.get("X-Organization-ID", "aurag-industrial")

    ctx = SiteContext(
        user_id=user_id,
        site_id=site_id,
        organization_id=org_id,
        roles=["PlantOperator"],
        clearance_level=ClearanceLevel.INTERNAL,
    )
    request.state.site_context = ctx
    return ctx
