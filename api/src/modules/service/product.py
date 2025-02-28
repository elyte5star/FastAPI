from modules.repository.queries.product import ProductQueries
from modules.repository.request_models.product import (
    CreateProductRequest,
    CreateProductResponse,
    GetProductRequest,
    GetProductResponse,
    GetProductsRequest,
    GetProductsResponse,
    ProductDisplay
)
from modules.repository.schema.product import Product
from modules.utils.misc import get_indent


class ProductHandler(ProductQueries):
    async def _create_product(
        self,
        req: CreateProductRequest,
    ) -> CreateProductResponse:
        product_exist = await self.find_product_by_name(req.new_product.name)
        if product_exist is None:
            new_product = Product(
                id=get_indent(),
                created_by=req.credentials.username,
                description=req.new_product.description,
                name=req.new_product.name,
                details=req.new_product.details,
                image=req.new_product.image,
                price=req.new_product.price,
                category=req.new_product.category,
                stock_quantity=req.new_product.stock_quantity,
            )
            await self.create_product_query(new_product)
            req.result.pid = new_product.id
            return req.req_success(
                f"Product with id: {new_product.id} created",
            )
        return req.req_failure("Product already exist")

    async def _get_product(self, req: GetProductRequest) -> GetProductResponse:
        product = await self.find_product_by_id(req.pid)
        if product is not None:
            req.result.product = product
            return req.req_success(f"Product with pid {req.pid} found")
        return req.req_failure(f"Product with pid {req.pid} not found")

    async def _get_products(
        self,
        req: GetProductsRequest,
    ) -> GetProductsResponse:
        products = await self.get_products_query()
        req.result.products = products
        return req.req_success(f"Total number of products: {len(products)}")
