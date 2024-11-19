from pydantic import BaseModel
from typing import Optional

# Базовая схема для чтения данных
class UserBase(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

# Схема для регистрации пользователя (без id)
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "client"  # По умолчанию "client"

# Схема для логина пользователя
class UserLogin(BaseModel):
    email: str
    password: str

# Схема для ответа о пользователе
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        orm_mode = True

from pydantic import BaseModel

class RenovationPackageBase(BaseModel):
    name: str
    description: str
    price: int
    photo_url: Optional[str] = None  # Ссылка на фото
    video_url: Optional[str] = None  # Ссылка на видео

class RenovationPackageCreate(RenovationPackageBase):
    pass

class RenovationPackageResponse(RenovationPackageBase):
    id: int

    class Config:
        from_attributes = True

