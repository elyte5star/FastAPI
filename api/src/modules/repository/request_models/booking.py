from pydantic import BaseModel, Field, ConfigDict, SecretStr
from modules.repository.validators.base import VerifyEmail, ValidateUUID
from modules.repository.request_models.base import BaseReq
from modules.repository.response_models.booking import (
    GetBookingResponse,
)
from typing_extensions import Annotated
import datetime
from modules.repository.response_models.job import GetJobRequestResponse
from modules.queue.models import CartItem, ShippingAddress


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


class CreateBooking(BaseModel):
    cart: list[CartItem]
    payment_details: Annotated[
        PaymentDetails, Field(validation_alias="paymentDetails", repr=True)
    ]
    shipping_address: Annotated[
        ShippingAddress, Field(validation_alias="shippingAddress", repr=True)
    ]
    user_id: ValidateUUID = Field(validation_alias="userId", repr=True)
    model_config = ConfigDict(extra="forbid")


class CreateBookingRequest(BaseReq):
    new_order: CreateBooking
    result: GetJobRequestResponse = GetJobRequestResponse()


class GetBookingRequest(BaseReq):
    oId: ValidateUUID
    result: GetBookingResponse = GetBookingResponse()
