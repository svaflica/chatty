from pydantic import BaseModel


class LoginUser(BaseModel):
    email: str
    password: str


class GetUserResult(BaseModel):
    email: str
    photo: bytes


# User
class User(GetUserResult):
    password: str


class UserChangePassword(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class LoginUserRabbit(BaseModel):
    message_id: str
    email: str
    password: str


class GetUserResultRabbit(BaseModel):
    message_id: str
    email: str
    photo: bytes


# User
class UserRabbit(GetUserResultRabbit):
    password: str


class UserChangePasswordRabbit(BaseModel):
    message_id: str
    email: str
    password: str


class TokenRabbit(BaseModel):
    message_id: str
    access_token: str
    token_type: str


class TokenDataRabbit(BaseModel):
    message_id: str
    email: str | None = None


class CheckTokenRabbit(BaseModel):
    message_id: str
