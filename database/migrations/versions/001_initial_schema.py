"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2023-10-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String, primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('username', sa.String, unique=True, nullable=False),
        sa.Column('email', sa.String, unique=True, nullable=False),
        sa.Column('hashed_password', sa.String, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)
    )

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String, primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column('last_active', sa.TIMESTAMP, nullable=False)
    )

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String, primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String, sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String, nullable=False),
        sa.Column('file_type', sa.String, nullable=False),
        sa.Column('file_path', sa.String, nullable=False),
        sa.Column('status', sa.String, nullable=False),
        sa.Column('uploaded_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column('processed_at', sa.TIMESTAMP, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True)
    )

    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String, primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('document_id', sa.String, sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String, sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('chunk_text', sa.Text, nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('metadata', sa.JSON, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)
    )

    # Create queries table
    op.create_table(
        'queries',
        sa.Column('id', sa.String, primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String, sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.Text, nullable=False),
        sa.Column('answer', sa.Text, nullable=False),
        sa.Column('sources', sa.JSON, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)
    )

    # Create indexes
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_queries_user_id', 'queries', ['user_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_queries_user_id', table_name='queries')
    op.drop_index('idx_document_chunks_document_id', table_name='document_chunks')
    op.drop_index('idx_documents_user_id', table_name='documents')

    # Drop tables
    op.drop_table('queries')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('sessions')
    op.drop_table('users')

    # Disable pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector;")