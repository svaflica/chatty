from sqlalchemy import String, Boolean
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import ForeignKey


Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, index=True)
    password: Mapped[str] = mapped_column(String)
    photo: Mapped[str] = mapped_column(String)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String(300))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'), index=True, nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete='CASCADE'), nullable=False)
    text: Mapped[str] = mapped_column(String(150))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Like(Base):
    __tablename__ = "like"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'), index=True, nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete='CASCADE'), nullable=False)


class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subscriber_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'), index=True, nullable=False)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(10))


class Complaint(Base):
    __tablename__ = "complaint"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(10))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete='CASCADE'), index=True, nullable=False)
