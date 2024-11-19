from jose import jwt, JWTError
from fastapi import HTTPException, Security, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from pydantic import ValidationError
from starlette import status
from models import User
from database import SessionLocal
import jwt

# Секретный ключ для JWT
SECRET_KEY = "aitu"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Функция для генерации JWT токена
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Функция для получения текущего пользователя из токена
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return {"id": user_id}  # Возвращаем объект пользователя или ID
    except (JWTError, ValidationError):
        raise credentials_exception

# Функция для проверки, является ли пользователь администратором
def is_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You don't have enough permissions")
    return current_user
