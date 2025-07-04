import json
from fastapi import Response
from jose import JWTError, jwk, jwt

from modules.repository.request_models.auth import BaseResponse, MSOFTMFALoginRequest
from modules.service.auth import AuthenticationHandler
from modules.utils.misc import get_indent
from httpx import AsyncClient, HTTPError


class MSOFTHandler(AuthenticationHandler):

    async def authenticate_msoft_user(
        self, req: MSOFTMFALoginRequest, response: Response
    ) -> BaseResponse:
        auth_code = req.code
        claims = await self.verify_msal_jwt(token)
        if claims is None:
            return req.req_failure("Couldnt not verify audience.")
        email = claims["preferred_username"]
        user_in_db = await self.find_user_by_email(email)
        if user_in_db is not None:
            if not user_in_db.enabled or user_in_db.is_locked:
                return req.req_failure(
                    " Account unverified or locked. Please, contact admin "
                )
            if not user_in_db.is_using_mfa:
                return req.req_failure("MFA is disabled for this account ")
            data = {
                "userId": user_in_db.id,
                "sub": user_in_db.username,
                "email": user_in_db.email,
                "admin": user_in_db.admin,
                "enabled": user_in_db.enabled,
                "active": user_in_db.active,
                "role": "USER" if not user_in_db.admin else "ADMIN",
                "jti": get_indent(),
                "discount": user_in_db.discount,
                "accountNonLocked": not user_in_db.is_locked,
            }
            token_data = await self.create_token_response(user_in_db, data)
            self.create_cookie(token_data.pop("refreshToken"), response)
            req.result.data = token_data
            return req.req_success(
                f"User with username/email: {user_in_db.username} is authorized"
            )
        return req.req_failure(f"User with email {email} is not authorized.")

    async def get_public_keys(self) -> dict:
        if not self.public_keys:
            async with AsyncClient(timeout=10) as client:
                self.cf.logger.debug(
                    f"Fetching public keyes from {self.cf.msal_jwks_url}"
                )
            response = await client.get(self.cf.msal_jwks_url)
            response.raise_for_status()
            self.public_keys = response.json().get("keys", [])
        return self.public_keys

    # Validate Token using Azure AD Public Keys
    async def verify_msal_jwt(self, token: str) -> dict | None:
        if not token:
            return None
        try:
            # Get Microsoft's public keys
            public_keys = await self.get_public_keys()
            # Decode JWT Header to get the key ID (kid)
            token_headers = jwt.get_unverified_header(token)
            token_kid = token_headers.get("kid")
            key_id = next(
                (key for key in public_keys if key.get("kid") == token_kid), None
            )
            self.cf.logger.debug(f"Loading public key from certificate: {key_id}")
            public_key = jwk.construct(key_data=json.dumps(key_id), algorithm="RS256")
            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                audience=self.cf.msal_client_id,
                issuer=f"https://sts.windows.net/{self.cf.msal_tenant_id}/",
            )
            print(claims)
            return claims
        except HTTPError as e:
            self.cf.logger.error(f"HTTP Exception for {e.request.url} - {e}")
            return None
        except JWTError:
            self.cf.logger.error("Invalid token or expired token.")
            return None
        except Exception as e:
            self.cf.logger.error(f"Internal server error: {str(e)}")
            return None
