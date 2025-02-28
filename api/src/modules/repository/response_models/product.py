from modules.repository.request_models.base import BaseResponse
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class CreateProductResponse(BaseResponse):
    pid: str = ""


class CreateProductReviewResponse(BaseResponse):
    id: str = ""


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


class ProductDisplay(BaseModel):
    pid: str = Field(alias="userid")
    created_at: datetime = Field(alias="createdAt")
    modified_at: Optional[datetime] = Field(
        default=None,
        alias="lastModifiedAt",
    )
    modified_by: Optional[str] = Field(default="", alias="lastModifiedBy")
    created_by: str = Field(alias="createdBy")
    name: str
    description: str
    details: str
    image: str
    price: float
    category: str
    reviews: list[ProductReview] = []
    promotion: ProductDeals = None


class GetProductResponse(BaseResponse):
    product: ProductDisplay = None


class GetProductsResponse(BaseResponse):
    products: list[ProductDisplay] = []


class GetProductReviewsResponse(BaseResponse):
    reviews: list[ProductReview] = []
