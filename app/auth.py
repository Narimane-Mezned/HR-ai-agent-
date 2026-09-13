import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Header

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hr-ai-agent-dev-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8

PASSWORD_MIN_LENGTH = 8

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")


def validate_password_strength(password: str) -> str | None:
    """Returns an error message if the password doesn't meet the policy, otherwise None."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    return None


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: str = Header(...)) -> str:
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_admin(user: str = Depends(get_current_user)) -> str:
    if user.strip().lower() != ADMIN_USERNAME.lower():
        raise HTTPException(status_code=403, detail="Admin access required")
    return user