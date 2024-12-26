from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from modules.repository.response_models.auth import TokenResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/token",
    summary="Get token",
    response_model=TokenResponse,
)
async def form_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    pass
