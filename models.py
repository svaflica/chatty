from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import ForeignKey

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, index=True)
    password: Mapped[str] = mapped_column(String)
    photo: Mapped[str] = mapped_column(String)


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String(300))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'))


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'), index=True, nullable=False)
    post_id: Mapped[str] = mapped_column(ForeignKey("post.id", ondelete='CASCADE'), nullable=False)
    text: Mapped[str] = mapped_column(String(150))


class Like(Base):
    __tablename__ = "like"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'), index=True, nullable=False)
    post_id: Mapped[str] = mapped_column(ForeignKey("post.id", ondelete='CASCADE'), nullable=False)
