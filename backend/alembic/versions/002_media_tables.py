"""002 media tables - media_files, image_analysis_results, music_analysis_results

Revision ID: 002
Revises: 001
Create Date: 2026-05-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Media files table
    op.create_table(
        "media_files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("generation_sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("media_type", sa.String(20), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_media_files_session_id", "media_files", ["session_id"])
    op.create_index("ix_media_files_user_id", "media_files", ["user_id"])

    # Image analysis results table
    op.create_table(
        "image_analysis_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "media_id",
            sa.String(36),
            sa.ForeignKey("media_files.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("colors", sa.JSON, nullable=False),
        sa.Column("composition", sa.String(500), nullable=False),
        sa.Column("mood", sa.String(200), nullable=False),
        sa.Column("subjects", sa.JSON, nullable=False),
        sa.Column("atmosphere", sa.String(500), nullable=False),
        sa.Column("texture", sa.String(300), nullable=False),
        sa.Column("light_direction", sa.String(200), nullable=False),
        sa.Column("emotional_impression", sa.String(500), nullable=False),
        sa.Column("image_category", sa.String(100), nullable=False),
        sa.Column("style_characteristics", sa.String(500), nullable=False),
        sa.Column("raw_response", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Music analysis results table
    op.create_table(
        "music_analysis_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "media_id",
            sa.String(36),
            sa.ForeignKey("media_files.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("artist", sa.String(255), nullable=True),
        sa.Column("album", sa.String(255), nullable=True),
        sa.Column("genre", sa.String(100), nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("bpm", sa.Integer, nullable=True),
        sa.Column("key", sa.String(50), nullable=True),
        sa.Column("chord_progression", sa.String(500), nullable=True),
        sa.Column("rhythm", sa.String(200), nullable=False),
        sa.Column("tempo", sa.String(100), nullable=False),
        sa.Column("mood", sa.String(200), nullable=False),
        sa.Column("energy_level", sa.String(100), nullable=False),
        sa.Column("emotional_impression", sa.String(500), nullable=False),
        sa.Column("raw_response", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("music_analysis_results")
    op.drop_table("image_analysis_results")
    op.drop_table("media_files")
