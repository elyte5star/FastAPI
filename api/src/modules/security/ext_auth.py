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
from httpx import AsyncClient, HTTPError, Response
from fastapi.openapi.models import OAuth2 as OAuth2Model
from modules.utils.misc import date_time_now_utc, time_delta
from fastapi.security import SecurityScopes
from datetime import datetime

cfg: ApiConfig = ApiConfig().from_toml_file().from_env_file()


SCHEME_NAME = "OAuthorization2CodePKCEBearer"
DESC = "Authorization code with PKCE "


class OAuth2CodeBearer(SecurityBase):

    def __init__(
        self,
        authorization_url: str,
        token_url: str,
        auth_method: str,
        scopes: dict[str, str],
        flows: OAuthFlowsModel | dict[str, dict[str, Any]] | None = None,
        scheme_name: str | None = SCHEME_NAME,
        description: str | None = DESC,
        refresh_url: str | None = None,
        auto_error: bool = True,
    ):
        self.auth_method = auth_method

        # ADD MORE OAUTHFLOWS AS NEEDED
        if not flows:
            flows = OAuthFlowsModel(
                authorizationCode=OAuthFlowAuthorizationCode(
                    authorizationUrl=authorization_url,
                    tokenUrl=token_url,
                    refreshUrl=refresh_url,
                    scopes=scopes,
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
        # A cache for Microsoft/Google public keys {'LOCAL': [], 'MSAL': [], 'GOOGLE': []}
        self.public_keys_cache: dict[str, list] = {
            method: [] for method in cfg.auth_methods
        }
        self.next_ext_api_call_time: datetime | None = None

    async def __call__(
        self, security_scopes: SecurityScopes, request: Request
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
        if self.auth_method == "MSAL":
            verified_claims = await self.verify_msal_jwt(
                token, security_scopes.scopes, self.auth_method
            )
            print(verified_claims)
        else:
            verified_claims = await self.verify_google_jwt(
                token, security_scopes.scopes, self.auth_method
            )
        return token

    async def verify_google_jwt(
        self, access_token: str, required_scopes: list[str], auth_method: str
    ):
        pass

    # Validate Azure Entra ID token using Azure AD Public Keys
    async def verify_msal_jwt(
        self, access_token: str, required_scopes: list[str], auth_method: str
    ) -> dict:
        """
        This verifies:

        # Scopes

        # Signature using Azure AD’s public key

        # Expiration (exp)

        # Issuer (iss)

        # Audience (aud)

        """
        if not access_token:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authorization token missing or invalid",
            )
        try:
            unverified_claims: dict[str, Any] = jwt.get_unverified_claims(
                access_token,
            )

            self.validate_scope(unverified_claims, required_scopes)

            # Get Microsoft's public keys
            public_keys = await self.get_public_keys(
                cfg.msal_jwks_url,
                auth_method,
            )
            # Decode JWT Header to get the key ID (kid)
            token_headers: dict[str, Any] = jwt.get_unverified_header(
                access_token,
            )

            token_kid = token_headers.get("kid")

            rsa_key = next(
                (key for key in public_keys if key.get("kid") == token_kid), None
            )
            if rsa_key is None:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid header error: Unable to find appropriate key",
                )
            cfg.logger.debug(f"Loading public key: {rsa_key}")
            claims = jwt.decode(
                access_token,
                key=rsa_key,
                algorithms=["RS256"],
                audience=cfg.msal_client_id,
                issuer=cfg.msal_issuer,
            )
            # ID token claims would at least contain: "iss", "sub", "aud", "exp", "iat",
            # print(unverified_claims)
            return claims
        except HTTPError as e:
            cfg.logger.error(f"HTTP Exception for {e.request.url} - {e}")
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"HTTP Exception for {e.request.url} - {e}",
            )
        except JWTError:
            cfg.logger.error("Invalid token or expired token.")
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token or expired token.",
            )
        except Exception as e:
            cfg.logger.error(f"Internal server error: {str(e)}")
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Token error: Unable to parse authentication",
            )

    def validate_scope(self, unverified_claims: dict, required_scopes: list[str]):
        if not required_scopes:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="No required scope specified",
            )
        # To small letters
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
                roles = [s.lower() for s in roles]
                matches = set(required_scopes).intersection(set(roles))
                if len(matches) > 0:
                    has_valid_scope = True
        else:
            if unverified_claims.get("scp"):
                # the scp claim is a space delimited string
                token_scopes = unverified_claims["scp"].lower().split()
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

    async def get_public_keys(
        self, jwks_uri: str, auth_method: str, params: dict | None = None
    ) -> list:
        make_api_call = (
            self.next_ext_api_call_time is None
            or date_time_now_utc() > self.next_ext_api_call_time
        )
        if not self.public_keys_cache[auth_method] or make_api_call:
            async with AsyncClient(timeout=10) as client:
                cfg.logger.debug(f"Fetching public keys from {jwks_uri}")
                response: Response = await client.get(jwks_uri, params=params)
                response.raise_for_status()  # Raises an error for non-200 responses
                self.public_keys_cache[auth_method] = response.json().get("keys", [])
                self.next_ext_api_call_time = date_time_now_utc() + time_delta(
                    minutes=60
                )  # Fetch keys every 1hr
        return self.public_keys_cache[auth_method]
