"""
Authentication and Captcha Router for Multi-Tenant Management.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from ..domain.auth_service import AuthService
from ..domain.captcha import CaptchaEngine
from libs.blockchain_contracts.auth_models import SessionToken, UserRole


class RegisterRequest(BaseModel):
    username: str
    password: str
    tenant_name: Optional[str] = None
    captcha_id: str
    captcha_solution: str


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: str
    captcha_solution: str


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

captcha_engine = CaptchaEngine()


def get_auth_service(request: Request) -> AuthService:
    # Retrieved from app state
    return request.app.state.auth_service


def get_current_session(
    request: Request,
    session_token: Optional[str] = Cookie(None),
) -> Optional[SessionToken]:
    token = session_token or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return None
    auth_service: AuthService = request.app.state.auth_service
    return auth_service.validate_session(token)


def require_auth(session: Optional[SessionToken] = Depends(get_current_session)) -> SessionToken:
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return session


def require_admin(session: SessionToken = Depends(require_auth)) -> SessionToken:
    if session.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return session


@router.get("/captcha")
async def get_captcha():
    """Generates a dynamic pure Python SVG Captcha challenge."""
    challenge_id, svg_content = captcha_engine.generate_challenge()
    return {
        "challenge_id": challenge_id,
        "svg": svg_content,
    }


@router.get("/captcha.svg")
async def get_captcha_svg(id: str):
    """Direct SVG image endpoint for <img src="..."> tags."""
    challenge = captcha_engine._challenges.get(id)
    if not challenge or challenge.is_expired:
        raise HTTPException(status_code=404, detail="Captcha expired or not found.")
    svg = captcha_engine._render_svg(challenge.question_text)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/register")
async def register(req: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)):
    # Validate Captcha
    if not captcha_engine.verify_answer(req.captcha_id, req.captcha_solution):
        raise HTTPException(status_code=400, detail="Invalid or expired captcha.")

    try:
        user = auth_service.register_user(
            username=req.username,
            password=req.password,
            tenant_name=req.tenant_name,
            role=UserRole.MEMBER,
        )
        return {
            "status": "success",
            "user_id": user.user_id,
            "username": user.username,
            "tenant_id": user.tenant_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    # Validate Captcha
    if not captcha_engine.verify_answer(req.captcha_id, req.captcha_solution):
        raise HTTPException(status_code=400, detail="Invalid or expired captcha.")

    try:
        session = auth_service.authenticate(req.username, req.password)
        # Set HTTP-only session cookie
        response.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,
            samesite="lax",
            max_age=86400,
        )
        return {
            "status": "success",
            "token": session.token,
            "username": session.username,
            "role": session.role.value,
            "tenant_id": session.tenant_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(response: Response, session: SessionToken = Depends(require_auth), auth_service: AuthService = Depends(get_auth_service)):
    auth_service.logout(session.token)
    response.delete_cookie("session_token")
    return {"status": "success", "message": "Logged out."}


@router.get("/me")
async def me(session: SessionToken = Depends(require_auth)):
    return {
        "username": session.username,
        "role": session.role.value,
        "tenant_id": session.tenant_id,
        "user_id": session.user_id,
    }
