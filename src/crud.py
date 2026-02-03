from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from .database import User, Note
from .schemas import UserCreate, NoteCreate, NoteUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# CRUD операции для пользователей
async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Получение пользователя по ID"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by id {user_id}: {e}")
        return None

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Получение пользователя по username"""
    try:
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by username {username}: {e}")
        return None

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Получение списка пользователей"""
    try:
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

# CRUD операции для заметок
async def get_notes_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Note]:
    """Получение всех заметок пользователя"""
    try:
        result = await db.execute(
            select(Note)
            .where(Note.user_id == user_id)
            .offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting notes for user {user_id}: {e}")
        return []

async def get_note(db: AsyncSession, note_id: int, user_id: int) -> Optional[Note]:
    """Получение заметки по ID (только для владельца)"""
    try:
        result = await db.execute(
            select(Note)
            .where(Note.id == note_id, Note.user_id == user_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting note {note_id} for user {user_id}: {e}")
        return None

async def create_note(db: AsyncSession, note: NoteCreate, user_id: int) -> Note:
    """Создание новой заметки"""
    try:
        db_note = Note(
            title=note.title,
            content=note.content,
            user_id=user_id
        )
        db.add(db_note)
        await db.commit()
        await db.refresh(db_note)
        logger.info(f"Note created successfully for user {user_id}")
        return db_note
    except Exception as e:
        logger.error(f"Error creating note for user {user_id}: {e}")
        raise

async def update_note(db: AsyncSession, note_id: int, note_update: NoteUpdate, user_id: int) -> Optional[Note]:
    """Обновление заметки (только для владельца)"""
    try:
        # Сначала проверяем, существует ли заметка и принадлежит ли пользователю
        db_note = await get_note(db, note_id, user_id)
        if not db_note:
            logger.warning(f"Note {note_id} not found for user {user_id}")
            return None

        # Обновляем поля, если они предоставлены
        if note_update.title is not None:
            db_note.title = note_update.title
        if note_update.content is not None:
            db_note.content = note_update.content

        await db.commit()
        await db.refresh(db_note)
        logger.info(f"Note {note_id} updated successfully for user {user_id}")
        return db_note
    except Exception as e:
        logger.error(f"Error updating note {note_id} for user {user_id}: {e}")
        raise

async def delete_note(db: AsyncSession, note_id: int, user_id: int) -> bool:
    """Удаление заметки (только для владельца)"""
    try:
        # Сначала проверяем, существует ли заметка и принадлежит ли пользователю
        db_note = await get_note(db, note_id, user_id)
        if not db_note:
            logger.warning(f"Note {note_id} not found for user {user_id}")
            return False

        await db.delete(db_note)
        await db.commit()
        logger.info(f"Note {note_id} deleted successfully for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting note {note_id} for user {user_id}: {e}")
        raise
