from modules.repository.request_models.base import BaseResponse
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Any


class CreateProductResponse(BaseResponse):
    pid: str = ""


class CreateProductsResponse(BaseResponse):
    pids: list[str] = []


class CreateProductReviewResponse(BaseResponse):
    rid: str = ""


class ProductReview(BaseModel):
    id: str
    rating: int
    comment: str
    date: datetime = Field(alias="createdAt")
    product_id: str
    email: EmailStr
    reviewer_name: str = Field(alias="reviewerName")


class ProductDeals(BaseModel):
    id: str
    new_price: float
    discount: float


class GetProductResponse(BaseResponse):
    product: Any = {}


class GetProductsResponse(BaseResponse):
    products: list[Any] = []


class GetProductReviewsResponse(BaseResponse):
    reviews: list[ProductReview] = []
