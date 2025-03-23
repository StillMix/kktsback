from sqlalchemy.orm import Session
from fastapi import HTTPException, APIRouter, Depends
from db import TeacherDB, GroupDB, ClassRykDB, Base, get_db
from pydantic import BaseModel 
from typing import Optional
import bcrypt

router = APIRouter()

# Модель для данных, которые мы получаем от клиента (Pydantic)

class Item(BaseModel):
    name: str
    fullname: str
    role: str
    login: str
    password: str 
    gmail: str
    vk: str


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

@router.post("/teachers/")
async def register_teacher(item: Item, db: Session = Depends(get_db)):
    # Проверка уникальности в базе данных
    existing_user = db.query(TeacherDB).filter(TeacherDB.gmail == item.gmail).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Gmail уже используется")
    
    existing_vk = db.query(TeacherDB).filter(TeacherDB.vk == item.vk).first()
    if existing_vk:
        raise HTTPException(status_code=400, detail="VK уже используется")
    
    # Хэшируем пароль перед сохранением
    hashed_password = hash_password(item.password)

    # Создаем нового пользователя
    user = TeacherDB(
        name=item.name, 
        fullname=item.fullname, 
        role="teacher", 
        login=item.login, 
        password=hashed_password,  # Храним хэшированный пароль
        gmail=item.gmail, 
        vk=item.vk, 
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Учитель успешно зарегистрирован", "user": item}

@router.get("/teachers/")
async def get_all_teachers(db: Session = Depends(get_db)):
    # Получаем всех пользователей из базы данных
    users = db.query(TeacherDB).all()
    
    # Преобразуем пользователей в формат, подходящий для возврата
    return {"message": "Учителя получены", "users": users}

@router.delete("/teachers/{id}/")
async def del_teacher(id: int, db: Session = Depends(get_db)):
    # Ищем пользователя по id
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()

    # Если пользователь не найден, возвращаем ошибку
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Удаляем пользователя
    db.delete(user)
    db.commit()

    return {"message": f"Учитель удален"}


@router.get("/teachers/{id}/")
async def get_one_teacher(id: int, db: Session = Depends(get_db)):
    # Ищем студента по id
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()

    # Если студент не найден, возвращаем ошибку
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Возвращаем данные студента
    return {"message": "Учитель получен", "user": user}


class Updateteacher(BaseModel):
    name: Optional[str] = None
    fullname: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    gmail: Optional[str] = None
    vk: Optional[str] = None
    group: Optional[str] = None

@router.put("/teachers/{id}/")
async def put_teacher(id: int, teacher_data: Updateteacher, db: Session = Depends(get_db)):
    # Ищем студента по id
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()

    # Если студент не найден, возвращаем ошибку
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Обновляем данные только если переданы новые значения
    if teacher_data.name is not None:
        user.name = teacher_data.name
    if teacher_data.fullname is not None:
        user.fullname = teacher_data.fullname
    if teacher_data.login is not None:
        user.login = teacher_data.login
    if teacher_data.password is not None:
        user.password = hash_password(teacher_data.password)
    if teacher_data.gmail is not None:
        user.gmail = teacher_data.gmail
    if teacher_data.vk is not None:
        user.vk = teacher_data.vk

    # Сохраняем изменения в базе данных
    db.commit()
    db.refresh(user)

    return {"message": "Учитель обновлен", "user": user}


@router.get("/teachers/{id}/subjects/")
async def get_teacher_subjects(id: int, db: Session = Depends(get_db)):
    # Ищем студента
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Получаем предметы студента
    subjects = db.query(PredmetDB).filter(PredmetDB.user_id == id).all()
    
    return {"message": "Предметы получены","subjects": subjects}

class PredmetCreate(BaseModel):
    color: str
    predmet: str
    attes: str
    srbal: float

@router.post("/teachers/{id}/subjects/")
async def add_teacher_subject(id: int, subject: PredmetCreate, db: Session = Depends(get_db)):
    # Проверяем, есть ли студент
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Создаем предмет
    new_subject = PredmetDB(
        color=subject.color,
        predmet=subject.predmet,
        attes=subject.attes,
        srbal=subject.srbal,
        user_id=id
    )

    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)

    return {"message": "Класс добавлен", "subject": new_subject}

class PredmetUpdate(BaseModel):
    color: Optional[str] = None
    predmet: Optional[str] = None
    attes: Optional[str] = None
    srbal: Optional[float] = None


@router.delete("/teachers/{id}/subjects/{subject_id}/")
async def delete_subject(id: int, subject_id: int, db: Session = Depends(get_db)):
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Класс не найден или не прнадлежит студенту")

    db.delete(subject)
    db.commit()

    return {"message": "Класс удален"}



class OcenkaCreate(BaseModel):
    name: str
    data: str
    ocenka: str

@router.post("/teachers/{id}/subjects/{subject_id}/ocenki/")
async def create_ocenka(id: int, subject_id: int, ocenka: OcenkaCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Класс не найден или не принадлежит студенту")

    # Создаем новую оценку
    new_ocenka = OcenkaDB(name=ocenka.name, data=ocenka.data, ocenka=ocenka.ocenka, predmet_id=subject.id)
    db.add(new_ocenka)
    db.commit()
    db.refresh(new_ocenka)

    return {"message": "Класс добавлена", "ocenka": new_ocenka}


@router.get("/teachers/{id}/subjects/{subject_id}/ocenki/")
async def get_ocenki(id: int, subject_id: int, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Класс не найден или не принадлежит студенту")

    # Получаем все оценки для данного предмета
    ocenki = db.query(OcenkaDB).filter(OcenkaDB.predmet_id == subject_id).all()

    return {"ocenki": ocenki}


@router.put("/teachers/{id}/subjects/{subject_id}/ocenki/{ocenka_id}/")
async def update_ocenka(
    id: int, 
    subject_id: int, 
    ocenka_id: int, 
    ocenka: OcenkaCreate,  # Параметры для обновления
    db: Session = Depends(get_db)
):
    # Находим оценку по ID
    db_ocenka = db.query(OcenkaDB).filter(OcenkaDB.id == ocenka_id, OcenkaDB.predmet_id == subject_id).first()

    # Если оценка не найдена, возвращаем ошибку
    if not db_ocenka:
        raise HTTPException(status_code=404, detail="Класс не найдена")

    # Обновляем поля оценка
    db_ocenka.name = ocenka.name
    db_ocenka.data = ocenka.data
    db_ocenka.ocenka = ocenka.ocenka

    db.commit()  # Сохраняем изменения
    db.refresh(db_ocenka)  # Обновляем объект

    return {"message": "Класс обновлена", "ocenka": db_ocenka}

@router.delete("/teachers/{id}/subjects/{subject_id}/ocenki/{ocenka_id}/")
async def delete_ocenka(id: int, subject_id: int, ocenka_id: int, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Класс не найден или не принадлежит студенту")

    # Проверяем, существует ли оценка
    ocenka = db.query(OcenkaDB).filter(OcenkaDB.id == ocenka_id, OcenkaDB.predmet_id == subject_id).first()
    if not ocenka:
        raise HTTPException(status_code=404, detail="Класс не найдена")

    db.delete(ocenka)
    db.commit()

    return {"message": "Класс удалена"}
