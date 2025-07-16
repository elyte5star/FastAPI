import json
from fastapi import Response
from jose import JWTError, jwt
from modules.repository.request_models.auth import BaseResponse, MFALoginRequest
from modules.service.auth import AuthenticationHandler
from modules.utils.misc import get_indent
from httpx import AsyncClient, HTTPError
from typing import Any
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64


class MFAHandler(AuthenticationHandler):

    async def authenticate_msoft_user(
        self, req: MFALoginRequest, response: Response
    ) -> BaseResponse:
        token = req.access_token
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

    async def get_public_keys(self) -> list:
        async with AsyncClient(timeout=10) as client:
            self.cf.logger.debug(f"Fetching public keyes from {self.cf.msal_jwks_url}")
            response = await client.get(self.cf.msal_jwks_url)
            response.raise_for_status()  # Raises an error for non-200 responses
        return response.json().get("keys", [])

    # Validate Azure Entra ID token using Azure AD Public Keys
    async def verify_msal_jwt(self, access_token: str) -> dict | None:

        # This verifies:

        # Signature using Azure AD’s public key

        # Expiration (exp)

        # Issuer (iss)

        # Audience (aud)
        if not access_token:
            return None
        try:
            # Get Microsoft's public keys
            public_keys = await self.get_public_keys()
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
            self.cf.logger.debug(f"Loading public key: {signing_key}")
            public_key = self.pem_public_key(signing_key)
            claims = jwt.decode(
                access_token,
                key=public_key,
                algorithms=["RS256"],
                audience=self.cf.msal_client_id,
                issuer=f"https://login.microsoftonline.com/{self.cf.msal_tenant_id}/v2.0",
            )
            # ID token claims would at least contain: "iss", "sub", "aud", "exp", "iat",
            # print(unverified_claims)
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
