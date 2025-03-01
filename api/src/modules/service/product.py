from modules.repository.queries.product import ProductQueries
from modules.repository.request_models.product import (
    CreateProductRequest,
    CreateProductResponse,
    GetProductRequest,
    GetProductResponse,
    GetProductsRequest,
    GetProductsResponse,
    CreateProductsResponse,
    CreateProductsRequest,
    CreateProductReviewRequest,
    CreateProductReviewResponse,
)
from modules.repository.schema.product import Product, Review
from modules.utils.misc import get_indent, obj_as_json, time_now


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

    async def _create_many_products(
        self, req: CreateProductsRequest
    ) -> CreateProductsResponse:
        new_products, product_ids = [], []
        for product in req.new_products:
            product_exist = await self.find_product_by_name(product.name)
            if product_exist is None:
                new_product = Product(
                    id=get_indent(),
                    created_by=req.credentials.username,
                    description=product.description,
                    name=product.name,
                    details=product.details,
                    image=product.image,
                    price=product.price,
                    category=product.category,
                    stock_quantity=product.stock_quantity,
                )
                product_ids.append(new_product.id)
                new_products.append(new_product)
            self.cf.logger.warning(f"product with name: {product.name} exist")
        await self.create_products_query(new_products)
        req.result.pids = product_ids
        return req.req_success(
            f"Total number of products created: {len(new_products)}",
        )

    async def _create_review(
        self, req: CreateProductReviewRequest
    ) -> CreateProductReviewResponse:
        product = await self.find_product_by_id(req.review.pid)
        if product is not None:
            new_review = Review(
                id=get_indent(),
                reviewer_name=req.review.reviewer_name,
                date=time_now(),
                email=req.review.email,
                rating=req.review.rating,
                comment=req.review.comment,
                product_id=req.review.pid,
            )
            await self.create_product_review_query(new_review)
            req.result.rid = new_review.id
            return req.req_success(
                f"Product review with id: {new_review.id} created",
            )
        return req.req_failure(f"Product with pid {req.review.pid} not found")

    async def _get_product(self, req: GetProductRequest) -> GetProductResponse:
        product = await self.find_product_by_id(req.pid)
        if product is not None:
            product_dict = obj_as_json(product)
            product_dict["pid"] = product_dict.pop("id")
            product_dict["stockQuantity"] = product_dict.pop("stock_quantity")
            req.result.product = self.remove_fields(product_dict)
            return req.req_success(f"Product with pid {req.pid} found")
        return req.req_failure(f"Product with pid {req.pid} not found")

    async def _get_products(
        self,
        req: GetProductsRequest,
    ) -> GetProductsResponse:
        result = []
        products = await self.get_products_query()
        for product in products:
            product_dict = obj_as_json(product)
            product_dict["pid"] = product_dict.pop("id")
            product_dict["stockQuantity"] = product_dict.pop("stock_quantity")
            result.append(self.remove_fields(product_dict))
        req.result.products = result
        return req.req_success(f"Total number of products: {len(result)}")

    def remove_fields(self, product: dict) -> dict:
        fields = ["modified_by", "modified_at", "created_at", "created_by"]
        for field in fields:
            if field in product.keys():
                del product[field]
        return product
