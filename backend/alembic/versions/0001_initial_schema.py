"""Initial schema migration — all core tables.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Token blacklist
    op.create_table(
        "token_blacklist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token", sa.String(512), unique=True, nullable=False, index=True),
        sa.Column("blacklisted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("zone", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("alert_type", sa.String(50)),
        sa.Column("risk_score", sa.Float),
        sa.Column("sensor_id", sa.String(100)),
        sa.Column("compound_hazard", sa.Boolean, server_default="false"),
        sa.Column("acknowledged_by", sa.String(80)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", sa.String(80)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Sensors
    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sensor_id", sa.String(100), nullable=False, index=True),
        sa.Column("sensor_type", sa.String(50), nullable=False),
        sa.Column("location", sa.String(100), nullable=False),
        sa.Column("zone", sa.String(100)),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(20)),
        sa.Column("status", sa.String(30), server_default="ok"),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_sensors_timestamp", "sensors", ["timestamp"])

    # Incident reports
    op.create_table(
        "incident_reports",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("incident_id", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("zone", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("risk_score", sa.Float),
        sa.Column("hazard_type", sa.String(50)),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("actions_taken", sa.Text),
        sa.Column("equipment_shutdown", sa.Text),
        sa.Column("evacuation_zones", sa.Text),
        sa.Column("personnel_count", sa.Integer),
        sa.Column("duration_estimate", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Permits
    op.create_table(
        "permits",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("permit_type", sa.String(50), nullable=False),
        sa.Column("work_description", sa.Text),
        sa.Column("zone", sa.String(100), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending"),
        sa.Column("requester", sa.String(80)),
        sa.Column("approved_by", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Shifts
    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("shift_name", sa.String(100), nullable=False),
        sa.Column("zone", sa.String(100)),
        sa.Column("supervisor", sa.String(80)),
        sa.Column("team", sa.Text),
        sa.Column("start_time", sa.DateTime(timezone=True)),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(30), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Equipment
    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("equipment_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("zone", sa.String(100)),
        sa.Column("status", sa.String(30), server_default="operational"),
        sa.Column("last_maintenance", sa.DateTime(timezone=True)),
        sa.Column("next_maintenance", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("equipment")
    op.drop_table("shifts")
    op.drop_table("permits")
    op.drop_table("incident_reports")
    op.drop_index("ix_sensors_timestamp", "sensors")
    op.drop_table("sensors")
    op.drop_table("alerts")
    op.drop_table("token_blacklist")
    op.drop_table("users")
