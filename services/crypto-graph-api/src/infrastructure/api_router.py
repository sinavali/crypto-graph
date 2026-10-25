"""
FastAPI HTTP router for crypto-graph API backend service.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from ..application.use_cases import CryptoGraphUseCases
from .rpc_rotator import ResilientRpcRotator
from .sqlite_storage import SqliteGraphStorage


class AddressLookupRequest(BaseModel):
    address: str
    chain: Optional[str] = None


router = APIRouter(prefix="/api/v1")

# Default service dependencies
storage = SqliteGraphStorage()
rpc = ResilientRpcRotator(offline_mode=False)
use_cases = CryptoGraphUseCases(rpc_provider=rpc, storage=storage)


@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "crypto-graph-api"}


@router.post("/address/lookup")
async def lookup_address(request: AddressLookupRequest) -> Dict[str, Any]:
    try:
        return await use_cases.lookup_address(request.address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/address/{address}/graph")
async def get_address_graph(address: str) -> Dict[str, Any]:
    try:
        return await use_cases.get_graph_topology(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/address/{address}/persona")
async def get_address_persona(address: str) -> Dict[str, Any]:
    try:
        return await use_cases.get_persona_profile(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/address/{address}/cross-chain")
async def get_address_cross_chain(address: str) -> List[Dict[str, Any]]:
    try:
        return await use_cases.get_cross_chain_flows(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
