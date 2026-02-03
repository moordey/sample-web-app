from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Схемы для пользователей
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль пользователя")

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Схемы для аутентификации
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LoginRequest(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль пользователя")

# Схемы для заметок
class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок заметки")
    content: str = Field(..., min_length=1, description="Содержимое заметки")

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Новый заголовок")
    content: Optional[str] = Field(None, min_length=1, description="Новое содержимое")

class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Схемы для ошибок
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Описание ошибки")
