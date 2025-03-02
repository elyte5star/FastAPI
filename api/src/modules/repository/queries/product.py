from modules.database.base import AsyncDatabaseSession
from modules.repository.schema.product import Product, Review
from asyncpg.exceptions import PostgresError


class ProductQueries(AsyncDatabaseSession):
    async def create_product_query(self, product: Product) -> None:
        try:
            self.async_session.add(product)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def create_products_query(self, products: list[Product]) -> None:
        try:
            self.async_session.add_all(products)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def get_products_query(self) -> list[Product]:
        stmt = self.select(Product).order_by(Product.created_at)
        result = await self.async_session.execute(stmt)
        products = result.scalars().all()
        return products

    async def find_product_by_id(self, pid: str) -> Product | None:
        return await self.async_session.get(Product, pid)

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
