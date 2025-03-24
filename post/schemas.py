from pydantic import BaseModel


# Post
class Post(BaseModel):
    user_id: int
    text: str


# Post with id
class EditPost(Post):
    id: int


class CommentPost(BaseModel):
    user_id: int
    post_id: int
    text: str


class EditCommentPost(CommentPost):
    id: int


class Like(BaseModel):
    user_id: int
    post_id: int


class RemoveLike(Like):
    id: int
