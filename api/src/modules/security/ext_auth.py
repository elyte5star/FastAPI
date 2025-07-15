from typing import Any, Dict, cast
from starlette.requests import Request
from typing_extensions import Annotated, Doc
from fastapi.security import OAuth2, SecurityScopes
from modules.settings.configuration import ApiConfig
from modules.security.current_user import JWTPrincipal
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import (
    OAuthFlows as OAuthFlowsModel,
    SecurityBase as SecurityBaseModel,
)
from fastapi.security.base import SecurityBase
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from fastapi.exceptions import HTTPException
from jose import JWTError, jwt
import time
from modules.repository.queries.common import CommonQueries
from httpx import AsyncClient, HTTPError
from fastapi.openapi.models import OAuth2 as OAuth2Model


cfg = ApiConfig().from_toml_file().from_env_file()

TOKEN_URL = ""
SCHEME_NAME = "OAuthorization2CodePKCEBearer"
SCOPES = {}
DESC = "Authorization code with PKCE "
AUTH_URL = ""
JWKS_URL = ""


queries = CommonQueries(cfg)


class OAuth2CodeBearer(SecurityBase):

    def __init__(
        self,
        authorizationUrl: str | None = None,
        tokenUrl: str | None = None,
        refreshUrl: str | None = None,
        scopes: dict[str, str] | None = None,
        scheme_name: str | None = SCHEME_NAME,
        description: str | None = DESC,
        auto_error: bool = True,
    ):
        super().__init__()
        flows = OAuthFlowsModel(
            authorizationCode=OAuthFlowAuthorizationCode(
                authorizationUrl=authorizationUrl or AUTH_URL,
                tokenUrl=tokenUrl or TOKEN_URL,
                refreshUrl=refreshUrl,
                scopes=scopes or SCOPES,
            ),
        )
        self.model = OAuth2Model(
            flows=cast(OAuthFlowsModel, flows), description=description
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(
        self, request: Request, security_scopes: SecurityScopes
    ) -> str | None:
        authorization = request.headers.get("Authorization", None)
        scheme, token = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and token):
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            else:
                return None
        return token

    async def get_public_keys(self, jwks_uri: str) -> list:
        if not cfg.public_keys:
            async with AsyncClient(timeout=10) as client:
                cfg.logger.debug(f"Fetching public keyes from {jwks_uri}")
                response = await client.get(jwks_uri)
                response.raise_for_status()  # Raises an error for non-200 responses
            cfg.public_keys = response.json().get("keys", [])
        return cfg.public_keys
