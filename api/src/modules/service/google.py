from modules.service.auth import AuthenticationHandler
from google.oauth2 import id_token
from google.auth.transport import requests
from modules.repository.request_models.auth import MFALoginRequest, BaseResponse
from modules.utils.misc import get_indent
from fastapi import Response


class GoogleHandler(AuthenticationHandler):

    async def authenticate_google_user(
        self, req: MFALoginRequest, response: Response
    ) -> BaseResponse:
        token = req.token
        user_dict = self.verify_gmail_jwt(token)
        if user_dict is None:
            return req.req_failure("Couldnt not verify the audience.")
        user_in_db = await self.find_user_by_email(user_dict["email"])
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
                f"User with username/email : {user_in_db.username} is authorized"
            )
        return req.req_failure(f"User {user_dict["email"]} is not authorized.")

    def verify_gmail_jwt(self, token: str) -> dict | None:
        if token is None:
            return None
        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            token_claims = id_token.verify_oauth2_token(
                token, requests.Request(), self.cf.google_client_id
            )
            # Or, if multiple clients access the backend server:
            # idinfo = id_token.verify_oauth2_token(token, requests.Request())
            # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
            #     raise ValueError('Could not verify audience.')

            # If auth request is from a G Suite domain:
            # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
            #     raise ValueError('Wrong hosted domain.')

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            response_data = {
                "userid": token_claims["sub"],
                "sub": token_claims["name"],
                "email": token_claims["email"],
            }

            return response_data
        except ValueError as e:
            self.cf.logger.error(f"Could not verify audience: {e}")
            return None
