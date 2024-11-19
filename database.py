from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Укажите вашу строку подключения к базе данных
DATABASE_URL = "sqlite:///./renovation.db"  # Для SQLite (замените на вашу СУБД, если требуется)

# Создаем движок подключения
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # Для SQLite
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()

# Функция для получения сессии базы данных (используется в Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
