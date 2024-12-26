from modules.repository.base import BaseResponse


class TokenResponse(BaseResponse):
    token: dict = dict()
