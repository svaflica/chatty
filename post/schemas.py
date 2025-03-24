from pydantic import BaseModel


# Post
class Post(BaseModel):
    user_id: int
    text: str


# Post with id
class EditPost(Post):
    id: int
    user_id: int
    text: str


class CommentPost(BaseModel):
    user_id: int
    post_id: int
    text: str


class EditCommentPost(BaseModel):
    id: int
    user_id: int
    post_id: int
    text: str
