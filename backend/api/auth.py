from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import TokenResponse, UserResponse
from app.models import User

router = APIRouter()
auth_service = AuthService()


@router.get("/google/login")
async def google_login(state: Optional[str] = None):
    """Initiate Google OAuth flow"""
    auth_url, state = auth_service.get_authorization_url(state)
    return {"auth_url": auth_url, "state": state}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        result = await auth_service.handle_callback(code, state, db)
        return TokenResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh Google OAuth token"""
    try:
        updated_user = await auth_service.refresh_google_token(current_user, db)
        return {"status": "success", "message": "Token refreshed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token refresh failed: {str(e)}")


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user"""
    # In a production app, you might want to invalidate the JWT token
    return {"status": "success", "message": "Logged out successfully"}


# Dependency to get current user from JWT token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    try:
        user_id = auth_service.verify_token(token)
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# OAuth2 scheme for token extraction
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
