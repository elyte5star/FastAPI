from typing import cast, Any
from starlette.requests import Request
from modules.settings.configuration import ApiConfig
from modules.security.current_user import JWTPrincipal
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import (
    OAuthFlows as OAuthFlowsModel,
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
from modules.repository.queries.common import CommonQueries
from httpx import AsyncClient, HTTPError
from fastapi.openapi.models import OAuth2 as OAuth2Model
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from datetime import datetime
from modules.utils.misc import date_time_now_utc, time_delta


cfg: ApiConfig = ApiConfig().from_toml_file().from_env_file()

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
        # A cache for Microsoft keys {'LOCAL': [], 'MSAL': [], 'GOOGLE': []}
        self.public_keys: dict[str, list] = {method: [] for method in cfg.auth_methods}
        self.refresh_public_keys_time: datetime | None = None

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
        await self.verify_msal_jwt(token, JWKS_URL, self.auth_method)
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
        self.refresh_public_keys_time = date_time_now_utc() - time_delta(60)
        print("later", self.refresh_public_keys_time)
        if not self.public_keys[auth_method]:
            async with AsyncClient(timeout=10) as client:
                cfg.logger.debug(f"Fetching public keyes from {jwks_uri}")
                response = await client.get(jwks_uri)
                response.raise_for_status()  # Raises an error for non-200 responses
            self.public_keys[auth_method] = response.json().get("keys", [])
            # self.refresh_public_keys_time = date_time_now_utc()
        return self.public_keys[auth_method]

    # Validate Azure Entra ID token using Azure AD Public Keys
    async def verify_msal_jwt(
        self, access_token: str, jwks_uri: str, auth_method: str
    ) -> dict:

        # This verifies:

        # Signature using Azure AD’s public key

        # Expiration (exp)

        # Issuer (iss)

        # Audience (aud)
        if not access_token:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authorization token missing or invalid",
            )
        try:
            # Get Microsoft's public keys
            public_keys = await self.get_public_keys(jwks_uri, auth_method)

            if not public_keys:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail="Public key not found",
                )

            # Decode JWT Header to get the key ID (kid)
            token_headers: dict[str, Any] = jwt.get_unverified_header(
                access_token,
            )
            unverified_claims: dict[str, Any] = jwt.get_unverified_claims(
                access_token,
            )
            token_kid = token_headers.get("kid")
            signing_key = next(
                (key for key in public_keys if key.get("kid") == token_kid), None
            )
            cfg.logger.debug(f"Loading public key: {signing_key}")
            public_key = self.pem_public_key(signing_key)
            claims = jwt.decode(
                access_token,
                key=public_key,
                algorithms=["RS256"],
                audience=cfg.msal_client_id,
                issuer=f"https://login.microsoftonline.com/{cfg.msal_tenant_id}/v2.0",
            )
            # ID token claims would at least contain: "iss", "sub", "aud", "exp", "iat",
            # print(unverified_claims)
            return claims
        except HTTPError as e:
            cfg.logger.error(f"HTTP Exception for {e.request.url} - {e}")
            return None
        except JWTError:
            cfg.logger.error("Invalid token or expired token.")
            return None
        except Exception as e:
            cfg.logger.error(f"Internal server error: {str(e)}")
            return None

    def pem_public_key(self, signing_key):
        return (
            rsa.RSAPublicNumbers(
                n=self.decode_value(signing_key["n"]),
                e=self.decode_value(signing_key["e"]),
            )
            .public_key(default_backend())
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    def ensure_bytes(self, key: Any):
        if isinstance(key, str):
            key = key.encode("utf-8")
        return key

    def decode_value(self, val) -> int:
        decoded = base64.urlsafe_b64decode(self.ensure_bytes(val) + b"==")
        return int.from_bytes(decoded, "big")
