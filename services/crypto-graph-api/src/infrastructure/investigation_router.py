"""
Multi-Tenant Investigation Router.
Manages tenant-isolated watchlists, saved graph investigations, and search history.
"""

from datetime import datetime, timezone
import json
import secrets
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from libs.blockchain_contracts.auth_models import SessionToken
from libs.blockchain_contracts.config_models import (
    InvestigationRecord,
    SearchHistoryRecord,
    WatchlistItem,
)
from .auth_router import require_auth


router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


class AddWatchlistRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    label: str = ""
    notes: str = ""


class SaveInvestigationRequest(BaseModel):
    title: str
    target_address: str
    graph_data: Dict[str, Any]


class RecordSearchRequest(BaseModel):
    address: str
    chain: str = "ethereum"


def get_storage(request: Request):
    return request.app.state.storage


# --- Watchlist ---
@router.get("/watchlist")
async def get_watchlist(
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> List[Dict[str, Any]]:
    """Returns watchlist strictly scoped to the user's tenant."""
    items = storage.get_watchlist(session.tenant_id)
    return [item.model_dump(mode="json") for item in items]


@router.post("/watchlist")
async def add_to_watchlist(
    req: AddWatchlistRequest,
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    """Adds a wallet address to the tenant's watchlist."""
    item_id = f"watch-{secrets.token_hex(8)}"
    item = WatchlistItem(
        id=item_id,
        tenant_id=session.tenant_id,
        address=req.address.lower(),
        label=req.label or f"Watch {req.address[:8]}...",
        chain=req.chain,
        notes=req.notes,
    )
    storage.add_to_watchlist(item)
    return item.model_dump(mode="json")


@router.delete("/watchlist/{address}")
async def remove_from_watchlist(
    address: str,
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> Dict[str, str]:
    """Removes an address from the tenant's watchlist."""
    storage.remove_from_watchlist(session.tenant_id, address.lower())
    return {"status": "success", "message": f"Removed {address} from watchlist."}


# --- Saved Investigations ---
@router.get("/saved")
async def list_saved_investigations(
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> List[Dict[str, Any]]:
    """Lists all saved investigations for the tenant."""
    records = storage.get_investigations(session.tenant_id)
    return [
        {
            "investigation_id": r.investigation_id,
            "title": r.title,
            "target_address": r.target_address,
            "created_at_utc": r.created_at_utc.isoformat(),
        }
        for r in records
    ]


@router.post("/saved")
async def save_investigation(
    req: SaveInvestigationRequest,
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    """Snapshots the active graph state into a persistent investigation."""
    inv_id = f"inv-{secrets.token_hex(8)}"
    record = InvestigationRecord(
        investigation_id=inv_id,
        tenant_id=session.tenant_id,
        user_id=session.user_id,
        title=req.title or f"Investigation {req.target_address[:10]}",
        target_address=req.target_address.lower(),
        graph_data_json=json.dumps(req.graph_data),
    )
    storage.save_investigation(record)
    return {
        "status": "success",
        "investigation_id": inv_id,
        "title": record.title,
    }


@router.get("/saved/{investigation_id}")
async def load_investigation(
    investigation_id: str,
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> Dict[str, Any]:
    """Loads a saved investigation snapshot."""
    record = storage.get_investigation_by_id(investigation_id)
    if not record or record.tenant_id != session.tenant_id:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return {
        "investigation_id": record.investigation_id,
        "title": record.title,
        "target_address": record.target_address,
        "graph_data": json.loads(record.graph_data_json),
        "created_at_utc": record.created_at_utc.isoformat(),
    }


# --- Search History ---
@router.get("/history")
async def get_search_history(
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> List[Dict[str, Any]]:
    records = storage.get_search_history(session.tenant_id, limit=10)
    return [r.model_dump(mode="json") for r in records]


@router.post("/history")
async def record_search(
    req: RecordSearchRequest,
    session: SessionToken = Depends(require_auth),
    storage = Depends(get_storage),
) -> Dict[str, str]:
    search_id = f"search-{secrets.token_hex(8)}"
    record = SearchHistoryRecord(
        search_id=search_id,
        tenant_id=session.tenant_id,
        user_id=session.user_id,
        address=req.address.lower(),
        chain=req.chain,
    )
    storage.add_search_history(record)
    return {"status": "success"}
