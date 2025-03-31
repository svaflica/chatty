from pydantic import BaseModel


class Subscription(BaseModel):
    subscriber_id: int
    user_id: int

class User(BaseModel):
    id: int
