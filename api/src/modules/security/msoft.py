from typing import Dict
from fastapi import Request
from typing_extensions import Annotated, Doc
from fastapi.security import OAuth2AuthorizationCodeBearer
from modules.settings.configuration import ApiConfig
from modules.security.current_user import JWTPrincipal

cfg = ApiConfig().from_toml_file().from_env_file()

TOKEN_URL = f"https://login.microsoftonline.com/{cfg.msal_tenant_id}/oauth2/v2.0/token"
SCHEME_NAME = "MSALAuthorizationCodeBearer"
SCOPES = cfg.msal_scopes
AUTH_URL = (
    f"https://login.microsoftonline.com/{cfg.msal_tenant_id}/oauth2/v2.0/authorize"
)
JWKS_URL = cfg.msal_jwks_url


class MSALBearer(OAuth2AuthorizationCodeBearer):

    def __init__(
        self,
        authorizationUrl: str = AUTH_URL,
        tokenUrl: str = TOKEN_URL,
        refreshUrl: str | None = None,
        scheme_name: str | None = SCHEME_NAME,
        scopes: dict[str, str] | None = SCOPES,
        description: str | None = None,
        auto_error: bool = True,
    ):
        super().__init__(
            authorizationUrl,
            tokenUrl,
            refreshUrl,
            scheme_name,
            scopes,
            description,
            auto_error,
        )

    async def __call__(self, request: Request) -> str | None:
        token = await super().__call__(request)
        print(token)
