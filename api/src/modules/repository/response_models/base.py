from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
        extra="allow",
        serialize_by_alias=True,
    )
    req_id: str = ""
    start_time: float = 0.0
    stop_time: float = 0.0
    process_time: float = 0.0
    success: bool = False
    message: str = ""


class GetInfoResponse(BaseResponse):
    info: dict = {}
