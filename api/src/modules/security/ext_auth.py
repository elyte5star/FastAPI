from typing import cast, Any
from starlette.requests import Request
from fastapi.security import SecurityScopes
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

TOKEN_URL = cfg.msal_token_url
AUTH_URL = cfg.msal_auth_url
SCHEME_NAME = "OAuthorization2CodePKCEBearer"
SCOPES = cfg.msal_scopes
DESC = "Authorization code with PKCE "
JWKS_URL = cfg.msal_jwks_url


queries = CommonQueries(cfg)


class OAuth2CodeBearer(SecurityBase):

    def __init__(
        self,
        flows: OAuthFlowsModel | dict[str, dict[str, Any]] | None = None,
        authorization_url: str | None = None,
        token_url: str | None = None,
        scopes: dict[str, str] | None = None,
        scheme_name: str | None = SCHEME_NAME,
        description: str | None = DESC,
        refresh_url: str | None = None,
        auto_error: bool = True,
        auth_method: str = "MSAL",
    ):

        # ADD MORE OAUTHFLOWS AS NEEDED
        if not flows:
            flows = OAuthFlowsModel(
                authorizationCode=OAuthFlowAuthorizationCode(
                    authorizationUrl=authorization_url or AUTH_URL,
                    tokenUrl=token_url or TOKEN_URL,
                    refreshUrl=refresh_url,
                    scopes=scopes or SCOPES,
                ),
            )
        self.model = OAuth2Model(
            flows=cast(OAuthFlowsModel, flows), description=description
        )
        self.scheme_name = (
            f"{auth_method.capitalize()}{scheme_name}" or self.__class__.__name__
        )
        self.auto_error = auto_error
        self.auth_method = auth_method
        # A cache for Microsoft keys
        self.public_keys: dict[str, list] = {method: [] for method in cfg.auth_methods}

    async def __call__(self, request: Request) -> str | None:
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

    def check_scope(self, unverified_claims: dict, required_scopes: list[str]):
        required_scopes = [s.lower() for s in required_scopes]
        has_valid_scope = False
        if (
            unverified_claims.get("scp") is None
            and unverified_claims.get("roles") is None
        ):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="No scope or app permission (role) claim was found in the bearer token",
            )
        is_app_permission = (
            True if unverified_claims.get("roles") is not None else False
        )
        if is_app_permission:
            roles = unverified_claims.get("roles", [])
            if not roles:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="No scope or app permission (role) claim was found in the bearer token",
                )
            else:
                matches = set(required_scopes).intersection(set(roles))
                if len(matches) > 0:
                    has_valid_scope = True
        else:
            if unverified_claims.get("scp"):
                # the scp claim is a space delimited string
                token_scopes = unverified_claims["scp"].split()
                matches = set(required_scopes).intersection(set(token_scopes))
                if len(matches) > 0:
                    has_valid_scope = True
            else:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="No scope or app permission (role) claim was found in the bearer token",
                )
        if is_app_permission and not has_valid_scope:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        elif not has_valid_scope:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

    async def get_public_keys(self, jwks_uri: str, auth_method: str) -> list:
        if not self.public_keys[auth_method]:
            async with AsyncClient(timeout=10) as client:
                cfg.logger.debug(f"Fetching public keyes from {jwks_uri}")
                response = await client.get(jwks_uri)
                response.raise_for_status()  # Raises an error for non-200 responses
            self.public_keys[auth_method] = response.json().get("keys", [])
        return self.public_keys[auth_method]
