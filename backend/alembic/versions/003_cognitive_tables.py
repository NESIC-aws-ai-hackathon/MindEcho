"""003 cognitive tables - context_questions, context_responses, free_text_inputs, emotion_candidates, emotion_selections

Revision ID: 003
Revises: 002
Create Date: 2026-05-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Context questions table
    op.create_table(
        "context_questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("generation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_order", sa.Integer, nullable=False),
        sa.Column("question_text", sa.String(500), nullable=False),
        sa.Column("choices", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_context_questions_session_id", "context_questions", ["session_id"])

    # Context responses table
    op.create_table(
        "context_responses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "question_id",
            sa.String(36),
            sa.ForeignKey("context_questions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("generation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selected_choice", sa.String(10), nullable=False),
        sa.Column("other_text", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_context_responses_session_id", "context_responses", ["session_id"])

    # Free text inputs table
    op.create_table(
        "free_text_inputs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("generation_sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("content", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Emotion candidates table
    op.create_table(
        "emotion_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("generation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("candidate_order", sa.Integer, nullable=False),
        sa.Column("emotion_label", sa.String(100), nullable=False),
        sa.Column("emotion_description", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_emotion_candidates_session_id", "emotion_candidates", ["session_id"])

    # Emotion selections table
    op.create_table(
        "emotion_selections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(36),
            sa.ForeignKey("emotion_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("generation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("candidate_id", "session_id", name="uq_emotion_selection"),
    )
    op.create_index("ix_emotion_selections_session_id", "emotion_selections", ["session_id"])


def downgrade() -> None:
    op.drop_table("emotion_selections")
    op.drop_table("emotion_candidates")
    op.drop_table("free_text_inputs")
    op.drop_table("context_responses")
    op.drop_table("context_questions")
