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

@router.post("/cteachers/")
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

@router.get("/gteachers/")
async def get_all_teachers(db: Session = Depends(get_db)):
    # Получаем всех пользователей из базы данных
    users = db.query(TeacherDB).all()
    
    # Преобразуем пользователей в формат, подходящий для возврата
    return {"message": "Учителя получены", "users": users}

@router.delete("/dteachers/{id}/")
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


@router.get("/gteachers/{id}/")
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

@router.put("/pteachers/{id}/")
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





















@router.get("/teachers/{id}/group/")
async def get_teacher_groups(id: int, db: Session = Depends(get_db)):
    # Ищем студента
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Получаем предметы студента
    groups = db.query(GroupDB).filter(GroupDB.teacher_id == id).all()
    
    return {"message": "Группы получены","group": groups}

class GroupCreate(BaseModel):
    name: str


@router.post("/teachers/{id}/groups/")
async def add_teacher_group(id: int, group: GroupCreate, db: Session = Depends(get_db)):

    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Создаем предмет
    new_group = GroupDB(
        name=group.name,
        teacher_id=id
    )

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return {"message": "Группа добавлена", "group": new_group}

class GroupUpdate(BaseModel):
    name: Optional[str] = None

@router.put("/teachers/{id}/groups/{group_id}/")
async def update_group(id: int, group_id: int, group_data: GroupUpdate, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    group = db.query(GroupDB).filter(GroupDB.id == group_id, GroupDB.teacher_id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена или не принадлежит студенту")

    # Обновляем только переданные поля
    if group_data.name is not None:
        group.name = group_data.name


    db.commit()
    db.refresh(group)

    return {"message": "Группы обновлены", "group": group}

@router.delete("/teachers/{id}/groups/{group_id}/")
async def delete_group(id: int, group_id: int, db: Session = Depends(get_db)):
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    group = db.query(GroupDB).filter(GroupDB.id == group_id, GroupDB.teacher_id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найден или не прнадлежит учителю")

    db.delete(group)
    db.commit()

    return {"message": "Группа удалена"}





















@router.get("/teachers/{id}/classwork/")
async def get_teacher_classryks(id: int, db: Session = Depends(get_db)):
    # Ищем студента
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Получаем предметы студента
    classryks = db.query(ClassRykDB).filter(ClassRykDB.teacher_id == id).all()
    
    return {"message": "Классное руководство получены","classryk": classryks}

class classryksCreate(BaseModel):
    name: str


@router.post("/teachers/{id}/classwork/")
async def add_teacher_classryks(id: int, classryks: classryksCreate, db: Session = Depends(get_db)):

    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    # Создаем предмет
    new_classryks = ClassRykDB(
        name=classryks.name,
        teacher_id=id
    )

    db.add(new_classryks)
    db.commit()
    db.refresh(new_classryks)

    return {"message": "Классное руководство добавлено", "classryks": new_classryks}

class classryksUpdate(BaseModel):
    name: Optional[str] = None

@router.put("/teachers/{id}/classworks/{classryks_id}/")
async def update_classryks(id: int, classryks_id: int, classryks_data: classryksUpdate, db: Session = Depends(get_db)):
    # Проверяем, существует ли студент
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Проверяем, существует ли предмет и принадлежит ли он студенту
    classryk = db.query(ClassRykDB).filter(ClassRykDB.id == classryks_id, ClassRykDB.teacher_id == id).first()
    if not classryk:
        raise HTTPException(status_code=404, detail="Классное руководство не найдено или не принадлежит учителю")

    # Обновляем только переданные поля
    if classryks_data.name is not None:
        classryk.name = classryks_data.name


    db.commit()
    db.refresh(classryk)

    return {"message": "Группы обновлены", "classryks": classryk}

@router.delete("/teachers/{id}/classworks/{classryks_id}/")
async def delete_classryks(id: int, classryks_id: int, db: Session = Depends(get_db)):
    user = db.query(TeacherDB).filter(TeacherDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Учитель не найден")

    classryks = db.query(ClassRykDB).filter(ClassRykDB.id == classryks_id, ClassRykDB.teacher_id == id).first()
    if not classryks:
        raise HTTPException(status_code=404, detail="Классное руководство не найдено или не прнадлежит учителю")

    db.delete(classryks)
    db.commit()

    return {"message": "Классное руководство удалено"}

