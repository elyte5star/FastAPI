from modules.repository.queries.product import ProductQueries
from modules.repository.request_models.product import (
    CreateProductRequest,
    CreateProductResponse,
    GetProductRequest,
    GetProductResponse,
    GetProductsRequest,
    GetProductsResponse,
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
                pid=get_indent(),
                created_by=req.credentials.username,
                description=req.new_product.description,
                details=req.new_product.description,
                image=req.new_product.image,
                price=req.new_product.price,
                category=req.new_product.category,
                stock_quantity=req.new_product.stock_quantity,
            )
            product_id = await self.create_product_query(new_product)
            if product_id:
                req.result.pid = product_id
                return req.req_success("New product created!")
            return req.req_failure("Couldn't create a product ,try later.")
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
