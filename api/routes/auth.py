"""
Authentication API Routes
Login, logout, and token management endpoints
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr

from ..auth.security import (
    authenticate_user, create_access_token, create_refresh_token,
    verify_token, get_current_user, audit_log
)
from ..models.api_models import ApiResponse
from src.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class RefreshRequest(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    username: str
    email: str
    role: str
    permissions: list
    last_login: datetime

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT tokens
    
    Args:
        request: Login credentials
        
    Returns:
        LoginResponse: JWT tokens and user information
    """
    try:
        # Authenticate user
        user = authenticate_user(request.username, request.password)
        if not user:
            audit_log("LOGIN_FAILED", request.username, "auth", "Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": user["username"], "type": "refresh"}
        )
        
        # Log successful login
        audit_log("LOGIN_SUCCESS", user["username"], "auth", f"Role: {user['role']}")
        
        # Return response
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user={
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "permissions": user["permissions"],
                "last_login": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token
    
    Args:
        request: Refresh token request
        
    Returns:
        New access token
    """
    try:
        # Verify refresh token
        payload = verify_token(request.refresh_token, "refresh")
        username = payload.get("sub")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        
        audit_log("TOKEN_REFRESH", username, "auth", "Access token refreshed")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.post("/logout", response_model=ApiResponse)
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout user (invalidate tokens)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Logout confirmation
    """
    try:
        # In a real implementation, you would add the token to a blacklist
        # For now, we'll just log the logout
        
        audit_log("LOGOUT", current_user["username"], "auth", "User logged out")
        
        return ApiResponse(
            success=True,
            message="Logged out successfully",
            data={
                "username": current_user["username"],
                "logout_time": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user profile
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserProfile: User profile information
    """
    try:
        return UserProfile(
            username=current_user["username"],
            email=current_user["email"],
            role=current_user["role"],
            permissions=current_user["permissions"],
            last_login=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

@router.get("/verify", response_model=ApiResponse)
async def verify_token_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Verify if current token is valid
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Token verification result
    """
    return ApiResponse(
        success=True,
        message="Token is valid",
        data={
            "username": current_user["username"],
            "role": current_user["role"],
            "verified_at": datetime.utcnow().isoformat()
        }
    )

@router.get("/demo-users", response_model=ApiResponse)
async def get_demo_users():
    """
    Get demo user credentials for development
    
    Returns:
        Demo user information (development only)
    """
    demo_info = {
        "admin": {"username": "admin", "password": "admin123", "role": "administrator"},
        "doctor": {"username": "doctor", "password": "doctor123", "role": "physician"},
        "nurse": {"username": "nurse", "password": "nurse123", "role": "nurse"},
        "viewer": {"username": "viewer", "password": "viewer123", "role": "observer"}
    }
    
    return ApiResponse(
        success=True,
        message="Demo user credentials (development only)",
        data=demo_info
    )