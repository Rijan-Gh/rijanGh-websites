from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def generate_access_key(length: int = 32) -> str:
    """Generate secure access key for business registration"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_otp(length: int = 6) -> str:
    """Generate OTP for phone verification"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def sanitize_phone_number(phone: str) -> str:
    """Sanitize phone number to E.164 format"""
    # Remove all non-numeric characters
    cleaned = ''.join(filter(str.isdigit, phone))
    
    # Add country code if not present (assuming India +91)
    if not cleaned.startswith('91') and len(cleaned) == 10:
        cleaned = '91' + cleaned
    
    return '+' + cleaned