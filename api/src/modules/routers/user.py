from fastapi import APIRouter, Depends
from typing import Annotated
from modules.repository.response_models.user import GetUserResponse, CreateUserResponse
from modules.repository.request_models.user import CreateUserRequest, GetUserRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/signup", response_model=CreateUserResponse, summary="Create User")
async def create_user(
    req: Annotated[CreateUserRequest, Depends()]
) -> CreateUserResponse:
    req.result = CreateUserResponse()
    return req.success("Yes§")


@router.get("/{userid}", response_model=GetUserResponse, summary="Get one user")
async def get_user(userid: str) -> GetUserResponse:
    res = GetUserRequest(userid=userid)

    return res.success("Just testing")
