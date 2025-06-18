from modules.service.product import ProductHandler
from fastapi import APIRouter, Depends, status
from typing import Annotated
from modules.security.dependency import security, JWTPrincipal, RoleChecker
from modules.repository.request_models.product import (
    CreateProductRequest,
    CreateProductResponse,
    GetProductRequest,
    GetProductResponse,
    GetProductsRequest,
    GetProductsResponse,
    CreateProduct,
    CreateProductsResponse,
    CreateProductsRequest,
    CreateProductReviewRequest,
    CreateProductReview,
    CreateProductReviewResponse,
    GetProductReviewRequest,
    GetProductReviewResponse,
    DeleteProductRequest,
    BaseResponse,
)


class ProductRouter(ProductHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/product",
            tags=["Product"],
        )
        self.router.add_api_route(
            path="/create",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_product,
            response_model=CreateProductResponse,
            methods=["POST"],
            dependencies=[Depends(RoleChecker(["ADMIN"]))],
            description="Create a product",
        )
        self.router.add_api_route(
            path="/create-many",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_products,
            response_model=CreateProductsResponse,
            methods=["POST"],
            description="Create a products",
        )
        self.router.add_api_route(
            path="/{pid}",
            endpoint=self.get_product,
            response_model=GetProductResponse,
            methods=["GET"],
            description="Get Product",
        )
        self.router.add_api_route(
            path="/{pid}",
            endpoint=self.delete_product,
            response_model=BaseResponse,
            methods=["DELETE"],
            description="Delete a product",
        )

        self.router.add_api_route(
            path="",
            endpoint=self.get_products,
            response_model=GetProductsResponse,
            methods=["GET"],
            description="Get product",
        )

        self.router.add_api_route(
            path="/review",
            status_code=status.HTTP_201_CREATED,
            endpoint=self.create_product_review,
            response_model=CreateProductReviewResponse,
            methods=["POST"],
            description="Create a product review",
        )
        self.router.add_api_route(
            path="/review/{rid}",
            endpoint=self.get_product_review,
            response_model=GetProductReviewResponse,
            methods=["GET"],
            description="Get a product revew",
        )

    async def create_product(
        self,
        new_product: CreateProduct,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> BaseResponse:
        return await self._create_product(
            CreateProductRequest(
                new_product=new_product,
                credentials=current_user,
            ),
        )

    async def create_product_review(self, review: CreateProductReview) -> BaseResponse:
        return await self._create_review(
            CreateProductReviewRequest(review=review),
        )

    async def create_products(
        self,
        new_products: list[CreateProduct],
        current_user: Annotated[JWTPrincipal, Depends(RoleChecker(["ADMIN"]))],
    ) -> BaseResponse:
        return await self._create_many_products(
            CreateProductsRequest(
                new_products=new_products,
                credentials=current_user,
            ),
        )

    async def get_products(
        self,
    ) -> BaseResponse:
        return await self._get_products(GetProductsRequest())

    async def get_product(
        self,
        pid: str,
    ) -> BaseResponse:
        return await self._get_product(GetProductRequest(pid=pid))

    async def get_product_review(
        self,
        rid: str,
    ) -> BaseResponse:
        return await self._get_product_review(GetProductReviewRequest(rid=rid))

    async def delete_product(
        self,
        pid: str,
        current_user: Annotated[
            JWTPrincipal,
            Depends(security),
        ],
    ) -> BaseResponse:
        return await self._delete_product(
            DeleteProductRequest(credentials=current_user, pid=pid)
        )
