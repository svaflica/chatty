from pydantic import BaseModel


# Post
class Post(BaseModel):
    user_id: int
    text: str


# Post with id
class EditPost(Post):
    id: int


# Post with id
class DeletePost(BaseModel):
    id: int


class CommentPost(BaseModel):
    user_id: int
    post_id: int
    text: str


class EditCommentPost(BaseModel):
    id: int
    text: str


class DeleteCommentPost(BaseModel):
    id: int


class Like(BaseModel):
    user_id: int
    post_id: int


# Post
class PostRabbit(BaseModel):
    message_id: str
    user_id: int
    text: str


class PostGetRabbit(BaseModel):
    message_id: str
    id: int

# Post with id
class EditPostRabbit(PostRabbit):
    id: int


# Post with id
class DeletePostRabbit(BaseModel):
    message_id: str
    id: int


class CommentPostRabbit(BaseModel):
    message_id: str
    user_id: int
    post_id: int
    text: str


class CommentPostGetRabbit(BaseModel):
    message_id: str
    id: int


class EditCommentPostRabbit(BaseModel):
    message_id: str
    id: int
    text: str


class DeleteCommentRabbit(BaseModel):
    message_id: str
    id: int


class LikeRabbit(BaseModel):
    message_id: str
    user_id: int
    post_id: int
