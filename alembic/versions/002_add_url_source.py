"""Add URL source support: source_type, source_url, content_hash + html filetype

Revision ID: 002
Revises: 001
Create Date: 2026-04-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend filetype enum with 'html' (ALTER TYPE ... ADD VALUE must run
    # outside a transaction block in some Postgres versions; Alembic's
    # transactional DDL handles this for us on modern PG).
    op.execute("ALTER TYPE filetype ADD VALUE IF NOT EXISTS 'html'")

    # sourcetype enum — created as a fresh type.
    sourcetype = sa.Enum("file", "url", name="sourcetype")
    sourcetype.create(op.get_bind(), checkfirst=True)

    # kb_document: add source columns.
    op.add_column(
        "kb_document",
        sa.Column(
            "source_type",
            sourcetype,
            nullable=False,
            server_default="file",
        ),
    )
    op.add_column(
        "kb_document",
        sa.Column("source_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "kb_document",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )
    # Drop server default so future inserts must specify source_type explicitly.
    op.alter_column("kb_document", "source_type", server_default=None)

    op.create_index(
        "ix_kb_document_source_url",
        "kb_document",
        ["source_url"],
    )

    # kb_document_version: mirror URL source provenance per version.
    op.add_column(
        "kb_document_version",
        sa.Column("source_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "kb_document_version",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("kb_document_version", "content_hash")
    op.drop_column("kb_document_version", "source_url")

    op.drop_index("ix_kb_document_source_url", table_name="kb_document")
    op.drop_column("kb_document", "content_hash")
    op.drop_column("kb_document", "source_url")
    op.drop_column("kb_document", "source_type")

    op.execute("DROP TYPE IF EXISTS sourcetype")
    # Note: Postgres does not support removing enum values without recreating
    # the type; leaving 'html' in filetype is harmless on downgrade.
