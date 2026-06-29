"""Generic repository implementing reusable CRUD over a SQLModel entity.

Repositories are the only place that talks to the ORM. They are constructed
with an active :class:`~sqlalchemy.orm.Session` (injected by the service layer)
and never manage transactions themselves — commit/rollback is owned by the
caller's unit of work (``session_scope`` / ``get_db``).
"""
from __future__ import annotations
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlmodel import SQLModel, select

from app.core.exceptions import NotFoundError

TEntity = TypeVar("TEntity", bound=SQLModel)


class BaseRepository(Generic[TEntity]):
    """Reusable CRUD operations for a single entity type.

    Subclasses set the :attr:`model` class attribute and may add
    entity-specific query methods.
    """

    model: type[TEntity]

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get(self, entity_id: int) -> TEntity | None:
        """Return an entity by primary key, or ``None`` if absent."""
        return self.session.get(self.model, entity_id)

    def get_or_404(self, entity_id: int) -> TEntity:
        """Return an entity by primary key or raise :class:`NotFoundError`."""
        obj = self.get(entity_id)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} with id={entity_id} not found.")
        return obj

    def get_by(self, **filters: Any) -> TEntity | None:
        """Return the first entity matching the given equality filters."""
        stmt = select(self.model).filter_by(**filters).limit(1)
        return self.session.exec(stmt).first()

    def get_by_or_404(self, **filters: Any) -> TEntity:
        obj = self.get_by(**filters)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} matching {filters} not found.")
        return obj

    def list(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
        order_by: Any | None = None,
        filters: dict[str, Any] | None = None,
        expressions: Sequence[Any] | None = None,
    ) -> list[TEntity]:
        """Return entities matching the given filters with optional paging.

        ``filters`` are simple column equality pairs; ``expressions`` are raw
        SQLAlchemy boolean clauses for ranges / OR / LIKE conditions.
        """
        stmt = select(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        if expressions:
            for expr in expressions:
                stmt = stmt.where(expr)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.exec(stmt).all())

    def paginate(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: Any | None = None,
        filters: dict[str, Any] | None = None,
        expressions: Sequence[Any] | None = None,
    ) -> tuple[list[TEntity], int]:
        """Return a page of entities plus the total matching count."""
        total = self.count(filters=filters, expressions=expressions)
        items = self.list(
            offset=offset,
            limit=limit,
            order_by=order_by,
            filters=filters,
            expressions=expressions,
        )
        return items, total

    def count(
        self,
        *,
        filters: dict[str, Any] | None = None,
        expressions: Sequence[Any] | None = None,
    ) -> int:
        """Count entities matching the given filters."""
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        if expressions:
            for expr in expressions:
                stmt = stmt.where(expr)
        return int(self.session.exec(stmt).one())

    def exists(self, **filters: Any) -> bool:
        """Return whether any entity matches the given equality filters."""
        return self.get_by(**filters) is not None

    def all(self, *, order_by: Any | None = None) -> list[TEntity]:
        """Return every entity (use with care on large tables)."""
        return self.list(order_by=order_by)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def add(self, entity: TEntity) -> TEntity:
        """Persist a new entity instance and flush to obtain its PK."""
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def create(self, **data: Any) -> TEntity:
        """Create, persist, and return a new entity from keyword fields."""
        entity = self.model(**data)
        return self.add(entity)

    def bulk_create(self, entities: Sequence[TEntity]) -> list[TEntity]:
        """Persist multiple entities in one flush."""
        items = list(entities)
        self.session.add_all(items)
        self.session.flush()
        for item in items:
            self.session.refresh(item)
        return items

    def update(self, entity: TEntity, data: dict[str, Any]) -> TEntity:
        """Apply a partial update to an existing entity and flush."""
        for key, value in data.items():
            setattr(entity, key, value)
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: TEntity) -> None:
        """Delete an existing entity."""
        self.session.delete(entity)
        self.session.flush()

    def delete_by_id(self, entity_id: int) -> bool:
        """Delete an entity by primary key; return whether a row was removed."""
        obj = self.get(entity_id)
        if obj is None:
            return False
        self.delete(obj)
        return True
