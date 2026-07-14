from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import create_access_token, hash_password, verify_password
from ..users.model import User
from ..users.schemas import UserRead, UserSignup
from .schemas import LoginRequest, TokenResponse


router = APIRouter(tags=["Auth"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignup, db: Session = Depends(get_db)):
    """Register a new user. Rejects duplicate username or email."""
    existing = db.query(User).filter(
        or_(User.username == payload.username, User.email == payload.email)
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a signed JWT."""
    identifier = payload.username_or_email.strip()
    user = db.query(User).filter(
        or_(User.username == identifier, User.email == identifier.lower())
    ).first()
    if user is None or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        detail = "This account uses Google Sign-In. Please use the 'Continue with Google' button." \
            if (user and not user.hashed_password) else "Invalid credentials"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=user)
