from api.src.modules.settings.configuration import ApiConfig
from modules.service.auth import AuthenticationHandler
from jose import JWTError, jwt
import requests
from cryptography.hazmat.primitives import serialization
import json

# Azure AD Configurations


class MSOFTHandler(AuthenticationHandler):
    def __init__(self, config: ApiConfig):
        super().__init__(config)
        self.TENANT_ID = config.msal_tenant_id
        self.CLIENT_ID = config.msal_client_id
        self.CLIENT_SECRET = config.msal_client_secret
        self.AUTH_URL = (
            f"https://login.microsoftonline.com/{self.TENANT_ID}/oauth2/v2.0/authorize"
        )
        self.TOKEN_URL = (
            f"https://login.microsoftonline.com/{self.TENANT_ID}/oauth2/v2.0/token"
        )
        self.KEYS_URL = (
            f"https://login.microsoftonline.com/{self.TENANT_ID}/discovery/keys"
        )
        self.SCOPE = f"api://{self.CLIENT_ID}/access_as_user offline_access"

    # Validate Token using Azure AD Public Keys
    def verify_msal_jwt(self, token: str) -> dict | None:
        if not token:
            return None
        try:
            response1 = requests.get(self.KEYS_URL)
            response1.raise_for_status()
            keys = response1.json().get("keys", [])

            token_headers = jwt.get_unverified_header(token)
            token_kid = token_headers.get("kid")
            public_key = next(
                (key for key in keys if key.get("kid") == token_kid), None
            )
            rsa_pem_key = jwt.construct_rsa_public_key(json.dumps(public_key))
            rsa_pem_key_bytes = rsa_pem_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            claims = jwt.decode(
                token,
                key=rsa_pem_key_bytes,
                algorithms=["RS256"],
                audience=f"api://{self.CLIENT_ID}",
                issuer=f"https://sts.windows.net/{self.TENANT_ID}/",
            )

            return claims
        except requests.RequestException as e:
            self.cf.logger.error(f"Request error: {str(e)}")
            return None
        except JWTError:
            self.cf.logger.error("Invalid token or expired token.")
            return None
        except Exception as e:
            self.cf.logger.error(f"Internal server error: {str(e)}")
            return None
