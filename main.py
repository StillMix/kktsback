from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, sessionmaker  # Импорт sessionmaker
from sqlalchemy import create_engine
from db import Base, get_db  # Импортируем Base и get_db
from student import router as student_router
from teacher import router as teacher_router
from backup import router as backup_router
from decouple import config  

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

app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(backup_router)

