"""Reusable SQLAlchemy column factories for entity definitions.

These helpers keep enum/JSON column declarations consistent and portable
across SQLite, MySQL, and PostgreSQL (no provider-native ENUM types).
"""
from __future__ import annotations
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String


def enum_column(
    enum_cls: type[Enum],
    *,
    nullable: bool = False,
    index: bool = False,
    length: int = 32,
) -> Column[Any]:
    """Build a portable, value-stored enum column.

    Stores the enum *value* (not its name) as a VARCHAR so the schema is
    portable and human-readable, while still round-tripping to enum members.
    """
    return Column(
        SAEnum(
            enum_cls,
            native_enum=False,
            length=length,
            validate_strings=True,
            values_callable=lambda e: [str(member.value) for member in e],
        ),
        nullable=nullable,
        index=index,
    )


def json_column(*, nullable: bool = False, index: bool = False) -> Column[Any]:
    """Build a JSON column for structured config / metadata fields."""
    return Column(JSON, nullable=nullable, index=index)


def string_column(
    length: int,
    *,
    nullable: bool = False,
    index: bool = False,
    unique: bool = False,
) -> Column[Any]:
    """Build a bounded VARCHAR column (MySQL requires explicit lengths)."""
    return Column(String(length), nullable=nullable, index=index, unique=unique)
