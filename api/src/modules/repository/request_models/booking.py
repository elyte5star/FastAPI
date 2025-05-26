from pydantic import BaseModel, Field
from typing import Optional
from modules.repository.validators.base import VerifyEmail,ValidateUUID
from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.booking import CreateBookingResponse
from decimal import Decimal
from typing_extensions import Annotated

class BillingAddress(BaseModel):
    b_full_name: Annotated[str,Field(validation_alias="bFullName")]
    b_email: Annotated[VerifyEmail,Field(validation_alias="bEmail")]
    b_address: Annotated[str, Field(validation_alias="bAddress")]
    b_country: Annotated[str,Field(validation_alias="bCountry")]
    b_zip: Annotated[str,Field(validation_alias="bZip")]
    b_city: Annotated[str,Field(validation_alias="bCity")]


class CartItem(BaseModel):
    discount: float
    quantity: Annotated[
        int,
        Field(
            examples=[1, 3, 4],
            strict=True,
            gt=0,
        ),
    ]
    pid:ValidateUUID
    calculated_price: Annotated[Decimal, Field(max_digits=7, decimal_places=2)]


class PaymentDetails(BaseModel):
    card_type: Annotated[str,Field(validation_alias="cardType")]
    card_number: Annotated[str,Field(validation_alias="cardNumber")]
    expiry_date: Annotated[str,Field(validation_alias="expiryDate")]
    card_cvv: Annotated[str,Field(validation_alias="cardCvv")]
    name_on_card: Annotated[str,Field(validation_alias="nameOnCard")]
    billing_address: Annotated[BillingAddress,Field(validation_alias="billingAddress")]


class ShippingDetails(BaseModel):
    full_name:Annotated[str,Field(validation_alias="fullName")]
    street_address:Annotated[str,Field(validation_alias="streetAddress")]
    country:str
    state:str
    email:VerifyEmail
    zip:str


class CreateBooking(BaseModel):
    cart: list[CartItem]
    total_price: Annotated[Decimal,Field(max_digits=7, decimal_places=2,validation_alias="totalPrice")]
    payment_details: Annotated[PaymentDetails,Field(validation_alias="paymentDetails")]
    shipping_details: Annotated[ShippingDetails,Field(default=None,validation_alias="shippingDetails")]


class CreateBookingRequest(BaseReq):
    new_order:CreateBooking =None
    result:CreateBookingResponse =CreateBookingResponse()
