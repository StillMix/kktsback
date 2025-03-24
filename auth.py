from sqlalchemy.orm import Session
from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from db import get_db, TeacherDB, UserDB

router = APIRouter()

SECRET_KEY = "mysecretkey"  # Лучше вынести в .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class AuthRequest(BaseModel):
    login: str
    password: str  # исправленная опечатка

class AuthResponse(BaseModel):
    id: int
    access_token: str
    token_type: str
    role: str
    name: str
    fullname: str
    login: str
    gmail: str
    vk: str
    group: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/auth/login", response_model=AuthResponse)  # Должен быть POST-запрос
async def login(auth_data: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(TeacherDB).filter(TeacherDB.login == auth_data.login).first()
    role = "teacher"

    if not user:
        user = db.query(UserDB).filter(UserDB.login == auth_data.login).first()
        role = "user"

    if not user or not verify_password(auth_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    # Создаем JWT-токен
    access_token = create_access_token(
        data={"sub": user.id, "role": role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        role=role,
        name=user.name,
        fullname=user.fullname,
        login=user.login,
        gmail=user.gmail,
        vk=user.vk,
        group=user.group,
        id=user.id,
    )
