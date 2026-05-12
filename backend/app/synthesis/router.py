from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.middleware import get_current_user_id
from app.synthesis.logic import generate_or_regenerate, get_formats, get_generated_text
from app.synthesis.models import (
    FormatInfo,
    FormatsResponse,
    GenerateRequest,
    GeneratedTextSchema,
)

router = APIRouter(prefix="/api/synthesis", tags=["synthesis"])


@router.get("/formats", response_model=FormatsResponse)
async def get_output_formats():
    """Get available output formats (no auth required)."""
    formats = get_formats()
    return FormatsResponse(formats=[FormatInfo(**f) for f in formats])


@router.post("/generate", status_code=status.HTTP_201_CREATED, response_model=GeneratedTextSchema)
async def post_generate(
    request: GenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate or regenerate text for a session."""
    generated = await generate_or_regenerate(
        db, request.session_id, user_id, request.output_format
    )
    await db.commit()
    return GeneratedTextSchema(
        session_id=generated.session_id,
        output_format=generated.output_format,
        generated_content=generated.generated_content,
        generation_count=generated.generation_count,
        created_at=generated.created_at,
        updated_at=generated.updated_at,
    )


@router.get("/{session_id}", response_model=GeneratedTextSchema)
async def get_session_text(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get generated text for a session."""
    generated = await get_generated_text(db, session_id, user_id)
    return GeneratedTextSchema(
        session_id=generated.session_id,
        output_format=generated.output_format,
        generated_content=generated.generated_content,
        generation_count=generated.generation_count,
        created_at=generated.created_at,
        updated_at=generated.updated_at,
    )
