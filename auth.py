from sqlalchemy.orm import Session
from fastapi import Security, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from db import get_db, TeacherDB, UserDB
from websocket import notify_disconnect_user

router = APIRouter()

SECRET_KEY = "mysecretkey"  # Лучше вынести в .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
@router.post("/auth/login", response_model=AuthResponse)
async def login(auth_data: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(TeacherDB).filter(TeacherDB.login == auth_data.login).first()
    role = "teacher"

    if not user:
        user = db.query(UserDB).filter(UserDB.login == auth_data.login).first()
        role = "user"

    if not user or not verify_password(auth_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    # Преобразуем group в строку
    if role == "teacher":
        # Если у учителя есть группа, то берём её название, если группа есть
        group = user.group[0].name if user.group else "Не назначена"
    else:
        # Для студента это поле остаётся строкой
        group = user.group

    # Создаем JWT-токен
    access_token = create_access_token(
      data={"sub": str(user.id), "role": role},  # Преобразуем ID в строку
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
        group=group,  # Группа теперь преобразована в строку
        id=user.id,
    )


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        role: str = payload.get("role")

        if user_id is None or role is None:
            raise HTTPException(status_code=401, detail="Недействительный токен")

        # Найти пользователя в БД
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        return {"user": user, "role": role}
    except JWTError as e:
        print("Ошибка JWT:", e)
        raise HTTPException(status_code=401, detail="Недействительный токен")