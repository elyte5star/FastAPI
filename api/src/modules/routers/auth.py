from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/token",
    summary="Get token",
    response_model=TokenResponse,
)
async def form_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    pass
