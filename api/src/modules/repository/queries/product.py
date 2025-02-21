from modules.database.base import AsyncDatabaseSession
from modules.repository.schema.product import Product
from asyncpg.exceptions import PostgresError


class ProductQueries(AsyncDatabaseSession):
    async def create_product_query(self, product: Product) -> None:
        result = ""
        self.async_session.add(product)
        try:
            await self.async_session.commit()
            result = "1234354456456"
        except PostgresError:
            await self.async_session.rollback()
            raise
        finally:
            return result

    async def get_products_query(self) -> list[Product]:
        result = await self.async_session.scalars(
            self.select((Product).order_by(Product.created_at))
        )
        return result

    async def find_product_by_id(self, pid: str) -> Product | None:
        return await self.async_session.get(Product, pid)

    async def find_product_by_name(self, name: str) -> Product | None:
        result = await self.async_session.scalars(
            self.select(Product)
            .where(Product.name == name)
            .execution_options(populate_existing=True)
        )
        return result.first()
