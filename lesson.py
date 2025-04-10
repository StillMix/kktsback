from sqlalchemy.orm import Session
from fastapi import HTTPException, APIRouter, Depends
from db import LessonsDB, SessionDB, Base, get_db
from pydantic import BaseModel 
from typing import Optional
from websocket import notify_racp_group


router = APIRouter()


class Item(BaseModel):
    date: str


@router.post("/lesson/")
async def register_teacher(item: Item, db: Session = Depends(get_db)):
    lesson = LessonsDB(
        date=item.date, 
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return {"message": "День успешно зарегистрирован", "lesson": item}


@router.get("/lesson/")
async def get_all_lesson(db: Session = Depends(get_db)):
    # Получаем всех пользователей из базы данных
    lessons = db.query(LessonsDB).all()
    
    # Преобразуем пользователей в формат, подходящий для возврата
    return {"message": "Распиние получено", "lessons": lessons}


@router.get("/lesson/{id}/")
async def get_one_teacher(id: int, db: Session = Depends(get_db)):
    # Ищем студента по id
    lessons = db.query(LessonsDB).filter(LessonsDB.id == id).first()

    # Если студент не найден, возвращаем ошибку
    if not lessons:
        raise HTTPException(status_code=404, detail="День не найден")

    # Возвращаем данные студента
    return {"message": "День получен", "lessons": lessons}










@router.get("/lesson/{id}/session/")
async def get_teacher_session(id: int, db: Session = Depends(get_db)):
    user = db.query(LessonsDB).filter(LessonsDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="День не найден")
    session = db.query(SessionDB).filter(SessionDB.lessons_id == id).all()
    
    return {"message": "Пары получены","session": session}

class sessionCreate(BaseModel):
    name:str
    group: str  # Это поле может быть пустым
    teacher: str
    teacher2: Optional[str] = None
    start: str
    end: str
    clases: str  
    adress: str
    color: str


@router.post("/lesson/{id}/session/")
async def add_teacher_session(id: int, session: sessionCreate, db: Session = Depends(get_db)):

    user = db.query(LessonsDB).filter(LessonsDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="День не найден")

    # Создаем предмет
    new_session = SessionDB(
        name = session.name,
        group =session.group,
        teacher =session.teacher,
        teacher2 =session.teacher2,
        start =session.start,
        end =session.end,
        clases =session.clases, 
        adress =session.adress,
        color =session.color,
        lessons_id=id
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    await notify_racp_group(session.group, f"newlesson:{session.group}")
    await notify_racp_group(session.teacher, f"newlessonteacher:{session.teacher}")
    await notify_racp_group(session.teacher2, f"newlessonteacher2:{session.teacher2}")
    return {"message": "Пара добавлена", "session": new_session}

class sessionUpdate(BaseModel):
    name: Optional[str] = None
    group: Optional[str] = None
    teacher: Optional[str] = None
    teacher2: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    clases: Optional[str] = None 
    adress: Optional[str] = None
    color: Optional[str] = None

@router.put("/lesson/{id}/session/{session_id}/")
async def update_session(id: int, session_id: int, session_data: sessionUpdate, db: Session = Depends(get_db)):
    user = db.query(LessonsDB).filter(LessonsDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="День не найден")

    session = db.query(SessionDB).filter(SessionDB.id == session_id, SessionDB.lessons_id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Пара не найдена или не принадлежит дню")

    # Обновляем только переданные поля
    if session_data.name is not None:
        session.name = session_data.name
    if session_data.group is not None:
        session.group = session_data.group
    if session_data.teacher is not None:
        session.teacher = session_data.teacher
    if session_data.teacher2 is not None:
        session.teacher2 = session_data.teacher2
    if session_data.start is not None:
        session.start = session_data.start
    if session_data.end is not None:
        session.end = session_data.end
    if session_data.clases is not None:
        session.clases = session_data.clases
    if session_data.adress is not None:
        session.adress = session_data.adress
    if session_data.color is not None:
        session.color = session_data.color



    db.commit()
    db.refresh(session)
    await notify_racp_group(session.group, f"updatelesson:{session.group}")
    return {"message": "Пары обновлены", "session": session}

@router.delete("/lesson/{id}/session/{session_id}/")
async def delete_session(id: int, session_id: int, db: Session = Depends(get_db)):
    user = db.query(LessonsDB).filter(LessonsDB.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="День не найден")

    session = db.query(SessionDB).filter(SessionDB.id == session_id, SessionDB.lessons_id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Пара не найден или не прнадлежит дню")

    db.delete(session)
    db.commit()
    await notify_racp_group(session.group, f"dellesson:{session.group}")
    return {"message": "Пара удалена"}