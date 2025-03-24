from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session, sessionmaker  # Импорт sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
SQLALCHEMY_DATABASE_URL = "sqlite:///./kkts.db" 
Base = declarative_base()  # Здесь 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db  # Возвращаем сессию для использования в зависимостях
    finally:
        db.close()

class PredmetDB(Base):
    __tablename__ = "predmeti"
    
    id = Column(Integer, primary_key=True, index=True)
    color = Column(String, index=True)
    predmet = Column(String, index=True)
    attes = Column(String)
    srbal = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    ocenki = relationship("OcenkaDB", back_populates="predmet")  # связь с OcenkaDB

class OcenkaDB(Base):
    __tablename__ = "ocenki"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    data = Column(String)
    ocenka = Column(String)
    predmet_id = Column(Integer, ForeignKey("predmeti.id"))  # внешний ключ на PredmetDB
    
    predmet = relationship("PredmetDB", back_populates="ocenki")  #

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    fullname = Column(String)
    role = Column(String)
    login = Column(String, unique=True, index=True)
    password = Column(String)
    gmail = Column(String, unique=True, index=True)
    vk = Column(String, unique=True, index=True)
    group = Column(String)

    predmeti = relationship("PredmetDB", backref="user")













class TeacherDB(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    fullname = Column(String)
    role = Column(String)
    login = Column(String, unique=True, index=True)
    password = Column(String)
    gmail = Column(String, unique=True, index=True)
    vk = Column(String, unique=True, index=True)

    # Уникальные backref для разных связей
    group = relationship("GroupDB", backref="group_teachers")  # связь с группой
    classryk = relationship("ClassRykDB", backref="classryk_teachers")  # связь с классами

class GroupDB(Base):
    __tablename__ = "group"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))


class ClassRykDB(Base):
    __tablename__ = "classryk"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))













class LessonsDB(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String)  # Оставляем строкой, как ты просил

    # Связь один ко многим: один урок - много сессий
    sessions = relationship("SessionDB", back_populates="lesson")


class SessionDB(Base):
    __tablename__ = "session"
    
    id = Column(Integer, primary_key=True, index=True)
    group = Column(String)  # Можно сделать ForeignKey на таблицу групп
    teacher = Column(String)  # Можно сделать ForeignKey на таблицу учителей
    teacher2 = Column(String, nullable=True)  # Второй учитель не всегда есть
    start = Column(String)  
    end = Column(String)
    clases = Column(String)  
    adress = Column(String)
    color = Column(String)

    # Внешний ключ для связи с `LessonsDB`
    lessons_id = Column(Integer, ForeignKey("lessons.id"))
    lesson = relationship("LessonsDB", back_populates="sessions")
