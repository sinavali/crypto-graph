"""
Admin Configuration and Persona Management Router.
Strictly protected by Admin Role RBAC.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
import httpx
from pydantic import BaseModel

from libs.blockchain_contracts.auth_models import SessionToken, Tenant, UserRole
from libs.blockchain_contracts.config_models import ConfigCategory
from libs.blockchain_contracts.models import (
    AttributionEvidence,
    ChainEcosystem,
    ClusteredWallet,
    ClusteringHeuristicType,
    PersonaProfile,
)
from .auth_router import require_admin
from ..domain.config_service import ConfigService


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class UpdateConfigBatchRequest(BaseModel):
    configs: Dict[str, str]


class RpcTestRequest(BaseModel):
    url: str
    timeout_seconds: float = 3.0


class UpdatePersonaRequest(BaseModel):
    label: Optional[str] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None


class LinkWalletRequest(BaseModel):
    address: str
    chain: str
    reason: str
    confidence_weight: float = 0.95


class CreateTenantRequest(BaseModel):
    name: str


class CreatePersonaRequest(BaseModel):
    primary_address: str
    label: str
    tags: Optional[List[str]] = None
    summary: Optional[str] = None


class UnlinkWalletRequest(BaseModel):
    address: str


class UpdateUserRoleRequest(BaseModel):
    role: str


class CreateUserRequest(BaseModel):
    tenant_id: Optional[str] = None
    username: str
    password: str
    role: str = "member"


def get_config_service(request: Request) -> ConfigService:
    return request.app.state.config_service


def get_storage(request: Request):
    return request.app.state.storage


# --- System Configurations ---
@router.get("/configs")
async def get_all_configs(
    admin: SessionToken = Depends(require_admin),
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """Returns all system configurations grouped by category."""
    raw_grouped = config_service.get_all_by_category()
    result = {}
    for cat, items in raw_grouped.items():
        result[cat] = [item.model_dump(mode="json") for item in items]
    return result


@router.post("/configs")
async def update_configs(
    req: UpdateConfigBatchRequest,
    admin: SessionToken = Depends(require_admin),
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, str]:
    """Batch updates configuration values with immediate runtime effect."""
    for key, value in req.configs.items():
        config_service.set(key, value)
    return {"status": "success", "message": f"Updated {len(req.configs)} configuration(s)."}


@router.post("/rpc/test")
async def test_rpc_endpoint(
    req: RpcTestRequest,
    admin: SessionToken = Depends(require_admin),
) -> Dict[str, Any]:
    """Probes an RPC node and measures real-world response latency."""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=req.timeout_seconds) as client:
            resp = await client.post(
                req.url,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
            )
            elapsed_ms = round((time.time() - start) * 1000, 2)
            return {
                "url": req.url,
                "status": "online" if resp.status_code == 200 else "degraded",
                "http_status": resp.status_code,
                "latency_ms": elapsed_ms,
            }
    except Exception as e:
        elapsed_ms = round((time.time() - start) * 1000, 2)
        return {
            "url": req.url,
            "status": "offline",
            "error": str(e),
            "latency_ms": elapsed_ms,
        }


# --- Persona Profiles Management ---
@router.get("/personas")
async def list_personas(
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> List[Dict[str, Any]]:
    """Returns all discovered and custom persona profiles."""
    profiles = storage.get_all_personas()
    return [p.model_dump(mode="json") for p in profiles]


@router.post("/personas/{persona_id}")
async def update_persona(
    persona_id: str,
    req: UpdatePersonaRequest,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    """Updates label, tags, or notes of a persona profile."""
    persona = storage.get_persona_profile(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona profile not found.")

    if req.label is not None:
        persona.label = req.label
    if req.tags is not None:
        persona.tags = req.tags
    if req.summary is not None:
        persona.summary = req.summary

    storage.save_persona_profile(persona)
    return persona.model_dump(mode="json")


@router.post("/personas/{persona_id}/link")
async def link_wallet_to_persona(
    persona_id: str,
    req: LinkWalletRequest,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    """Manually links an address to an existing persona with attribution evidence."""
    persona = storage.get_persona_profile(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona profile not found.")

    norm_addr = req.address.lower()
    evidence = AttributionEvidence(
        heuristic=ClusteringHeuristicType.CO_FUNDING_TEMPORAL,
        description=f"Manual Admin Attribution: {req.reason}",
        confidence_weight=req.confidence_weight,
        timestamp_utc=datetime.now(timezone.utc),
    )

    # Check if wallet already in cluster
    existing = next((w for w in persona.clustered_wallets if w.address == norm_addr), None)
    if existing:
        existing.evidences.append(evidence)
    else:
        try:
            chain_eco = ChainEcosystem(req.chain.lower())
        except ValueError:
            chain_eco = ChainEcosystem.ETHEREUM

        now = datetime.now(timezone.utc)
        persona.clustered_wallets.append(
            ClusteredWallet(
                address=norm_addr,
                chain=chain_eco,
                first_seen_utc=now,
                last_seen_utc=now,
                evidences=[evidence],
            )
        )

    # Recalculate persona confidence
    all_evs = [ev for w in persona.clustered_wallets for ev in w.evidences]
    p_false = 1.0
    for ev in all_evs:
        p_false *= (1.0 - ev.confidence_weight)
    persona.confidence_score = round(min(1.0, max(0.0, 1.0 - p_false)), 4)

    storage.save_persona_profile(persona)
    return persona.model_dump(mode="json")


@router.post("/personas")
async def create_custom_persona(
    req: CreatePersonaRequest,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    norm_addr = req.primary_address.lower()
    now = datetime.now(timezone.utc)
    persona_id = f"persona-custom-{abs(hash(norm_addr)):08x}"
    wallet = ClusteredWallet(
        address=norm_addr,
        chain=ChainEcosystem.ETHEREUM if norm_addr.startswith("0x") else ChainEcosystem.BITCOIN,
        first_seen_utc=now,
        last_seen_utc=now,
        evidences=[],
    )
    persona = PersonaProfile(
        persona_id=persona_id,
        label=req.label or f"Custom Persona {persona_id[:8]}",
        primary_address=norm_addr,
        clustered_wallets=[wallet],
        confidence_score=1.0,
        tags=req.tags or ["custom-attributed"],
        summary=req.summary or f"Manually initialized persona profile for {norm_addr[:10]}...",
    )
    storage.save_persona_profile(persona)
    return persona.model_dump(mode="json")


@router.post("/personas/{persona_id}/unlink")
async def unlink_wallet_from_persona(
    persona_id: str,
    req: UnlinkWalletRequest,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    persona = storage.get_persona_profile(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona profile not found.")
    norm_addr = req.address.lower()
    if norm_addr == persona.primary_address.lower():
        raise HTTPException(status_code=400, detail="Cannot unlink primary address of persona.")

    persona.clustered_wallets = [w for w in persona.clustered_wallets if w.address.lower() != norm_addr]

    # Recalculate persona confidence
    all_evs = [ev for w in persona.clustered_wallets for ev in w.evidences]
    if all_evs:
        p_false = 1.0
        for ev in all_evs:
            p_false *= (1.0 - ev.confidence_weight)
        persona.confidence_score = round(min(1.0, max(0.0, 1.0 - p_false)), 4)
    else:
        persona.confidence_score = 0.50

    storage.save_persona_profile(persona)
    return persona.model_dump(mode="json")


@router.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: str,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, str]:
    persona = storage.get_persona_profile(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona profile not found.")
    storage.delete_persona_profile(persona_id)
    return {"status": "success", "message": f"Persona {persona_id} deleted."}


# --- Multi-Tenant & User Administration ---
@router.get("/tenants")
async def list_tenants(
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    tenants = storage.get_all_tenants()
    users = storage.get_all_users()
    return {
        "tenants": [t.model_dump(mode="json") for t in tenants],
        "users": [
            {
                "user_id": u.user_id,
                "tenant_id": u.tenant_id,
                "username": u.username,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at_utc": u.created_at_utc.isoformat(),
            }
            for u in users
        ],
    }


@router.post("/tenants")
async def create_tenant(
    req: CreateTenantRequest,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    tenant_id = f"tenant-{abs(hash(req.name)):08x}"
    tenant = Tenant(tenant_id=tenant_id, name=req.name)
    storage.create_tenant(tenant)
    return tenant.model_dump(mode="json")


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    users = storage.get_all_users()
    target_user = next((u for u in users if u.user_id == user_id), None)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    new_status = not target_user.is_active
    storage.update_user_status(user_id, new_status)
    return {"user_id": user_id, "is_active": new_status}


@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    req: UpdateUserRoleRequest,
    admin: SessionToken = Depends(require_admin),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    users = storage.get_all_users()
    target_user = next((u for u in users if u.user_id == user_id), None)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    try:
        role_enum = UserRole(req.role.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role '{req.role}'. Must be 'admin' or 'member'.")
    storage.update_user_role(user_id, role_enum)
    return {"user_id": user_id, "role": role_enum.value}


@router.post("/users")
async def admin_create_user(
    req: CreateUserRequest,
    request: Request,
    admin: SessionToken = Depends(require_admin),
) -> Dict[str, Any]:
    auth_service = request.app.state.auth_service
    storage = request.app.state.storage
    try:
        role_enum = UserRole(req.role.lower()) if req.role else UserRole.MEMBER
        user = auth_service.register_user(
            username=req.username,
            password=req.password,
            role=role_enum,
        )
        if req.tenant_id:
            with storage._get_connection() as conn:
                conn.execute("UPDATE users SET tenant_id = ? WHERE user_id = ?", (req.tenant_id, user.user_id))
            user.tenant_id = req.tenant_id
        return {
            "status": "success",
            "user_id": user.user_id,
            "username": user.username,
            "tenant_id": user.tenant_id,
            "role": user.role.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
