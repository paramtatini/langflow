from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class SAPCredentials(SQLModel, table=True):  # type: ignore[call-arg]
    """Simple table to store SAP credentials as JSON."""

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    user_id: UUIDstr = Field(foreign_key="user.id", index=True)
    credentials_data: dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False), description="JSON data containing SAP credentials"
    )
    agents_data: dict[str, Any] | None = Field(
        sa_column=Column(JSON, nullable=True), description="JSON data containing SAP agents"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SAPCredentialsCreate(SQLModel):
    credentials_data: dict[str, Any]
    agents_data: dict[str, Any] | None = None


class SAPCredentialsRead(SQLModel):
    id: UUIDstr
    user_id: UUIDstr
    credentials_data: dict[str, Any]
    agents_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class SAPCredentialsUpdate(SQLModel):
    credentials_data: dict[str, Any] | None = None
    agents_data: dict[str, Any] | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
