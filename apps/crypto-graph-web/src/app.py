"""
FastAPI Server-Rendered (SSR) Web Frontend for crypto-graph.
Pure Python web layer utilizing Jinja2 templates, HTMX partials, and Cytoscape.js.
Supports Multi-Tenancy, Built-in Captcha, and Comprehensive Admin Configurations.
"""

from pathlib import Path
from typing import Any, Optional
from fastapi import Cookie, FastAPI, Form, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from libs.blockchain_contracts.auth_models import UserRole
from libs.blockchain_contracts.config_models import SearchHistoryRecord
from libs.blockchain_contracts.fixtures import (
    CLUSTER_WALLET_A,
    SATOSHI_BTC,
    SOLANA_SAMPLE,
    TRON_SAMPLE,
    VITALIK_ETH,
)
from services.crypto_graph_api.src.application.use_cases import CryptoGraphUseCases
from services.crypto_graph_api.src.domain.auth_service import AuthService
from services.crypto_graph_api.src.domain.captcha import CaptchaEngine
from services.crypto_graph_api.src.domain.clustering import PersonaClusteringEngine
from services.crypto_graph_api.src.domain.config_service import ConfigService
from services.crypto_graph_api.src.infrastructure.admin_router import router as admin_router
from services.crypto_graph_api.src.infrastructure.api_router import router as api_router
from services.crypto_graph_api.src.infrastructure.auth_router import captcha_engine, router as auth_router
from services.crypto_graph_api.src.infrastructure.investigation_router import router as investigation_router
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

# Shared backend instances
storage = SqliteGraphStorage()
config_service = ConfigService(storage)
auth_service = AuthService(storage, config_service=config_service)
clustering_engine = PersonaClusteringEngine(config_service=config_service)
rpc = ResilientRpcRotator(config_service=config_service, offline_mode=False)
use_cases = CryptoGraphUseCases(
    rpc_provider=rpc,
    storage=storage,
    clustering=clustering_engine,
)

# Attach state for routers
app.state.storage = storage
app.state.config_service = config_service
app.state.auth_service = auth_service
app.state.use_cases = use_cases

# Mount API routers
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(investigation_router)


def get_session_from_request(request: Request) -> Optional[Any]:
    token = request.cookies.get("session_token")
    if not token:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            token = auth_hdr.replace("Bearer ", "").strip()
    if token:
        return auth_service.validate_session(token)
    return None


@app.get("/", response_class=HTMLResponse)
async def index_view(request: Request, address: Optional[str] = Query(None)):
    """Primary render-view dashboard."""
    initial_address = address or VITALIK_ETH
    session = get_session_from_request(request)

    # Record search in history if authenticated
    if session and address:
        storage.add_search_history(
            SearchHistoryRecord(
                search_id=f"search-{initial_address[:6]}",
                tenant_id=session.tenant_id,
                user_id=session.user_id,
                address=initial_address,
                chain="ethereum",
            )
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "default_address": initial_address,
            "sample_vitalik": VITALIK_ETH,
            "sample_satoshi": SATOSHI_BTC,
            "sample_cluster": CLUSTER_WALLET_A,
            "sample_solana": SOLANA_SAMPLE,
            "sample_tron": TRON_SAMPLE,
            "session": session,
        },
    )


# --- Authentication Web Views ---
@app.get("/auth/login", response_class=HTMLResponse)
async def login_view(request: Request, error: Optional[str] = None):
    challenge_id, svg = captcha_engine.generate_challenge()
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "captcha_id": challenge_id,
            "captcha_svg": svg,
            "error": error,
        },
    )


@app.post("/auth/login")
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    captcha_id: str = Form(...),
    captcha_solution: str = Form(...),
):
    if not captcha_engine.verify_answer(captcha_id, captcha_solution):
        return await login_view(request, error="Invalid or expired security captcha solution.")

    try:
        session = auth_service.authenticate(username, password)
        resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        resp.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,
            samesite="lax",
            max_age=86400,
        )
        return resp
    except ValueError as e:
        return await login_view(request, error=str(e))


@app.get("/auth/register", response_class=HTMLResponse)
async def register_view(request: Request, error: Optional[str] = None):
    challenge_id, svg = captcha_engine.generate_challenge()
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "captcha_id": challenge_id,
            "captcha_svg": svg,
            "error": error,
        },
    )


@app.post("/auth/register")
async def register_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    tenant_name: str = Form(...),
    captcha_id: str = Form(...),
    captcha_solution: str = Form(...),
):
    if not captcha_engine.verify_answer(captcha_id, captcha_solution):
        return await register_view(request, error="Invalid or expired security captcha solution.")

    try:
        auth_service.register_user(username, password, tenant_name=tenant_name)
        # Automatically authenticate after registration
        session = auth_service.authenticate(username, password)
        resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        resp.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,
            samesite="lax",
            max_age=86400,
        )
        return resp
    except ValueError as e:
        return await register_view(request, error=str(e))


@app.post("/auth/logout")
async def logout_action(request: Request):
    token = request.cookies.get("session_token")
    if token:
        auth_service.logout(token)
    resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie("session_token")
    return resp


# --- Admin Web Views ---
@app.get("/admin/config", response_class=HTMLResponse)
async def admin_config_view(request: Request):
    session = get_session_from_request(request)
    if not session or session.role != UserRole.ADMIN:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    all_configs = storage.get_all_configs()
    config_dict = {c.config_key: c.config_value for c in all_configs}

    return templates.TemplateResponse(
        request=request,
        name="admin/config.html",
        context={
            "session": session,
            "configs": config_dict,
        },
    )


@app.get("/admin/personas", response_class=HTMLResponse)
async def admin_personas_view(request: Request):
    session = get_session_from_request(request)
    if not session or session.role != UserRole.ADMIN:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    personas = storage.get_all_personas()
    return templates.TemplateResponse(
        request=request,
        name="admin/personas.html",
        context={
            "session": session,
            "personas": personas,
        },
    )


@app.get("/admin/tenants", response_class=HTMLResponse)
async def admin_tenants_view(request: Request):
    session = get_session_from_request(request)
    if not session or session.role != UserRole.ADMIN:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    tenants = storage.get_all_tenants()
    users = storage.get_all_users()
    return templates.TemplateResponse(
        request=request,
        name="admin/tenants.html",
        context={
            "session": session,
            "tenants": tenants,
            "users": users,
        },
    )


# --- Streaming HTMX Partials ---
@app.get("/partials/investigation-panel", response_class=HTMLResponse)
async def investigation_panel_partial(request: Request):
    session = get_session_from_request(request)
    watchlist = []
    investigations = []
    search_history = []
    if session:
        watchlist = storage.get_watchlist(session.tenant_id)
        investigations = storage.get_investigations(session.tenant_id)
        search_history = storage.get_search_history(session.tenant_id, limit=8)

    return templates.TemplateResponse(
        request=request,
        name="partials/investigation_panel.html",
        context={
            "session": session,
            "watchlist": watchlist,
            "investigations": investigations,
            "search_history": search_history,
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
