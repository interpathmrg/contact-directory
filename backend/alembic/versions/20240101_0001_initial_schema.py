"""Initial schema: societies, roles, contacts, user_roles + seed data

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tabla: societies
    # ------------------------------------------------------------------
    op.create_table(
        "societies",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ------------------------------------------------------------------
    # Tabla: roles
    # ------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ------------------------------------------------------------------
    # Tabla: contacts
    # ------------------------------------------------------------------
    op.create_table(
        "contacts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("apellido", sa.String(100), nullable=False),
        sa.Column("empresa", sa.String(200), nullable=True),
        sa.Column("cargo", sa.String(100), nullable=True),
        sa.Column("puesto", sa.String(200), nullable=True),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("telefono", sa.String(20), nullable=True),
        sa.Column("celular", sa.String(20), nullable=True),
        sa.Column("email", sa.String(150), nullable=True),
        sa.Column("nombre_contacto_interno", sa.String(200), nullable=True),
        sa.Column("email_contacto_interno", sa.String(150), nullable=True),
        sa.Column("telefono_contacto_interno", sa.String(20), nullable=True),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("sociedad_id", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.String(150), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["sociedad_id"], ["societies.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Índices de contacts
    op.create_index("ix_contacts_email", "contacts", ["email"], unique=True)
    op.create_index(
        "ix_contacts_nombre_apellido", "contacts", ["nombre", "apellido"]
    )
    op.create_index(
        "ix_contacts_sociedad_active", "contacts", ["sociedad_id", "is_active"]
    )
    op.create_index("ix_contacts_empresa", "contacts", ["empresa"])

    # Índice GIN para búsqueda full-text en español
    op.execute(
        """
        CREATE INDEX ix_contacts_fts ON contacts
        USING gin(
            to_tsvector(
                'spanish',
                coalesce(nombre, '') || ' ' ||
                coalesce(apellido, '') || ' ' ||
                coalesce(empresa, '') || ' ' ||
                coalesce(email, '')
            )
        )
        """
    )

    # Trigger para actualizar updated_at automáticamente
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_contacts_updated_at
        BEFORE UPDATE ON contacts
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
        """
    )

    # ------------------------------------------------------------------
    # Tabla: user_roles
    # ------------------------------------------------------------------
    op.create_table(
        "user_roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_email", sa.String(150), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by", sa.String(150), nullable=True),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_roles_user_email", "user_roles", ["user_email"], unique=True
    )

    # ------------------------------------------------------------------
    # Seed data: societies
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO societies (name) VALUES
            ('EGE HAINA'),
            ('SIBA'),
            ('Trelia')
        """
    )

    # ------------------------------------------------------------------
    # Seed data: roles
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO roles (name, description, permissions) VALUES
        (
            'ADMIN',
            'Administrador con acceso completo',
            '{"contacts": ["read", "write", "delete"], "import": true, "export": true, "labels": true, "admin": true}'::jsonb
        ),
        (
            'VIEWER',
            'Usuario de solo lectura con acceso a etiquetas',
            '{"contacts": ["read"], "import": false, "export": false, "labels": true, "admin": false}'::jsonb
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_contacts_updated_at ON contacts")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")
    op.drop_index("ix_user_roles_user_email", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_index("ix_contacts_fts", table_name="contacts")
    op.drop_index("ix_contacts_empresa", table_name="contacts")
    op.drop_index("ix_contacts_sociedad_active", table_name="contacts")
    op.drop_index("ix_contacts_nombre_apellido", table_name="contacts")
    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_table("contacts")
    op.drop_table("roles")
    op.drop_table("societies")
