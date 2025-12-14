"""
Authentication and Security Module for EDFlow AI
Implements JWT-based authentication and security middleware
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from passlib.hash import bcrypt

from src.utils import get_logger

logger = get_logger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "edflow-ai-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Demo users for development (in production, use a proper database)
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@edflow.ai",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "administrator",
        "permissions": ["read", "write", "admin", "simulate"]
    },
    "doctor": {
        "username": "doctor",
        "email": "doctor@edflow.ai", 
        "hashed_password": pwd_context.hash("doctor123"),
        "role": "physician",
        "permissions": ["read", "write", "simulate"]
    },
    "nurse": {
        "username": "nurse",
        "email": "nurse@edflow.ai",
        "hashed_password": pwd_context.hash("nurse123"),
        "role": "nurse",
        "permissions": ["read", "write"]
    },
    "viewer": {
        "username": "viewer",
        "email": "viewer@edflow.ai",
        "hashed_password": pwd_context.hash("viewer123"),
        "role": "observer",
        "permissions": ["read"]
    }
}

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

class AuthorizationError(Exception):
    """Custom authorization error"""
    pass

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with username and password"""
    user = DEMO_USERS.get(username)
    if not user:
        return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise AuthenticationError("Failed to create access token")

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {str(e)}")
        raise AuthenticationError("Failed to create refresh token")

def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            raise AuthenticationError(f"Invalid token type. Expected {token_type}")
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise AuthenticationError("Token has expired")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        
        # Verify token
        payload = verify_token(token, "access")
        
        # Get user info
        username = payload.get("sub")
        if not username:
            raise AuthenticationError("Invalid token payload")
        
        user = DEMO_USERS.get(username)
        if not user:
            raise AuthenticationError("User not found")
        
        # Return user info without password hash
        return {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "permissions": user["permissions"]
        }
        
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    
    return permission_checker

def require_role(role: str):
    """Decorator to require specific role"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {role}"
            )
        return current_user
    
    return role_checker

# Security middleware functions
def validate_api_key(api_key: str) -> bool:
    """Validate API key for external integrations"""
    valid_api_keys = os.getenv("VALID_API_KEYS", "").split(",")
    return api_key in valid_api_keys if valid_api_keys != [""] else True

def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "&", "\"", "'", "/", "\\"]
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    # Limit length
    return sanitized[:max_length]

def validate_patient_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize patient data"""
    if not isinstance(data, dict):
        raise ValueError("Patient data must be a dictionary")
    
    # Sanitize string fields
    string_fields = ["chief_complaint", "ems_report", "location"]
    for field in string_fields:
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_input(data[field], 500)
    
    # Validate vital signs ranges
    if "vitals" in data and isinstance(data["vitals"], dict):
        vitals = data["vitals"]
        
        # Heart rate validation (30-300 bpm)
        if "hr" in vitals:
            hr = vitals["hr"]
            if not isinstance(hr, (int, float)) or hr < 30 or hr > 300:
                raise ValueError("Invalid heart rate. Must be between 30-300 bpm")
        
        # Blood pressure validation
        if "bp_sys" in vitals:
            bp_sys = vitals["bp_sys"]
            if not isinstance(bp_sys, (int, float)) or bp_sys < 50 or bp_sys > 300:
                raise ValueError("Invalid systolic BP. Must be between 50-300 mmHg")
        
        if "bp_dia" in vitals:
            bp_dia = vitals["bp_dia"]
            if not isinstance(bp_dia, (int, float)) or bp_dia < 30 or bp_dia > 200:
                raise ValueError("Invalid diastolic BP. Must be between 30-200 mmHg")
        
        # SpO2 validation (70-100%)
        if "spo2" in vitals:
            spo2 = vitals["spo2"]
            if not isinstance(spo2, (int, float)) or spo2 < 70 or spo2 > 100:
                raise ValueError("Invalid SpO2. Must be between 70-100%")
        
        # Temperature validation (30-45°C)
        if "temp" in vitals:
            temp = vitals["temp"]
            if not isinstance(temp, (int, float)) or temp < 30 or temp > 45:
                raise ValueError("Invalid temperature. Must be between 30-45°C")
    
    return data

# Rate limiting (simple in-memory implementation)
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_minutes: int = 15):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for given identifier"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # Check if under limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(identifier: str):
    """Check rate limit for identifier"""
    if not rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

# Security headers middleware
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

def add_security_headers(response):
    """Add security headers to response"""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

# HIPAA compliance helpers
def anonymize_patient_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove or anonymize sensitive patient information"""
    # Remove or hash sensitive fields
    sensitive_fields = ["name", "ssn", "dob", "address", "phone"]
    
    anonymized = data.copy()
    for field in sensitive_fields:
        if field in anonymized:
            del anonymized[field]
    
    # Keep only medical data necessary for ED operations
    return anonymized

def audit_log(action: str, user: str, resource: str, details: Optional[str] = None):
    """Log security-relevant actions for audit trail"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "user": user,
        "resource": resource,
        "details": details,
        "ip_address": "system"  # Would be extracted from request in real implementation
    }
    
    # In production, this would write to a secure audit log
    logger.info(f"AUDIT: {action} by {user} on {resource}")
    
    return log_entry

# Export security functions
__all__ = [
    "get_current_user",
    "require_permission", 
    "require_role",
    "validate_api_key",
    "sanitize_input",
    "validate_patient_data",
    "check_rate_limit",
    "add_security_headers",
    "anonymize_patient_data",
    "audit_log",
    "authenticate_user",
    "create_access_token",
    "create_refresh_token",
    "verify_token"
]