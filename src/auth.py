from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from .database import get_db, User, Token, TOKEN_EXPIRE_HOURS, SECRET_KEY
from .schemas import UserCreate, LoginRequest, TokenResponse
import secrets
import logging

logger = logging.getLogger(__name__)

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Получение пользователя по username"""
    try:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by username {username}: {e}")
        return None

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Получение пользователя по email"""
    try:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {e}")
        return None

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Создание нового пользователя"""
    try:
        # Проверяем, существует ли пользователь с таким username
        existing_user = await get_user_by_username(db, user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Проверяем, существует ли пользователь с таким email
        existing_email = await get_user_by_email(db, user.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Создаем нового пользователя
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User {user.username} created successfully")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user {user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Аутентификация пользователя"""
    try:
        user = await get_user_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for username: {username}")
            return None
        logger.info(f"User {username} authenticated successfully")
        return user
    except Exception as e:
        logger.error(f"Error authenticating user {username}: {e}")
        return None

async def create_token_for_user(db: AsyncSession, user_id: int) -> TokenResponse:
    """Создание токена для пользователя"""
    try:
        # Генерируем уникальный токен
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS)

        # Сохраняем токен в базе данных
        db_token = Token(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(db_token)
        await db.commit()
        await db.refresh(db_token)

        logger.info(f"Token created for user_id: {user_id}")
        return TokenResponse(
            access_token=token,
            expires_at=expires_at
        )
    except Exception as e:
        logger.error(f"Error creating token for user_id {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the token"
        )

async def get_token_by_value(db: AsyncSession, token: str) -> Optional[Token]:
    """Получение токена по значению"""
    try:
        result = await db.execute(select(Token).where(Token.token == token))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting token by value: {e}")
        return None

async def invalidate_token(db: AsyncSession, token: str) -> bool:
    """Инвалидация токена"""
    try:
        db_token = await get_token_by_value(db, token)
        if db_token:
            db_token.is_active = False
            await db.commit()
            logger.info(f"Token invalidated: {token}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error invalidating token: {e}")
        return False

async def get_current_user_from_token(db: AsyncSession, token: str) -> User:
    """Получение текущего пользователя по токену"""
    try:
        # Проверяем, существует ли токен в базе данных
        db_token = await get_token_by_value(db, token)
        if not db_token:
            logger.warning(f"Invalid token used: {token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем, активен ли токен
        if not db_token.is_active:
            logger.warning(f"Attempted to use invalidated token: {token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем, не истек ли токен
        if datetime.utcnow() > db_token.expires_at:
            await invalidate_token(db, token)
            logger.warning(f"Expired token used: {token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Получаем пользователя
        result = await db.execute(select(User).where(User.id == db_token.user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User not found for token: {token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while validating the token"
        )
