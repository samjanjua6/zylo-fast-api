from __future__ import annotations

import re
import urllib.parse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.security import create_access_token
from ..users.model import User

router = APIRouter(prefix="/auth/google", tags=["Google OAuth"])

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_INFO_URL  = "https://oauth2.googleapis.com/tokeninfo"


@router.get("/login")
def google_login():
    """Redirect browser to Google's OAuth consent screen."""
    params = {
        "client_id":     settings.GOOGLE_CLIENT_ID,
        "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """Exchange Google auth code → verify identity → issue Zylo JWT → redirect to /chat."""

    # 1. Exchange authorization code for tokens
    try:
        token_resp = httpx.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        })
        token_resp.raise_for_status()
        token_data = token_resp.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Google token exchange failed: {exc}")

    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="No id_token in Google response")

    # 2. Validate id_token and extract user info via Google's tokeninfo endpoint
    try:
        info_resp = httpx.get(GOOGLE_INFO_URL, params={"id_token": id_token})
        info_resp.raise_for_status()
        google_user = info_resp.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Google token validation failed: {exc}")

    google_id = google_user.get("sub")
    email     = google_user.get("email")
    name      = google_user.get("name", "")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Incomplete Google profile")

    # 3. Find or create the user
    # First try to match by google_id, then fall back to email (to link existing accounts)
    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Link Google account to existing email-based user
            user.google_id = google_id
            db.commit()

    if not user:
        # Brand-new user — create one
        username = _unique_username(name, email, db)
        user = User(
            username=username,
            email=email,
            google_id=google_id,
            hashed_password=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. Issue a Zylo JWT and redirect to the chat page
    zylo_token = create_access_token({"sub": str(user.id)})
    redirect_url = (
        "/chat"
        f"?token={urllib.parse.quote(zylo_token)}"
        f"&username={urllib.parse.quote(user.username)}"
    )
    return RedirectResponse(redirect_url)


# ── helpers ───────────────────────────────────────────────────────────────────

def _unique_username(name: str, email: str, db: Session) -> str:
    """Derive a unique username from the Google display name or email prefix."""
    # Lowercase, strip non-alphanumeric, cap at 40 chars
    base = re.sub(r"[^a-z0-9]", "", name.lower().replace(" ", ""))[:40]
    if not base:
        base = re.sub(r"[^a-z0-9]", "", email.split("@")[0].lower())[:40]
    if not base:
        base = "user"

    candidate = base
    counter   = 1
    while db.query(User).filter(User.username == candidate).first():
        candidate = f"{base}{counter}"
        counter  += 1
    return candidate
