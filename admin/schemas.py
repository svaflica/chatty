from pydantic import BaseModel


class User(BaseModel):
    user_id: int


class Post(BaseModel):
    post_id: int


class Comment(BaseModel):
    comment_id: int


class Feedback(BaseModel):
    text: str


class Complaint(BaseModel):
    user_id: int
    text: str


class UserRabbit(BaseModel):
    message_id: str
    user_id: int


class PostRabbit(BaseModel):
    message_id: str
    post_id: int


class CommentRabbit(BaseModel):
    message_id: str
    comment_id: int


class FeedbackRabbit(BaseModel):
    message_id: str
    text: str


class ComplaintRabbit(BaseModel):
    message_id: str
    user_id: int
    text: str
