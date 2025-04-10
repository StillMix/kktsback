from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, sessionmaker  
from sqlalchemy import create_engine
from db import Base, get_db  
from student import router as student_router
from teacher import router as teacher_router
from backup import router as backup_router
from auth import router as auth_router
from websocket import router as websocket_router
from lesson import router as lesson_router
from decouple import config  
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",  
    "http://127.0.0.1:5173",
    "http://172.20.10.2:8000",
    "https://kktsback.tw1.ru", 
    "https://kkts.tw1.ru"
]

ALLOWED_IPS = config("ALLOWED_IPS").split(",")  
VALID_TOKENS = config("VALID_TOKENS").split(",")  
ADMIN_USERNAME = config("ADMIN_USERNAME")  
ADMIN_PASSWORD = config("ADMIN_PASSWORD")  



SQLALCHEMY_DATABASE_URL = "sqlite:///./kkts.db" 

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,  
    allow_methods=["*"], 
    allow_headers=["*"],  
)

@app.get("/")
async def home():
    return {"message": "CORS настроен!"}

app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(backup_router)
app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(lesson_router)
