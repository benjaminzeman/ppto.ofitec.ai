from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.settings import get_settings

ALGORITHM = "HS256"

# Obtenemos duraciones desde settings (con fallback por compatibilidad)
def _access_minutes() -> int:
    return getattr(get_settings(), "access_token_minutes", 60 * 8)

def _refresh_minutes() -> int:
    return getattr(get_settings(), "refresh_token_minutes", 60 * 24 * 14)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_secret_key() -> str:
    return get_settings().jwt_secret

def get_refresh_secret_key() -> str:
    return get_settings().refresh_jwt_secret

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=_access_minutes())
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "type": "access", "exp": expire}
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)

def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=_refresh_minutes())
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "type": "refresh", "exp": expire}
    return jwt.encode(to_encode, get_refresh_secret_key(), algorithm=ALGORITHM)

def decode_token(token: str, refresh: bool = False) -> Optional[str]:
    try:
        secret = get_refresh_secret_key() if refresh else get_secret_key()
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if refresh and token_type != "refresh":
            return None
        if not refresh and token_type != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None

# Validación y rotación (stateless). Para revocación futura se podría
# almacenar refresh tokens en tabla (jti + blacklist). Placeholder jti omitido.

