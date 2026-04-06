"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_active", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "programs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("university_name", sa.Text(), nullable=False),
        sa.Column("program_name", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("field", sa.Text(), nullable=False),
        sa.Column("degree_type", sa.Text(), nullable=False),
        sa.Column("min_gpa", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_gpa", sa.Float(), nullable=True),
        sa.Column("min_ielts", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_ielts", sa.Float(), nullable=True),
        sa.Column("tuition_year", sa.Integer(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("requirements_text", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("embedding", sa.Text(), nullable=True),  # stored as vector via pgvector
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    # Change embedding column to vector type after table creation
    op.execute("ALTER TABLE programs ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536)")

    op.create_table(
        "user_deadlines",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=False),
        sa.Column("notified_30", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notified_7", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notified_1", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "checklist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_name", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "document_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("degree_type", sa.Text(), nullable=False),
        sa.Column("item_name", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )

    # Seed document templates
    op.execute("""
        INSERT INTO document_templates (degree_type, item_name, hint, order_index) VALUES
        ('all', 'Диплом + транскрипт', 'Нотариально заверенный перевод', 1),
        ('all', 'CV / резюме', 'На английском языке, 1–2 страницы', 2),
        ('all', 'IELTS / TOEFL', 'Оригинал сертификата', 3),
        ('all', 'Загранпаспорт', 'Скан всех страниц', 4),
        ('master', 'Мотивационное письмо', 'Statement of purpose, 500–1000 слов', 5),
        ('master', 'Рекомендательное письмо 1', 'От преподавателя или научного руководителя', 6),
        ('master', 'Рекомендательное письмо 2', 'От работодателя или второго преподавателя', 7),
        ('mba', 'Statement of Purpose', 'Фокус на карьерных целях', 5),
        ('mba', 'GMAT / GRE', 'Сертификат теста', 6),
        ('mba', 'Рекомендательное письмо 1', '', 7),
        ('mba', 'Рекомендательное письмо 2', '', 8),
        ('mba', 'Рекомендательное письмо 3', '', 9),
        ('phd', 'Research Proposal', '3–5 страниц с описанием исследования', 5),
        ('phd', 'Мотивационное письмо', '', 6),
        ('phd', 'Рекомендательное письмо 1', '', 7),
        ('phd', 'Рекомендательное письмо 2', '', 8),
        ('phd', 'Публикации (при наличии)', 'Статьи, препринты, конференции', 9)
    """)


def downgrade() -> None:
    op.drop_table("document_templates")
    op.drop_table("checklist_items")
    op.drop_table("user_deadlines")
    op.drop_table("programs")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
