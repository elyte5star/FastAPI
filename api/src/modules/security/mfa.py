from typing import Any, cast
from starlette.requests import Request
from typing_extensions import Annotated, Doc
from fastapi.security import OAuth2, OAuth2AuthorizationCodeBearer
from modules.settings.configuration import ApiConfig
from modules.security.current_user import JWTPrincipal
from fastapi.security.base import SecurityBase
from fastapi.openapi.models import (
    OAuthFlows as OAuthFlowsModel,
    SecurityBase as SecurityBaseModel,
)
from fastapi.openapi.models import (
    OAuthFlowAuthorizationCode,
    OAuthFlowPassword,
    OAuthFlowClientCredentials,
)
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from fastapi.exceptions import HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import HTTPBearer as HTTPBearerModel
from jose import JWTError, jwt
import time
from modules.repository.queries.common import CommonQueries

cfg = ApiConfig().from_toml_file().from_env_file()

TOKEN_URL = f"https://login.microsoftonline.com/{cfg.msal_tenant_id}/oauth2/v2.0/token"
SCHEME_NAME = "AuthorizationCodeBearer"
SCOPES = cfg.msal_scopes
DESC = "Authorization code with PKCE "
AUTH_URL = (
    f"https://login.microsoftonline.com/{cfg.msal_tenant_id}/oauth2/v2.0/authorize"
)
JWKS_URL = cfg.msal_jwks_url

ALLOWED_ROLES = ["ADMIN", "USER"]
queries = CommonQueries(cfg)


class AuthCodeBearer(OAuth2):
    def __init__(
        self,
        authorizationUrl: str | None = None,
        tokenUrl: str | None = None,
        refreshUrl: str | None = None,
        scopes: dict[str, str] | None = None,
        scheme_name: str | None = None,
        description: str | None = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            authorizationCode=OAuthFlowAuthorizationCode(
                authorizationUrl=authorizationUrl or AUTH_URL,
                tokenUrl=tokenUrl or TOKEN_URL,
                refreshUrl=refreshUrl,
                scopes=scopes,
            ),
            password=OAuthFlowPassword(
                tokenUrl=tokenUrl or TOKEN_URL,
                refreshUrl=refreshUrl,
                scopes=scopes,
            ),
            clientCredentials=OAuthFlowClientCredentials(
                tokenUrl=tokenUrl or TOKEN_URL,
                refreshUrl=refreshUrl,
                scopes=scopes,
            ),
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> str | None:
        token = await super().__call__(request)
        print(token)
        return token
