from pydantic import BaseModel


class GetUserResult(BaseModel):
    email: str
    photo: bytes | None = None


# User
class User(GetUserResult):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
