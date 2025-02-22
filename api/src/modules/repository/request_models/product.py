from pydantic import BaseModel, Field
from typing_extensions import Annotated
from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.product import (
    CreateProductResponse,
    GetProductResponse,
    GetProductsResponse,
    CreateProductReviewResponse,
    GetProductReviewsResponse,
)
from modules.repository.validators.base import VerifyEmail, ValidateUUID


class CreateProduct(BaseModel):
    name: str
    description: str
    details: str
    image: str
    price: float
    category: str
    stock_quantity: Annotated[
        int,
        Field(
            examples=[1, 3, 4],
            default=1,
            strict=True,
            gt=0,
            validation_alias="stockQuantity",
        ),
    ]


class CreateProductReview(BaseModel):
    rating: int
    comment: str = Field(min_length=3, max_length=500)
    email: VerifyEmail
    pid: ValidateUUID
    reviewer_name: Annotated[
        str,
        Field(strict=True, validation_alias="reviewerName"),
    ]


class CreateProductReviewrequest(BaseReq):
    review: CreateProductReview = None
    result: CreateProductReviewResponse = CreateProductReviewResponse()


class CreateProductRequest(BaseReq):
    new_product: CreateProduct = None
    result: CreateProductResponse = CreateProductResponse()


class GetProductRequest(BaseReq):
    pid: ValidateUUID
    result: GetProductResponse = GetProductResponse()


class GetProductsRequest(BaseReq):
    result: GetProductResponse = GetProductsResponse()


class GetProductReviewsRequest(BaseReq):
    result: GetProductReviewsResponse = GetProductReviewsResponse()
