import jwt
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from config import settings
from loguru import logger

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=1440)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_credentials(request: Request):
    token = request.cookies.get("admin_session")
    
    # Check authorization header as fallback for API endpoints
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        # If it's a browser request to an HTML page, we should ideally redirect to login.
        # However, for generic dependency, raising 401 is standard.
        # We'll let the caller handle redirection or just throw 401.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
        
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None or username != settings.admin_username:
            raise HTTPException(status_code=401, detail="Invalid session")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid session")
