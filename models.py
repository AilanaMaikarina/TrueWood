from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Модель для таблицы пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="client")  # Роль пользователя (admin или client)


from sqlalchemy import Column, Integer, String, Float, Text

class RenovationPackage(Base):
    __tablename__ = "renovation_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # Название пакета
    description = Column(Text, nullable=False)  # Подробное описание
    price = Column(Integer, nullable=False)  # Цена
    photo_url = Column(String, nullable=True)  # URL для фото
    video_url = Column(String, nullable=True)  # URL для видео

