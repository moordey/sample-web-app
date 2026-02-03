from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.database import get_db
from src.schemas import UserCreate, LoginRequest, TokenResponse, UserResponse
from src.auth import create_user, authenticate_user, create_token_for_user, invalidate_token, get_current_user_from_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserResponse, tags=["Authentication"])
async def register_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    """Регистрация нового пользователя"""
    try:
        db_user = await create_user(db, user)
        logger.info(f"User {user.username} registered successfully")
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            created_at=db_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user {user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )

@router.post("/login", response_model=TokenResponse, tags=["Authentication"])
async def login_user(login_data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Аутентификация пользователя и получение токена"""
    try:
        user = await authenticate_user(db, login_data.username, login_data.password)
        if not user:
            logger.warning(f"Failed login attempt for username: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_response = await create_token_for_user(db, user.id)
        logger.info(f"User {user.username} logged in successfully")
        return token_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login for username {login_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication"
        )

@router.post("/logout", tags=["Authentication"])
async def logout_user(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Выход пользователя (инвалидация токена)"""
    try:
        success = await invalidate_token(db, token)
        if not success:
            logger.warning(f"Logout attempt with invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        logger.info("User logged out successfully")
        return {"message": "Successfully logged out"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )

@router.get("/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Получение информации о текущем пользователе"""
    try:
        user = await get_current_user_from_token(db, token)
        logger.info(f"User info requested for {user.username}")
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting user information"
        )
