"""
FastAPI Server-Rendered (SSR) Web Frontend for crypto-graph.
Pure Python web layer utilizing Jinja2 templates, HTMX partials, and Cytoscape.js.
Zero Node.js runtime needed.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from libs.blockchain_contracts.fixtures import (
    CLUSTER_WALLET_A,
    SATOSHI_BTC,
    VITALIK_ETH,
)
from services.crypto_graph_api.src.application.use_cases import CryptoGraphUseCases
from services.crypto_graph_api.src.infrastructure.rpc_rotator import ResilientRpcRotator
from services.crypto_graph_api.src.infrastructure.sqlite_storage import SqliteGraphStorage


app = FastAPI(title="crypto-graph Visualizer", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Shared backend use case instance
storage = SqliteGraphStorage()
rpc = ResilientRpcRotator(offline_mode=False)
use_cases = CryptoGraphUseCases(rpc_provider=rpc, storage=storage)


@app.get("/", response_class=HTMLResponse)
async def index_view(request: Request, address: Optional[str] = Query(None)):
    """Primary render-view dashboard."""
    initial_address = address or VITALIK_ETH
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "default_address": initial_address,
            "sample_vitalik": VITALIK_ETH,
            "sample_satoshi": SATOSHI_BTC,
            "sample_cluster": CLUSTER_WALLET_A,
        },
    )


@app.get("/partials/address-summary", response_class=HTMLResponse)
async def address_summary_partial(request: Request, address: str = Query(...)):
    """HTMX partial returning address details and volume metrics."""
    data = await use_cases.lookup_address(address)
    return templates.TemplateResponse(
        request=request,
        name="partials/address_summary.html",
        context={"summary": data},
    )


@app.get("/partials/persona-card", response_class=HTMLResponse)
async def persona_card_partial(request: Request, address: str = Query(...)):
    """HTMX partial returning multi-wallet Persona Profile card."""
    data = await use_cases.get_persona_profile(address)
    return templates.TemplateResponse(
        request=request,
        name="partials/persona_card.html",
        context={"persona": data},
    )


@app.get("/partials/counterparties", response_class=HTMLResponse)
async def counterparties_partial(request: Request, address: str = Query(...)):
    """HTMX partial returning counterparty interaction table."""
    graph_data = await use_cases.get_graph_topology(address)
    nodes = graph_data["elements"]["nodes"]
    edges = graph_data["elements"]["edges"]
    return templates.TemplateResponse(
        request=request,
        name="partials/counterparties.html",
        context={"nodes": nodes, "edges": edges, "target": address.lower()},
    )


@app.get("/partials/cross-chain", response_class=HTMLResponse)
async def cross_chain_partial(request: Request, address: str = Query(...)):
    """HTMX partial returning cross-chain bridge flows."""
    flows = await use_cases.get_cross_chain_flows(address)
    return templates.TemplateResponse(
        request=request,
        name="partials/cross_chain.html",
        context={"flows": flows, "address": address.lower()},
    )


@app.get("/api/graph-data", response_class=JSONResponse)
async def graph_data_endpoint(address: str = Query(...)):
    """Returns Cytoscape.js format JSON graph data."""
    data = await use_cases.get_graph_topology(address)
    return JSONResponse(content=data)


@app.get("/health")
async def health():
    return {"status": "ok", "app": "crypto-graph-web"}
