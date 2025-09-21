from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.services.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class UserCreate(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    username = decode_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = db.query(User).filter(User.username == username).first()
    # user.is_active puede ser una columna; asegurar coerción booleana
    if not user or not bool(getattr(user, "is_active", True)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return user

@router.post("/register", response_model=TokenOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(400, "Username ya existe")
    user = User(username=payload.username, hashed_password=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    username = str(user.username)
    access = create_access_token(username)
    refresh = create_refresh_token(username)
    return TokenOut(access_token=access, refresh_token=refresh)

@router.post("/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    username = str(user.username)
    access = create_access_token(username)
    refresh = create_refresh_token(username)
    return TokenOut(access_token=access, refresh_token=refresh)

@router.get("/me")
def me(current: User = Depends(get_current_user)):
    return {"id": current.id, "username": current.username}


class RefreshIn(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshIn):
    username = decode_token(payload.refresh_token, refresh=True)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")
    # Rotación (emitimos nuevos access+refresh). Para revocación real se debe invalidar el anterior.
    new_access = create_access_token(username)
    new_refresh = create_refresh_token(username)
    return TokenOut(access_token=new_access, refresh_token=new_refresh)

