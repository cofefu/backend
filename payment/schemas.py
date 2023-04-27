from pydantic import BaseModel


class SbisAuthTokens(BaseModel):
    access_token: str
    sid: str
    token: str
