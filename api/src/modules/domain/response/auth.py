from modules.domain.base import BaseResponse


class TokenResponse(BaseResponse):
    token: dict = dict()
