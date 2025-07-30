from modules.database.schema.product import Product, Review
from asyncpg.exceptions import PostgresError
from collections.abc import Sequence
from modules.repository.queries.common import CommonQueries


class ProductQueries(CommonQueries):
    async def create_product_query(self, product: Product) -> Product:
        try:
            self.async_session.add(product)
            await self.async_session.commit()
            await self.async_session.refresh(product)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            return product

    async def create_products_query(self, products: list[Product]) -> None:
        try:
            self.async_session.add_all(products)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def get_products_query(self) -> Sequence[Product]:
        stmt = self.select(Product).order_by(Product.created_at)
        result = await self.async_session.execute(stmt)
        return result.scalars().all()

    async def delete_product_query(self, pid: str) -> None:
        try:
            stmt = self.delete(Product).where(Product.id == pid)
            await self.async_session.execute(stmt)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def find_product_review_by_id(self, rid: str) -> Review | None:
        return await self.async_session.get(Review, rid)

    async def find_product_by_name(self, name: str) -> Product | None:
        result = await self.async_session.scalars(
            self.select(Product)
            .where(Product.name == name)
            .execution_options(populate_existing=True)
        )
        return result.first()

    async def create_product_review_query(self, review: Review) -> None:
        try:
            self.async_session.add(review)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def update_product_info_query(self, pid: str, changes: dict):
        try:
            user = await self.async_session.get(Product, pid)
            for key, value in changes.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.async_session.commit()
        except PostgresError as e:
            await self.async_session.rollback()
            self.logger.error("Failed to update user:", e)
            raise
