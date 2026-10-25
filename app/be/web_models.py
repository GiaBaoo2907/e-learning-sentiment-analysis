"""SQLAlchemy models shared by the web API and SQL Server schema."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Unicode, UnicodeText, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(Unicode(120), nullable=False)
    email: Mapped[str] = mapped_column(Unicode(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    role: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class PasswordReset(Base):
    __tablename__ = "PasswordResets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Unicode(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)


class Category(Base):
    __tablename__ = "Categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Unicode(500), nullable=False, default="")


class Course(Base):
    __tablename__ = "Courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("Categories.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    instructor: Mapped[str] = mapped_column(Unicode(120), nullable=False)
    description: Mapped[str] = mapped_column(UnicodeText, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Unicode(1000))
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    category: Mapped[Category] = relationship()
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "Lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("Courses.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    description: Mapped[str] = mapped_column(Unicode(1000), nullable=False, default="")
    video_url: Mapped[str] = mapped_column(Unicode(1000), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    course: Mapped[Course] = relationship(back_populates="lessons")


class Enrollment(Base):
    __tablename__ = "Enrollments"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="UQ_Enrollments_User_Course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("Courses.id"), nullable=False, index=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class LessonProgress(Base):
    __tablename__ = "LessonProgress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="UQ_LessonProgress_User_Lesson"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), nullable=False, index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("Lessons.id"), nullable=False, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Feedback(Base):
    __tablename__ = "Feedback"
    __table_args__ = (UniqueConstraint("user_id", "course_id", "lesson_id", name="UQ_Feedback_User_Course_Lesson"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("Courses.id"), nullable=False, index=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("Lessons.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(UnicodeText, nullable=False)
    sentiment: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    moderation_status: Mapped[str] = mapped_column(Unicode(20), nullable=False, default="visible", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
