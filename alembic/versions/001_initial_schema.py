"""Initial schema - knowledge base, document, chunk, task tables

Revision ID: 001
Revises:
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("document_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "kb_document",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("knowledge_base_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_type", sa.Enum("pdf", "txt", "docx", name="filetype"), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "parsing", "chunking", "embedding", "ready", "failed", name="documentstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_base.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_kb_document_kb_id", "kb_document", ["knowledge_base_id"])

    op.create_table(
        "kb_document_version",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["kb_document.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_kb_doc_version_doc_id", "kb_document_version", ["document_id"])

    op.create_table(
        "kb_chunk",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["kb_document.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_kb_chunk_doc_id", "kb_chunk", ["document_id"])

    op.create_table(
        "task",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("task_type", sa.Enum("document_ingest", name="tasktype"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "success", "failed", name="taskstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["kb_document.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_task_doc_id", "task", ["document_id"])
    op.create_index("ix_task_status", "task", ["status"])


def downgrade() -> None:
    op.drop_table("task")
    op.drop_table("kb_chunk")
    op.drop_table("kb_document_version")
    op.drop_table("kb_document")
    op.drop_table("knowledge_base")
    op.execute("DROP TYPE IF EXISTS filetype")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS tasktype")
    op.execute("DROP TYPE IF EXISTS taskstatus")
