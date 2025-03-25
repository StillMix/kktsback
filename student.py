from sqlalchemy.orm import Session
from fastapi import HTTPException, APIRouter, Depends
from db import UserDB, PredmetDB, OcenkaDB, TeacherDB, Base, get_db
from pydantic import BaseModel 
from typing import Optional
import bcrypt
from websocket import notify_disconnect_user  # Импортируем функцию
from auth import get_current_user


router = APIRouter()

# Модель для данных, которые мы получаем от клиента (Pydantic)
class OcenkaItem(BaseModel):
    name: str
    data: str
    ocenka: str

class PredmetItem(BaseModel):
    color: str
    predmet: str
    attes: str
    srbal: float
    ocenki: list[OcenkaItem] = []

class Item(BaseModel):
    name: str
    fullname: str
    role: str
    login: str
    password: str 
    gmail: str
    vk: str
    group: str
    ocenki: list[PredmetItem] = []


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

@router.post("/students/")
async def register_student(item: Item, db: Session = Depends(get_db)):
    # Проверка уникальности в базе данных
    existing_user = db.query(UserDB).filter(UserDB.gmail == item.gmail).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Gmail уже используется")
    
    existing_vk = db.query(UserDB).filter(UserDB.vk == item.vk).first()
    if existing_vk:
        raise HTTPException(status_code=400, detail="VK уже используется")
    
    # Хэшируем пароль перед сохранением
    hashed_password = hash_password(item.password)

    # Создаем нового пользователя
    user = UserDB(
        name=item.name, 
        fullname=item.fullname, 
        role="student", 
        login=item.login, 
        password=hashed_password,  # Храним хэшированный пароль
        gmail=item.gmail, 
        vk=item.vk, 
        group=item.group
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Добавляем предметы и оценки (если есть)
    if item.ocenki:
        for predmet in item.ocenki:
            db_predmet = PredmetDB(
                color=predmet.color, 
                predmet=predmet.predmet, 
                attes=predmet.attes, 
                srbal=predmet.srbal, 
                user_id=user.id
            )
            db.add(db_predmet)
            db.commit()
            db.refresh(db_predmet)

            for ocenka in predmet.ocenki:
                db_ocenka = OcenkaDB(
                    name=ocenka.name, 
                    data=ocenka.data, 
                    ocenka=ocenka.ocenka, 
                    predmet_id=db_predmet.id
                )
                db.add(db_ocenka)

            db.commit()

    return {"message": "Студент успешно зарегистрирован", "user": item}

@router.get("/students/")
async def get_all_students(db: Session = Depends(get_db)):
    # Получаем всех пользователей из базы данных
    users = db.query(UserDB).all()
    
    # Преобразуем пользователей в формат, подходящий для возврата
    return {"message": "Студенты получены", "users": users}

@router.delete("/students/{id}/")
async def del_student(id: int, db: Session = Depends(get_db)):
    # Ищем пользователя по id
    user = db.query(UserDB).filter(UserDB.id == id).first()

    # Если пользователь не найден, возвращаем ошибку
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Удаляем пользователя
    db.delete(user)
    db.commit()

    # Отправляем уведомление об отключении
    await notify_disconnect_user(user.id, user.name, "student")
    return {"message": f"Студент удален"}


@router.get("/students/{id}/")
async def get_one_student(id: int, db: Session = Depends(get_db)):
    # Ищем студента по id
    user = db.query(UserDB).filter(UserDB.id == id).first()

    # Если студент не найден, возвращаем ошибку
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Возвращаем данные студента
    return {"message": "Студент получен", "user": user}


class UpdateStudent(BaseModel):
    name: Optional[str] = None
    fullname: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    gmail: Optional[str] = None
    vk: Optional[str] = None
    group: Optional[str] = None

@router.put("/students/{id}/")
async def put_student(id: int, student_data: UpdateStudent, db: Session = Depends(get_db)):
    # Ищем студента по id
    user = db.query(UserDB).filter(UserDB.id == id).first()

    # Если студент не найден, возвращаем ошибку
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Обновляем данные только если переданы новые значения
    if student_data.name is not None:
        user.name = student_data.name
    if student_data.fullname is not None:
        user.fullname = student_data.fullname
    if student_data.gmail is not None:
        user.gmail = student_data.gmail
    if student_data.login is not None:
        user.login = student_data.login
    if student_data.password is not None:
        user.password = hash_password(student_data.password)
    if student_data.vk is not None:
        user.vk = student_data.vk
    if student_data.group is not None:
        user.group = student_data.group

    # Сохраняем изменения в базе данных
    db.commit()
    db.refresh(user)

    return {"message": "Студент обновлен", "user": user}


@router.get("/students/{id}/subjects/")
async def get_student_subjects(
    id: int, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)  # Добавляем проверку текущего пользователя
):
    if current_user["role"] == "teacher":
        # Проверка, если у учителя есть доступ к группе студента
        student = db.query(UserDB).filter(UserDB.id == id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Студент не найден")
        print(current_user)
        # Проверяем, что учитель ведет занятия в группе студента
        teacher = db.query(TeacherDB).filter(TeacherDB.id == current_user['user'].id).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Учитель не найден")

        # Проверка, что учитель связан с группой студента (например, через group)
        if teacher.group and student.group != teacher.group:
            raise HTTPException(status_code=403, detail="Учитель не имеет доступа к этому студенту")

    elif current_user['user'].id != id:
        # Если текущий пользователь не учитель, то проверяем, что он не пытается получить доступ к данным другого пользователя
        raise HTTPException(status_code=403, detail="У вас нет доступа к данным другого студента")

    # Получаем предметы студента
    subjects = db.query(PredmetDB).filter(PredmetDB.user_id == id).all()

    return {"message": "Предметы получены", "subjects": subjects}

class PredmetCreate(BaseModel):
    color: str
    predmet: str
    attes: str
    srbal: float

@router.post("/students/{id}/subjects/")
async def add_student_subject(id: int, subject: PredmetCreate, db: Session = Depends(get_db)):
    # Проверяем, есть ли студент
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

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

    return {"message": "Предмет добавлен", "subject": new_subject}

class PredmetUpdate(BaseModel):
    color: Optional[str] = None
    predmet: Optional[str] = None
    attes: Optional[str] = None
    srbal: Optional[float] = None

@router.put("/students/{id}/subjects/{subject_id}/")
async def update_subject(id: int, subject_id: int, subject_data: PredmetUpdate, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Предмет не найден или не принадлежит студенту")

    # Обновляем только переданные поля
    if subject_data.color is not None:
        subject.color = subject_data.color
    if subject_data.predmet is not None:
        subject.predmet = subject_data.predmet
    if subject_data.attes is not None:
        subject.attes = subject_data.attes
    if subject_data.srbal is not None:
        subject.srbal = subject_data.srbal

    db.commit()
    db.refresh(subject)

    return {"message": "Предмет обновлен", "subject": subject}

@router.delete("/students/{id}/subjects/{subject_id}/")
async def delete_subject(id: int, subject_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Предмет не найден или не прнадлежит студенту")

    db.delete(subject)
    db.commit()

    return {"message": "Предмет удален"}



class OcenkaCreate(BaseModel):
    name: str
    data: str
    ocenka: str

@router.post("/students/{id}/subjects/{subject_id}/ocenki/")
async def create_ocenka(id: int, subject_id: int, ocenka: OcenkaCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Предмет не найден или не принадлежит студенту")

    # Создаем новую оценку
    new_ocenka = OcenkaDB(name=ocenka.name, data=ocenka.data, ocenka=ocenka.ocenka, predmet_id=subject.id)
    db.add(new_ocenka)
    db.commit()
    db.refresh(new_ocenka)

    return {"message": "Оценка добавлена", "ocenka": new_ocenka}


@router.get("/students/{id}/subjects/{subject_id}/ocenki/")
async def get_ocenki(id: int, subject_id: int, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Предмет не найден или не принадлежит студенту")

    # Получаем все оценки для данного предмета
    ocenki = db.query(OcenkaDB).filter(OcenkaDB.predmet_id == subject_id).all()

    return {"ocenki": ocenki}


@router.put("/students/{id}/subjects/{subject_id}/ocenki/{ocenka_id}/")
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
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    # Обновляем поля оценка
    db_ocenka.name = ocenka.name
    db_ocenka.data = ocenka.data
    db_ocenka.ocenka = ocenka.ocenka

    db.commit()  # Сохраняем изменения
    db.refresh(db_ocenka)  # Обновляем объект

    return {"message": "Оценка обновлена", "ocenka": db_ocenka}

@router.delete("/students/{id}/subjects/{subject_id}/ocenki/{ocenka_id}/")
async def delete_ocenka(id: int, subject_id: int, ocenka_id: int, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(UserDB).filter(UserDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    subject = db.query(PredmetDB).filter(PredmetDB.id == subject_id, PredmetDB.user_id == id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Предмет не найден или не принадлежит студенту")

    # Проверяем, существует ли оценка
    ocenka = db.query(OcenkaDB).filter(OcenkaDB.id == ocenka_id, OcenkaDB.predmet_id == subject_id).first()
    if not ocenka:
        raise HTTPException(status_code=404, detail="Оценка не найдена")

    db.delete(ocenka)
    db.commit()

    return {"message": "Оценка удалена"}
