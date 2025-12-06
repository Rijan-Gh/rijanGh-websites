from passlib.context import CryptContext
import hashlib
import secrets
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_salt(length: int = 16) -> str:
    """Generate random salt"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_string(text: str) -> str:
    """Hash string using SHA256"""
    return hashlib.sha256(text.encode()).hexdigest()

def generate_api_key(length: int = 32) -> str:
    """Generate API key for business integration"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_token(length: int = 64) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(length)