from pydantic import BaseModel


class User(BaseModel):
    user_id: int


class Post(BaseModel):
    post_id: int


class Comment(BaseModel):
    comment_id: int


class Feedback(BaseModel):
    text: str
