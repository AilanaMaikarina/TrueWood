from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import Session, sessionmaker, declarative_base
import bcrypt
from starlette.staticfiles import StaticFiles
from models import User  # Only keep User model
from schemas import UserBase, UserCreate, UserLogin
from database import engine, SessionLocal
from auth import is_admin, get_current_user, create_access_token

# Инициализация FastAPI
from fastapi import FastAPI
from models import Base  # Импортируем Base
from database import engine  # Импортируем engine

app = FastAPI()
# Указываем FastAPI обслуживать статические файлы из папки static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт для получения данных пользователя
@app.get("/api/users/{user_id}", response_model=UserBase)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user
    return {"message": "User not found"}

# Регистрация пользователя
@app.post("/api/register/")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Проверка на существование пользователя с таким email
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Хэширование пароля
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password.decode('utf-8'),
        role=user.role if user.role else "client"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "role": new_user.role}

# Логин пользователя
@app.post("/api/login/")
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Генерация токена
    access_token = create_access_token(data={"user_id": db_user.id})
    return {"access_token": access_token, "token_type": "bearer"}

# Получение профиля пользователя
@app.get("/profile", response_model=UserBase)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

# Редактирование профиля пользователя
@app.put("/profile", response_model=UserBase)
async def update_profile(user: UserCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.name = user.name if user.name else db_user.name
    db_user.email = user.email if user.email else db_user.email
    if user.password:
        db_user.password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    db.commit()
    db.refresh(db_user)
    return db_user

# Удаление профиля пользователя
@app.delete("/profile")
async def delete_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return {"message": "Profile deleted successfully"}


from typing import List, Optional
from database import get_db
from schemas import RenovationPackageCreate, RenovationPackageResponse
from models import RenovationPackage

from fastapi import Depends, HTTPException, status




# Эндпоинт для получения списка пакетов ремонта
@app.get("/packages/", response_model=List[RenovationPackageResponse])
def get_packages(
        db: Session = Depends(get_db),
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        sort_by: Optional[str] = "name"  # Сортировка: "name" или "price"
):
    query = db.query(RenovationPackage)

    # Фильтрация по минимальной цене
    if price_min is not None:
        query = query.filter(RenovationPackage.price >= price_min)

    # Фильтрация по максимальной цене
    if price_max is not None:
        query = query.filter(RenovationPackage.price <= price_max)

    # Сортировка
    if sort_by == "price":
        query = query.order_by(RenovationPackage.price)
    else:
        query = query.order_by(RenovationPackage.name)

    packages = query.all()

    if not packages:
        raise HTTPException(status_code=404, detail="No renovation packages found")

    return packages


from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates




# Эндпоинт для добавления нового пакета ремонта (доступно только администратору)
@app.post("/packages/", response_model=RenovationPackageResponse)
def create_package(
        package: RenovationPackageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Получение текущего пользователя
):
    if current_user.role != "admin":  # Проверка роли
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add renovation packages"
        )

    db_package = RenovationPackage(**package.dict())
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    return db_package


# Эндпоинт для редактирования пакета ремонта (доступно только администратору)
@app.put("/packages/{package_id}", response_model=RenovationPackageResponse)
def update_package(
        package_id: int,
        package: RenovationPackageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Получение текущего пользователя
):
    if current_user.role != "admin":  # Проверка роли
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can edit renovation packages"
        )

    db_package = db.query(RenovationPackage).filter(RenovationPackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Renovation package not found")

    db_package.name = package.name
    db_package.description = package.description
    db_package.price = package.price

    db.commit()
    db.refresh(db_package)
    return db_package


@app.put("/about_page/{package_id}", response_model=RenovationPackageResponse)
def update_package(
        package_id: int,
        package: RenovationPackageCreate,
        db: Session = Depends(get_db)
):
    db_package = db.query(RenovationPackage).filter(RenovationPackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Renovation package not found")

    db_package.name = package.name
    db_package.description = package.description
    db_package.price = package.price

    db.commit()
    db.refresh(db_package)
    return db_package


# Эндпоинт для удаления пакета ремонта (доступно только администратору)
@app.delete("/packages/{package_id}")
def delete_package(
        package_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Получение текущего пользователя
):
    if current_user.role != "admin":  # Проверка роли
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete renovation packages"
        )

    db_package = db.query(RenovationPackage).filter(RenovationPackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Renovation package not found")

    db.delete(db_package)
    db.commit()
    return {"message": "Renovation package deleted successfully"}



# Получение всех пакетов для админа
@app.get("/admin/packages/", response_model=List[RenovationPackageResponse])
def admin_get_packages(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access this")

    return db.query(RenovationPackage).all()


# Добавление нового пакета
@app.post("/admin/packages/", response_model=RenovationPackageResponse)
def admin_create_package(
        package: RenovationPackageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create packages")

    new_package = RenovationPackage(**package.dict())
    db.add(new_package)
    db.commit()
    db.refresh(new_package)
    return new_package


# Редактирование пакета
@app.put("/admin/packages/{package_id}", response_model=RenovationPackageResponse)
def admin_update_package(
        package_id: int,
        package: RenovationPackageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update packages")

    db_package = db.query(RenovationPackage).filter(RenovationPackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")

    db_package.name = package.name
    db_package.description = package.description
    db_package.price = package.price

    db.commit()
    db.refresh(db_package)
    return db_package


# Удаление пакета
@app.delete("/admin/packages/{package_id}")
def admin_delete_package(
        package_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete packages")

    db_package = db.query(RenovationPackage).filter(RenovationPackage.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")

    db.delete(db_package)
    db.commit()
    return {"message": "Package deleted successfully"}