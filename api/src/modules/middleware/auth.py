from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import time


class JWTBearer(HTTPBearer):
    def __init__(self, config, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.cf = config

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )

            if self.verify_jwt(credentials.credentials) is None:
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )

            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, token: str):
        if token is None:
            return None
        try:
            self.payload = jwt.decode(
                token, self.cf.secret_key, algorithms=[self.cf.algorithm]
            )
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None
