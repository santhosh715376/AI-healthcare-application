import os
import re
import random
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("JWT_SECRET", "healthcare_secret_key_2026_super_secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

import bcrypt

security = HTTPBearer()

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def generate_6digit_id() -> int:
    """Generates a random unique 6-digit integer ID (100000-999999)."""
    return random.randint(100000, 999999)


def validate_email(email: str) -> bool:
    """Standard RFC-5322 email syntax validation."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def parse_phone_number(phone_raw: str) -> tuple[str, int]:
    """
    Parses country code and exact 10-digit integer phone number.
    Example: '+919876543210' -> ('+91', 9876543210)
    Example: '9876543210' -> ('+91', 9876543210)
    """
    clean = re.sub(r"[^\d+]", "", str(phone_raw).strip())
    
    country_code = "+91"
    digits = clean

    if clean.startswith("+"):
        if clean.startswith("+91") and len(clean) == 13:
            country_code = "+91"
            digits = clean[3:]
        elif clean.startswith("+1") and len(clean) == 12:
            country_code = "+1"
            digits = clean[2:]
        else:
            # Match +code and rest digits
            match = re.match(r"^(\+[1-9]\d{0,3})(\d{10})$", clean)
            if match:
                country_code = match.group(1)
                digits = match.group(2)

    if not digits.isdigit() or len(digits) != 10:
        raise HTTPException(status_code=400, detail="Phone number must be an exact 10-digit integer (e.g., 9876543210).")

    num_int = int(digits)
    if not (1000000000 <= num_int <= 9999999999):
        raise HTTPException(status_code=400, detail="10-digit phone number must be between 1000000000 and 9999999999.")

    return country_code, num_int


def validate_phone(phone: str) -> bool:
    try:
        parse_phone_number(phone)
        return True
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token authorization.")


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = credentials.credentials
    return decode_access_token(token)


def require_doctor(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "DOCTOR":
        raise HTTPException(status_code=403, detail="Access forbidden: Doctor role required.")
    return current_user


def require_patient(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "PATIENT":
        raise HTTPException(status_code=403, detail="Access forbidden: Patient role required.")
    return current_user
