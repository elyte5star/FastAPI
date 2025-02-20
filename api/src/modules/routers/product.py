from modules.service.product import ProductHandler
from fastapi import APIRouter, Depends, status, Request
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
)


class ProductRouter(ProductHandler):
    def __init__(self, config):
        super().__init__(config)
        self.router: APIRouter = APIRouter(
            prefix="/product",
            tags=["Products"],
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
            path="/{pid}",
            endpoint=self.get_product,
            response_model=GetProductResponse,
            methods=["GET"],
            description="Get Product",
        )

        self.router.add_api_route(
            path="",
            endpoint=self.get_products,
            response_model=GetProductsResponse,
            methods=["GET"],
            description="Get product",
        )

    async def create_product(
        self,
        new_product: CreateProduct,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ) -> CreateProductResponse:
        return await self._create_product(
            CreateProductRequest(
                new_product=new_product,
                credentials=current_user,
            ),
        )

    async def get_products(
        self,
    ) -> GetProductsResponse:
        return await self._get_products(GetProductsRequest())

    async def get_product(
        self,
        pid: str,
    ) -> GetProductResponse:
        return await self._get_product(GetProductRequest(pid=pid))
