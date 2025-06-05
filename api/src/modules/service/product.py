from modules.repository.queries.product import ProductQueries
from modules.repository.request_models.product import (
    CreateProductRequest,
    GetProductRequest,
    GetProductsRequest,
    CreateProductsRequest,
    CreateProductReviewRequest,
    GetProductReviewRequest,
    DeleteProductRequest,
)
from modules.repository.response_models import product
from modules.database.schema.product import Product, Review
from modules.utils.misc import get_indent


class ProductHandler(ProductQueries):

    async def _create_product(
        self,
        req: CreateProductRequest,
    ) -> product.CreateProductResponse:
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
    ) -> product.CreateProductsResponse:
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
    ) -> product.CreateProductReviewResponse:
        product = await self.find_product_by_id(req.review.pid)
        if product is not None:
            new_review = Review(
                id=get_indent(),
                reviewer_name=req.review.reviewer_name,
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

    async def _get_product(self, req: GetProductRequest) -> product.GetProductResponse:
        product_in_db = await self.find_product_by_id(req.pid)
        if product_in_db is not None:
            pydantic_model = product.Product.model_validate(product_in_db)
            req.result.product = pydantic_model
            return req.req_success(f"Product with pid {req.pid} found")
        return req.req_failure(f"Product with pid {req.pid} not found")

    async def _get_product_review(
        self, req: GetProductReviewRequest
    ) -> product.GetProductReviewResponse:
        review_in_db = await self.find_product_review_by_id(req.rid)
        if review_in_db is not None:
            pydantic_model = product.ProductReview.model_validate(review_in_db)
            req.result.review = pydantic_model
            return req.req_success(f"Product review with rid {req.rid} found")
        return req.req_failure(f"Product with review rid {req.rid} not found")

    async def _get_products(
        self,
        req: GetProductsRequest,
    ) -> product.GetProductsResponse:
        products_in_db = [
            product.Product.model_validate(product_in_db)
            for product_in_db in await self.get_products_query()
        ]
        req.result.products = products_in_db
        return req.req_success(f"Total number of products: {len(products_in_db)}")

    async def _delete_product(self, req: DeleteProductRequest) -> product.BaseResponse:
        product = await self.find_product_by_id(req.pid)
        if product is not None:
            await self.delete_product_query(req.pid)
            self.cf.logger.warning(
                f"Product with id: {req.pid} was deleted by :{req.credentials.userid}"
            )
            return req.req_success(f"Product with id: {req.pid} deleted")
        return req.req_failure(f"Product with pid {req.pid} not found")
