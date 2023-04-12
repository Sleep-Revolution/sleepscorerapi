import jwt
from datetime import datetime, timedelta
import os
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

def CreateAccessToken(CentreId: int) -> str:
    # Define token expiration time
    # _jwt = 
    expires_delta = timedelta(minutes=30)
    expires = datetime.utcnow() + expires_delta

    # Define token payload
    payload = {"centreId": str(CentreId), "exp": expires}

    # Generate token
    token = jwt.encode(payload, os.environ["JWT_KEY"], algorithm="HS256")

    return token

def ParseAccessToken(Token: str) -> int:
    try:
        payload = jwt.decode(Token, os.environ["JWT_KEY"], algorithms=["HS256"])
        centreId = int(payload["centreId"])
        return centreId
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class JWTBearer(HTTPBearer):
    def __init__(self):
        super().__init__()
        self.secret_key = os.environ["JWT_KEY"]

    async def __call__(self, request :Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            try:
                payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=["HS256"])
                centreId = int(payload["centreId"])
                return centreId
            except jwt.PyJWTError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
                
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
