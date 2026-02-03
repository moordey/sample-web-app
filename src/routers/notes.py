from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List
from src.database import get_db
from src.schemas import NoteCreate, NoteUpdate, NoteResponse
from src.crud import get_notes_by_user, get_note, create_note, update_note, delete_note
from src.auth import get_current_user_from_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[NoteResponse], tags=["Notes"])
async def get_user_notes(
    skip: int = 0,
    limit: int = 100,
    token: str = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Получение списка заметок пользователя"""
    if not token:
        logger.warning("Attempt to get notes without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await get_current_user_from_token(db, token)
        notes = await get_notes_by_user(db, user.id, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(notes)} notes for user {user.username}")
        return notes
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notes for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting notes"
        )

@router.post("/", response_model=NoteResponse, tags=["Notes"])
async def create_user_note(
    note: NoteCreate,
    token: str = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Создание новой заметки"""
    if not token:
        logger.warning("Attempt to create note without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await get_current_user_from_token(db, token)
        db_note = await create_note(db, note, user.id)
        logger.info(f"Note created successfully for user {user.username}")
        return NoteResponse(
            id=db_note.id,
            title=db_note.title,
            content=db_note.content,
            user_id=db_note.user_id,
            created_at=db_note.created_at,
            updated_at=db_note.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating note for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the note"
        )

@router.get("/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def get_user_note(
    note_id: int,
    token: str = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Получение заметки по ID"""
    if not token:
        logger.warning("Attempt to get note without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await get_current_user_from_token(db, token)
        db_note = await get_note(db, note_id, user.id)
        if not db_note:
            logger.warning(f"Note {note_id} not found for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        logger.info(f"Note {note_id} retrieved successfully for user {user.username}")
        return NoteResponse(
            id=db_note.id,
            title=db_note.title,
            content=db_note.content,
            user_id=db_note.user_id,
            created_at=db_note.created_at,
            updated_at=db_note.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while getting the note"
        )

@router.put("/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def update_user_note(
    note_id: int,
    note_update: NoteUpdate,
    token: str = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Обновление заметки"""
    if not token:
        logger.warning("Attempt to update note without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await get_current_user_from_token(db, token)
        db_note = await update_note(db, note_id, note_update, user.id)
        if not db_note:
            logger.warning(f"Note {note_id} not found for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        logger.info(f"Note {note_id} updated successfully for user {user.username}")
        return NoteResponse(
            id=db_note.id,
            title=db_note.title,
            content=db_note.content,
            user_id=db_note.user_id,
            created_at=db_note.created_at,
            updated_at=db_note.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the note"
        )

@router.delete("/{note_id}", tags=["Notes"])
async def delete_user_note(
    note_id: int,
    token: str = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Удаление заметки"""
    if not token:
        logger.warning("Attempt to delete note without token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await get_current_user_from_token(db, token)
        success = await delete_note(db, note_id, user.id)
        if not success:
            logger.warning(f"Note {note_id} not found for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        logger.info(f"Note {note_id} deleted successfully for user {user.username}")
        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the note"
        )
