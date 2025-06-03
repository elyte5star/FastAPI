from pydantic import BaseModel, Field, ConfigDict, SecretStr, computed_field
from modules.repository.validators.base import VerifyEmail, ValidateUUID
from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.booking import (
    CreateBookingResponse,
    GetBookingResponse,
)
from decimal import Decimal
from typing_extensions import Annotated
import datetime
from modules.repository.response_models.job import JobResponse


class BillingAddress(BaseModel):
    b_first_name: Annotated[str, Field(validation_alias="bfirstName", repr=True)]
    b_last_name: Annotated[str, Field(validation_alias="blastName", repr=True)]
    b_email: Annotated[
        VerifyEmail,
        Field(validation_alias="bemail", repr=True),
    ]
    b_address: Annotated[str, Field(validation_alias="baddress", repr=True)]
    b_country: Annotated[str, Field(validation_alias="bcountry", repr=True)]
    b_zip: Annotated[str, Field(validation_alias="bzip", repr=True)]
    b_city: Annotated[str, Field(validation_alias="bcity", repr=True)]


class CartItem(BaseModel):
    price: Annotated[
        Decimal,
        Field(
            max_digits=7,
            decimal_places=2,
            repr=True,
        ),
    ]
    discount: Annotated[
        Decimal,
        Field(
            default=0.0,
            max_digits=7,
            decimal_places=2,
            examples=[0.1, 0.3, 0.4],
            strict=True,
            repr=True,
            gt=0,
        ),
    ]

    quantity: Annotated[
        int,
        Field(
            examples=[1, 3, 4],
            strict=True,
            repr=True,
            gt=0,
        ),
    ]
    pid: ValidateUUID

    @computed_field
    @property
    def calculated_price(self) -> Decimal:
        discount = self.price * self.discount
        sale_price = self.price - discount
        return sale_price * self.quantity

    model_config = ConfigDict(extra="forbid")


class PaymentDetails(BaseModel):
    card_type: Annotated[str, Field(validation_alias="cardType", repr=True)]
    card_number: Annotated[SecretStr, Field(validation_alias="cardNumber")]
    expiry_date: Annotated[datetime.date, Field(validation_alias="expiryDate")]
    card_cvv: Annotated[SecretStr, Field(validation_alias="cardCvv")]
    name_on_card: Annotated[
        str,
        Field(validation_alias="nameOnCard", repr=True),
    ]
    currency: str = "NOK"
    billing_address: Annotated[
        BillingAddress, Field(validation_alias="billingAddress", repr=True)
    ]
    model_config = ConfigDict(extra="forbid")


class ShippingDetails(BaseModel):
    first_name: Annotated[str, Field(validation_alias="firstName", repr=True)]
    last_name: Annotated[str, Field(validation_alias="lastName", repr=True)]
    street_address: Annotated[
        str,
        Field(
            validation_alias="streetAddress",
            repr=True,
        ),
    ]
    country: str
    state: str
    email: VerifyEmail
    zip_code: Annotated[str, Field(validation_alias="zip", repr=True)]
    model_config = ConfigDict(extra="forbid")


class CreateBooking(BaseModel):
    cart: list[CartItem]
    payment_details: Annotated[
        PaymentDetails, Field(validation_alias="paymentDetails", repr=True)
    ]
    shipping_details: Annotated[
        ShippingDetails, Field(validation_alias="shippingDetails", repr=True)
    ]
    userid: ValidateUUID = Field(validation_alias="userId", repr=True)
    model_config = ConfigDict(extra="forbid")


class CreateBookingRequest(BaseReq):
    new_order: CreateBooking | None = None
    result: JobResponse = JobResponse()


class BookingModel(BaseModel):
    cart: list[CartItem]
    total_price: Annotated[
        Decimal,
        Field(
            max_digits=7,
            decimal_places=2,
            validation_alias="totalPrice",
            repr=True,
        ),
    ]
    shipping_details: Annotated[
        ShippingDetails,
        Field(
            serialization_alias="shippingDetails",
            repr=True,
        ),
    ]
    userid: str = Field(serialization_alias="userId", repr=True)

    model_config = ConfigDict(serialize_by_alias=True)


class GetBookingRequest(BaseReq):
    oId: ValidateUUID
    result: GetBookingResponse = GetBookingResponse()
