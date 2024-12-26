from fastapi import APIRouter
from modules.repository.response_models.user import GetUserResponse, CreateUserResponse
from modules.repository.request_models.user import CreateUserRequest

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("/signup", response_model=CreateUserResponse, summary="Create User")
async def create_user(user_data: CreateUserRequest) -> CreateUserResponse:
    pass


@user_router.get("/{userid}", response_model=GetUserResponse, summary="Get one user")
async def get_user(userid: str) -> GetUserResponse:
    pass
