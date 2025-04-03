from pydantic import BaseModel


class Subscription(BaseModel):
    subscriber_id: int
    user_id: int

class User(BaseModel):
    id: int


class SubscriptionRabbit(BaseModel):
    message_id: str
    subscriber_id: int
    user_id: int

class UserRabbit(BaseModel):
    message_id: str
    id: int
