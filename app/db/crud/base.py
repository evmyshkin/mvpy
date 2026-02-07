"""Имплементация базового DAO-объекта для взаимодействия с БД."""

from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.db.base import BaseDBModel

ModelType = TypeVar('ModelType', bound=BaseDBModel)


class BaseCrud[ModelType]:
    """Базовый класс CRUD для взаимодействия с БД.

    Содержит основные CRUD-методы.
    """

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    # INSERT
    async def add_one(self, session: AsyncSession, **values: object) -> ModelType:
        """Добавляет одну запись в БД."""
        new_instance = self.model(**values)
        session.add(new_instance)
        try:
            await session.commit()
            return new_instance
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при добавлении записи в базу данных',
            ) from e

    async def add_many(
        self, session: AsyncSession, instances: list[dict[str, Any]]
    ) -> list[ModelType]:
        """Добавляет несколько записей в БД."""
        new_instances = [self.model(**values) for values in instances]
        session.add_all(new_instances)
        try:
            await session.commit()
            return new_instances
        except SQLAlchemyError as e:
            await session.rollback()
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка при добавлении записей в базу данных',
            ) from e

    # SELECT
    async def find_one_or_none(
        self, session: AsyncSession, **filter_by: object
    ) -> ModelType | None:
        """Ищет одну запись по атрибутам.

        Args:
            session: Асинхронная сессия БД
            **filter_by: Фильтры для поиска

        Returns:
            Найденная запись или None
        """
        conditions = [getattr(self.model, field) == value for field, value in filter_by.items()]
        query = select(self.model).where(and_(*conditions)) if conditions else select(self.model)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def find_all(self, session: AsyncSession, **filter_by) -> Sequence[ModelType]:
        """Возвращает все записи по фильтру."""
        conditions = [getattr(self.model, field) == value for field, value in filter_by.items()]
        query = select(self.model).where(and_(*conditions)) if conditions else select(self.model)
        result = await session.execute(query)
        return result.scalars().all()

    # UPDATE
    async def update_one_or_none(
        self, session: AsyncSession, filter_by: Mapping[str, Any], values: Mapping[str, Any]
    ) -> ModelType | None:
        """Обновляет запись по фильтру и возвращает обновленную запись."""
        conditions = [getattr(self.model, k) == v for k, v in filter_by.items()]
        stmt = (
            update(self.model)
            .where(and_(*conditions) if conditions else True)
            .values(**values)
            .execution_options(synchronize_session='fetch')
            .returning(self.model)
        )
        result = await session.execute(stmt)
        updated_record = result.scalar_one_or_none()
        await session.commit()
        return updated_record

    async def update_records(
        self, session: AsyncSession, filter_by: Mapping[str, Any], values: Mapping[str, Any]
    ) -> None:
        """Обновляет все записи по фильтру."""
        conditions = [getattr(self.model, k) == v for k, v in filter_by.items()]
        stmt = update(self.model).where(and_(*conditions) if conditions else True).values(**values)
        await session.execute(stmt)
        await session.commit()

    # DELETE
    async def delete_one(self, session: AsyncSession, **filter_by: object) -> BaseDBModel | None:
        """Удаляет одну запись по фильтру."""
        conditions = [getattr(self.model, field) == value for field, value in filter_by.items()]
        stmt = delete(self.model).where(and_(*conditions) if conditions else True)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            await session.commit()  # Коммитим один раз после удаления
            return record
        return None
