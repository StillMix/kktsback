from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, sessionmaker  # Импорт sessionmaker
from sqlalchemy import create_engine
from db import Base, get_db  # Импортируем Base и get_db
from student import router as student_router
from teacher import router as teacher_router
from backup import router as backup_router
from auth import router as auth_router
from websocket import router as websocket_router
from decouple import config  
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",  # Ваш Vue.js (Vite) сервер
    "http://127.0.0.1:5173",
    "https://stillmix-kktsback-325a.twc1.net", 
    "https://stillmix-kkts-c97f.twc1.net"
      # Разрешить ваш основной домен (если нужно)
]

ALLOWED_IPS = config("ALLOWED_IPS").split(",")  
VALID_TOKENS = config("VALID_TOKENS").split(",")  
ADMIN_USERNAME = config("ADMIN_USERNAME")  
ADMIN_PASSWORD = config("ADMIN_PASSWORD")  
# Подключение к базе данных


SQLALCHEMY_DATABASE_URL = "sqlite:///./kkts.db"  # Для SQLite, база данных будет храниться в файле test.db

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Создаем приложение FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешенные источники
    allow_credentials=True,  # Разрешить передачу куки
    allow_methods=["*"],  # Разрешенные методы (GET, POST, PUT, DELETE и др.)
    allow_headers=["*"],  # Разрешенные заголовки
)

@app.get("/")
async def home():
    return {"message": "CORS настроен!"}

app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(backup_router)
app.include_router(auth_router)
app.include_router(websocket_router)

