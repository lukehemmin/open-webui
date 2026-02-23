import hashlib
import base64
import secrets
import time
import logging

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

from open_webui.utils.auth import get_admin_user

log = logging.getLogger(__name__)

router = APIRouter()

CHATGPT_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CHATGPT_OAUTH_AUTH_URL = "https://auth.openai.com/oauth/authorize"
CHATGPT_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
CHATGPT_OAUTH_SCOPES = "openid profile email offline_access"
CHATGPT_OAUTH_PLACEHOLDER_KEY = "__chatgpt_oauth__"

# state → {code_verifier, redirect_uri}  (in-memory, single-process)
_pending_states: dict = {}


def _get_redirect_uri(request: Request) -> str:
    custom = request.app.state.config.CHATGPT_OAUTH_REDIRECT_URI
    if custom:
        return custom
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/v1/chatgpt-oauth/callback"


def _make_pkce_pair() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


async def refresh_chatgpt_token(app) -> str:
    """만료 5분 전에 refresh_token으로 갱신. 현재 유효한 access_token 반환."""
    expires_at = app.state.config.CHATGPT_OAUTH_EXPIRES_AT
    access_token = app.state.config.CHATGPT_OAUTH_ACCESS_TOKEN

    if not access_token:
        return ""

    # 만료까지 5분 이상 남아있으면 현재 토큰 반환
    if expires_at and time.time() < expires_at - 300:
        return access_token

    refresh_token = app.state.config.CHATGPT_OAUTH_REFRESH_TOKEN
    if not refresh_token:
        log.warning("ChatGPT OAuth: access token expired and no refresh token available")
        return access_token  # 만료됐지만 그냥 반환 (API가 401 반환할 것)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                CHATGPT_OAUTH_TOKEN_URL,
                json={
                    "client_id": CHATGPT_OAUTH_CLIENT_ID,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/json"},
            ) as r:
                if r.status != 200:
                    text = await r.text()
                    log.error(f"ChatGPT OAuth token refresh failed: {r.status} {text}")
                    return access_token
                data = await r.json()

        app.state.config.CHATGPT_OAUTH_ACCESS_TOKEN = data["access_token"]
        app.state.config.CHATGPT_OAUTH_EXPIRES_AT = time.time() + data.get("expires_in", 3600)
        if "refresh_token" in data:
            app.state.config.CHATGPT_OAUTH_REFRESH_TOKEN = data["refresh_token"]

        log.info("ChatGPT OAuth token refreshed successfully")
        return app.state.config.CHATGPT_OAUTH_ACCESS_TOKEN

    except Exception as e:
        log.exception(f"ChatGPT OAuth token refresh error: {e}")
        return access_token


def _add_openai_connection(request: Request):
    """콜백 성공 후 OPENAI 연결 항목에 chatgpt_oauth 추가 (중복 방지)."""
    urls = list(request.app.state.config.OPENAI_API_BASE_URLS)
    keys = list(request.app.state.config.OPENAI_API_KEYS)
    configs = dict(request.app.state.config.OPENAI_API_CONFIGS)

    already_exists = any(
        configs.get(str(i), {}).get("type") == "chatgpt_oauth"
        for i in range(len(urls))
    )
    if already_exists:
        return

    idx = len(urls)
    urls.append("https://api.openai.com/v1")
    keys.append(CHATGPT_OAUTH_PLACEHOLDER_KEY)
    configs[str(idx)] = {"type": "chatgpt_oauth", "enable": True}

    request.app.state.config.OPENAI_API_BASE_URLS = urls
    request.app.state.config.OPENAI_API_KEYS = keys
    request.app.state.config.OPENAI_API_CONFIGS = configs


def _remove_openai_connection(request: Request):
    """disconnect 시 chatgpt_oauth 연결 항목 제거."""
    urls = list(request.app.state.config.OPENAI_API_BASE_URLS)
    keys = list(request.app.state.config.OPENAI_API_KEYS)
    configs = dict(request.app.state.config.OPENAI_API_CONFIGS)

    oauth_idx = None
    for i in range(len(urls)):
        if configs.get(str(i), {}).get("type") == "chatgpt_oauth":
            oauth_idx = i
            break

    if oauth_idx is None:
        return

    urls.pop(oauth_idx)
    keys.pop(oauth_idx)

    # config 인덱스 재정렬
    new_configs = {}
    new_idx = 0
    for i in range(len(urls) + 1):  # 원래 길이 기준
        if i == oauth_idx:
            continue
        if str(i) in configs:
            new_configs[str(new_idx)] = configs[str(i)]
        new_idx += 1

    request.app.state.config.OPENAI_API_BASE_URLS = urls
    request.app.state.config.OPENAI_API_KEYS = keys
    request.app.state.config.OPENAI_API_CONFIGS = new_configs


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/login")
async def chatgpt_oauth_login(request: Request, user=Depends(get_admin_user)):
    """OAuth PKCE 플로우 시작. auth_url과 사용될 redirect_uri를 반환."""
    redirect_uri = _get_redirect_uri(request)
    code_verifier, code_challenge = _make_pkce_pair()
    state = secrets.token_urlsafe(32)

    _pending_states[state] = {
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
    }

    params = (
        f"client_id={CHATGPT_OAUTH_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={CHATGPT_OAUTH_SCOPES}"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    auth_url = f"{CHATGPT_OAUTH_AUTH_URL}?{params}"

    return {"auth_url": auth_url, "redirect_uri": redirect_uri}


@router.get("/callback")
async def chatgpt_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """OpenAI 인증 후 리다이렉트 되는 콜백. 토큰을 교환하고 설정 저장."""
    if error:
        log.error(f"ChatGPT OAuth error: {error} - {error_description}")
        return RedirectResponse(
            f"/admin/settings?tab=connections&chatgpt_error={error}"
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    pending = _pending_states.pop(state, None)
    if pending is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    code_verifier = pending["code_verifier"]
    redirect_uri = pending["redirect_uri"]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                CHATGPT_OAUTH_TOKEN_URL,
                json={
                    "client_id": CHATGPT_OAUTH_CLIENT_ID,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/json"},
            ) as r:
                if r.status != 200:
                    text = await r.text()
                    log.error(f"ChatGPT OAuth token exchange failed: {r.status} {text}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Token exchange failed: {r.status}",
                    )
                data = await r.json()
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"ChatGPT OAuth token exchange error: {e}")
        raise HTTPException(status_code=502, detail="Token exchange request failed")

    if "access_token" not in data:
        log.error(f"ChatGPT OAuth: no access_token in response: {data}")
        raise HTTPException(status_code=502, detail="No access_token in response")

    request.app.state.config.CHATGPT_OAUTH_ACCESS_TOKEN = data["access_token"]
    request.app.state.config.CHATGPT_OAUTH_REFRESH_TOKEN = data.get("refresh_token", "")
    request.app.state.config.CHATGPT_OAUTH_EXPIRES_AT = time.time() + data.get(
        "expires_in", 3600
    )

    _add_openai_connection(request)

    log.info("ChatGPT OAuth connected successfully")
    return RedirectResponse("/admin/settings?tab=connections&chatgpt=connected")


@router.get("/status")
async def chatgpt_oauth_status(request: Request, user=Depends(get_admin_user)):
    """현재 ChatGPT OAuth 연결 상태 반환."""
    access_token = request.app.state.config.CHATGPT_OAUTH_ACCESS_TOKEN
    expires_at = request.app.state.config.CHATGPT_OAUTH_EXPIRES_AT

    connected = bool(access_token)
    expired = bool(expires_at) and time.time() > expires_at

    return {
        "connected": connected,
        "expires_at": expires_at if expires_at else None,
        "expired": expired,
    }


@router.post("/disconnect")
async def chatgpt_oauth_disconnect(request: Request, user=Depends(get_admin_user)):
    """ChatGPT OAuth 연결 해제. 토큰 삭제 및 OpenAI 연결 항목 제거."""
    request.app.state.config.CHATGPT_OAUTH_ACCESS_TOKEN = ""
    request.app.state.config.CHATGPT_OAUTH_REFRESH_TOKEN = ""
    request.app.state.config.CHATGPT_OAUTH_EXPIRES_AT = 0.0

    _remove_openai_connection(request)

    log.info("ChatGPT OAuth disconnected")
    return {"success": True}


class ChatGPTOAuthConfigForm(BaseModel):
    redirect_uri: str


@router.get("/config")
async def get_chatgpt_oauth_config(request: Request, user=Depends(get_admin_user)):
    """저장된 ChatGPT OAuth 설정 조회."""
    return {
        "redirect_uri": request.app.state.config.CHATGPT_OAUTH_REDIRECT_URI,
    }


@router.post("/config")
async def update_chatgpt_oauth_config(
    request: Request,
    form_data: ChatGPTOAuthConfigForm,
    user=Depends(get_admin_user),
):
    """ChatGPT OAuth 설정 저장 (redirect_uri 등)."""
    request.app.state.config.CHATGPT_OAUTH_REDIRECT_URI = form_data.redirect_uri.strip()
    return {
        "redirect_uri": request.app.state.config.CHATGPT_OAUTH_REDIRECT_URI,
    }
