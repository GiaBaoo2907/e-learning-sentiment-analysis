"""FastAPI backend for the E-learning sentiment analysis web application."""

import hashlib
import os
import smtplib
import sys
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

import joblib
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, func, select, true
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
src_path = str(ROOT / 'app/ml/src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from sentiment_analysis.preprocessing import clean_text, segment_text
from be.web_models import (
    Base,
    Category,
    Course,
    Enrollment,
    Feedback,
    Lesson,
    LessonProgress,
    PasswordReset,
    User,
)
from be.web_security import create_access_token, decode_access_token, hash_password, verify_password


load_dotenv(ROOT / ".env")
MODEL_PATH = Path(os.getenv("SENTIMENT_MODEL_PATH", ROOT / "data/models/svm_tfidf.joblib"))
VECTORIZER_PATH = Path(
    os.getenv("SENTIMENT_VECTORIZER_PATH", ROOT / "data/processed/vectorized/tfidf_vectorizer.joblib")
)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(ROOT / 'data/edupulse.db').as_posix()}")
APP_SECRET = os.getenv("APP_SECRET_KEY", "change-this-development-secret-before-deployment")
APP_ENV = os.getenv("APP_ENV", "development").lower()
LABELS = {0: "Tiêu cực", 1: "Trung tính", 2: "Tích cực"}


def _make_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
bearer = HTTPBearer(auto_error=False)
app = FastAPI(title="E-learning Sentiment Analysis API", version="2.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "app/fe"), name="static")
_model = None
_vectorizer = None


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)


class CategoryInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)


class CourseInput(BaseModel):
    category_id: int
    title: str = Field(min_length=3, max_length=200)
    instructor: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=5)
    thumbnail_url: str | None = Field(default=None, max_length=1000)
    is_published: bool = False


class LessonInput(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=1000)
    video_url: str = Field(min_length=8, max_length=1000)
    position: int = Field(ge=1)
    duration_seconds: int = Field(default=0, ge=0)


class FeedbackInput(BaseModel):
    text: str = Field(min_length=3, max_length=5000)
    rating: int = Field(ge=1, le=5)
    course_id: int
    lesson_id: int | None = None


class ModerationInput(BaseModel):
    status: str = Field(pattern="^(visible|hidden)$")


class RoleInput(BaseModel):
    role: str = Field(pattern="^(student|admin)$")


def get_db():
    with SessionLocal() as session:
        yield session


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Vui lòng đăng nhập.")
    payload = decode_access_token(credentials.credentials, APP_SECRET)
    if not payload:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập hết hạn hoặc không hợp lệ.")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Tài khoản không tồn tại hoặc đã bị khóa.")
    return user


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials, APP_SECRET)
    if not payload:
        return None
    user = db.get(User, int(payload["sub"]))
    return user if user is not None and user.is_active else None


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền quản trị.")
    return user


def user_json(user: User) -> dict:
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}


def category_json(category: Category) -> dict:
    return {"id": category.id, "name": category.name, "description": category.description}


def lesson_json(lesson: Lesson, completed: bool = False) -> dict:
    return {
        "id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "video_url": lesson.video_url,
        "position": lesson.position,
        "duration_seconds": lesson.duration_seconds,
        "completed": completed,
    }


def course_json(db: Session, course: Course, user_id: int | None = None) -> dict:
    lessons = list(db.scalars(select(Lesson).where(Lesson.course_id == course.id).order_by(Lesson.position)))
    completed_ids: set[int] = set()
    enrolled = False
    if user_id is not None:
        enrolled = db.scalar(
            select(Enrollment.id).where(Enrollment.user_id == user_id, Enrollment.course_id == course.id)
        ) is not None
        completed_ids = set(
            db.scalars(
                select(LessonProgress.lesson_id).where(
                    LessonProgress.user_id == user_id,
                    LessonProgress.is_completed == true(),
                    LessonProgress.lesson_id.in_([lesson.id for lesson in lessons] or [-1]),
                )
            )
        )
    completed = sum(lesson.id in completed_ids for lesson in lessons)
    return {
        "id": course.id,
        "category_id": course.category_id,
        "category": category_json(course.category),
        "title": course.title,
        "instructor": course.instructor,
        "description": course.description,
        "thumbnail_url": course.thumbnail_url,
        "is_published": course.is_published,
        "lesson_count": len(lessons),
        "enrolled": enrolled,
        "completed_lessons": completed,
        "progress_percent": round(completed / len(lessons) * 100) if lessons else 0,
        "lessons": [lesson_json(lesson, lesson.id in completed_ids) for lesson in lessons],
    }


def _predict(text: str) -> int:
    if _model is None or _vectorizer is None:
        raise HTTPException(status_code=503, detail="Mô hình cảm xúc chưa sẵn sàng.")
    cleaned = clean_text(text)
    if len(cleaned) < 3:
        raise HTTPException(status_code=422, detail="Vui lòng nhập nội dung đánh giá rõ hơn.")
    features = _vectorizer.transform([segment_text(cleaned)])
    label = int(_model.predict(features)[0])
    if label not in LABELS:
        raise HTTPException(status_code=500, detail="Mô hình trả về nhãn không hợp lệ.")
    return label


def _feedback_ready(db: Session, user: User, course_id: int, lesson_id: int | None) -> None:
    enrolled = db.scalar(
        select(Enrollment.id).where(Enrollment.user_id == user.id, Enrollment.course_id == course_id)
    )
    if enrolled is None:
        raise HTTPException(status_code=403, detail="Bạn cần tham gia khóa học trước khi đánh giá.")
    if lesson_id is not None:
        lesson = db.get(Lesson, lesson_id)
        if lesson is None or lesson.course_id != course_id:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng trong khóa học này.")
        done = db.scalar(
            select(LessonProgress.id).where(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.is_completed == true(),
            )
        )
        if done is None:
            raise HTTPException(status_code=403, detail="Hãy hoàn thành bài giảng trước khi đánh giá.")
        return
    lesson_ids = list(db.scalars(select(Lesson.id).where(Lesson.course_id == course_id)))
    if not lesson_ids:
        raise HTTPException(status_code=400, detail="Khóa học chưa có bài giảng để xác nhận hoàn thành.")
    done_count = db.scalar(
        select(func.count(LessonProgress.id)).where(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id.in_(lesson_ids),
            LessonProgress.is_completed == true(),
        )
    )
    if done_count != len(lesson_ids):
        raise HTTPException(status_code=403, detail="Hãy hoàn thành toàn bộ khóa học trước khi đánh giá khóa học.")


def _feedback_json(db: Session, feedback: Feedback) -> dict:
    user = db.get(User, feedback.user_id)
    course = db.get(Course, feedback.course_id)
    lesson = db.get(Lesson, feedback.lesson_id) if feedback.lesson_id else None
    return {
        "id": feedback.id,
        "user_id": feedback.user_id,
        "student_name": user.full_name if user else "",
        "course_id": feedback.course_id,
        "course_title": course.title if course else "",
        "lesson_id": feedback.lesson_id,
        "lesson_title": lesson.title if lesson else None,
        "rating": feedback.rating,
        "text": feedback.text,
        "sentiment": feedback.sentiment,
        "sentiment_label": LABELS[feedback.sentiment],
        "moderation_status": feedback.moderation_status,
        "created_at": feedback.created_at.isoformat(),
    }


def _send_reset_email(to_email: str, token: str) -> bool:
    host = os.getenv("SMTP_HOST")
    if not host:
        return False
    message = EmailMessage()
    message["Subject"] = "Đặt lại mật khẩu E-learning"
    message["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "no-reply@example.local"))
    message["To"] = to_email
    message.set_content(f"Mã đặt lại mật khẩu của bạn: {token}\nMã hết hạn sau 30 phút.")
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
        smtp.starttls()
        if os.getenv("SMTP_USER"):
            smtp.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
        smtp.send_message(message)
    return True


@app.on_event("startup")
def initialize_app() -> None:
    global _model, _vectorizer
    if DATABASE_URL.startswith("sqlite"):
        (ROOT / "data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    if not MODEL_PATH.is_file() or not VECTORIZER_PATH.is_file():
        raise RuntimeError(
            "Model artifacts are missing. Run preprocessing and train-svm first; "
            f"expected {MODEL_PATH} and {VECTORIZER_PATH}."
        )
    _model = joblib.load(MODEL_PATH)
    _vectorizer = joblib.load(VECTORIZER_PATH)
    if getattr(_model, "n_features_in_", None) != len(_vectorizer.vocabulary_):
        raise RuntimeError("Model and TF-IDF vectorizer dimensions do not match; regenerate both artifacts.")


@app.get("/", include_in_schema=False)
def student_frontend():
    return FileResponse(ROOT / "app/fe" / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_frontend():
    return FileResponse(ROOT / "app/fe" / "admin.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL_PATH.name, "database": engine.dialect.name}


# Account and session endpoints
@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email này đã được đăng ký.")
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role="student",
        is_active=True,
        created_at=now_utc(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role, APP_SECRET)
    return {"access_token": token, "token_type": "bearer", "user": user_json(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
    token = create_access_token(user.id, user.role, APP_SECRET)
    return {"access_token": token, "token_type": "bearer", "user": user_json(user)}


@app.get("/api/auth/me")
def me(user: User = Depends(require_user)):
    return user_json(user)


@app.patch("/api/auth/profile")
def update_profile(payload: ProfileRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    user.full_name = payload.full_name.strip()
    db.commit()
    return user_json(user)


@app.post("/api/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email, User.is_active == true()))
    result: dict[str, str | None] = {"message": "Nếu email tồn tại, hướng dẫn đặt lại mật khẩu sẽ được gửi."}
    if user is not None:
        token = os.urandom(32).hex()
        reset = PasswordReset(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=now_utc() + timedelta(minutes=30),
        )
        db.add(reset)
        db.commit()
        sent = _send_reset_email(email, token)
        if not sent and APP_ENV == "development":
            result["development_token"] = token
    return result


@app.post("/api/auth/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.token_hash == token_hash,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > now_utc(),
        )
    )
    if reset is None:
        raise HTTPException(status_code=400, detail="Mã đặt lại không hợp lệ hoặc đã hết hạn.")
    user = db.get(User, reset.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Tài khoản không còn tồn tại.")
    user.password_hash = hash_password(payload.new_password)
    reset.used_at = now_utc()
    db.commit()
    return {"message": "Đã cập nhật mật khẩu. Bạn có thể đăng nhập lại."}


# Public course catalog and student learning endpoints
@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db)):
    return [category_json(item) for item in db.scalars(select(Category).order_by(Category.name))]


@app.get("/api/courses")
def list_courses(
    q: str | None = None,
    category_id: int | None = None,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    statement = select(Course).where(Course.is_published == true())
    if q:
        statement = statement.where(Course.title.ilike(f"%{q.strip()}%"))
    if category_id:
        statement = statement.where(Course.category_id == category_id)
    courses = list(db.scalars(statement.order_by(Course.created_at.desc())))
    return [course_json(db, course, user.id if user else None) for course in courses]


@app.get("/api/student/courses")
def student_courses(user: User = Depends(require_user), db: Session = Depends(get_db)):
    courses = db.scalars(
        select(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == user.id)
        .order_by(Course.title)
    )
    return [course_json(db, course, user.id) for course in courses]


@app.get("/api/courses/{course_id}")
def course_detail(
    course_id: int,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None or not course.is_published:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học.")
    return course_json(db, course, user.id if user else None)


@app.post("/api/courses/{course_id}/enroll", status_code=201)
def enroll(course_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if course is None or not course.is_published:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học.")
    exists = db.scalar(select(Enrollment.id).where(Enrollment.user_id == user.id, Enrollment.course_id == course_id))
    if exists is None:
        db.add(Enrollment(user_id=user.id, course_id=course_id, enrolled_at=now_utc()))
        db.commit()
    return {"message": "Đã ghi danh khóa học."}


@app.put("/api/student/lessons/{lesson_id}/progress")
def set_progress(
    lesson_id: int,
    completed: bool = True,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")
    enrolled = db.scalar(
        select(Enrollment.id).where(Enrollment.user_id == user.id, Enrollment.course_id == lesson.course_id)
    )
    if enrolled is None:
        raise HTTPException(status_code=403, detail="Hãy ghi danh khóa học trước.")
    progress = db.scalar(
        select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id)
    )
    if progress is None:
        progress = LessonProgress(user_id=user.id, lesson_id=lesson_id, is_completed=completed, updated_at=now_utc())
        db.add(progress)
    else:
        progress.is_completed = completed
        progress.updated_at = now_utc()
    db.commit()
    return {"lesson_id": lesson_id, "completed": completed}


# Student feedback lifecycle
@app.get("/api/student/feedback")
def own_feedback(user: User = Depends(require_user), db: Session = Depends(get_db)):
    records = db.scalars(select(Feedback).where(Feedback.user_id == user.id).order_by(Feedback.created_at.desc()))
    return [_feedback_json(db, row) for row in records]


@app.post("/api/feedback", status_code=201)
def create_feedback(payload: FeedbackInput, user: User = Depends(require_user), db: Session = Depends(get_db)):
    _feedback_ready(db, user, payload.course_id, payload.lesson_id)
    already = db.scalar(
        select(Feedback.id).where(
            Feedback.user_id == user.id,
            Feedback.course_id == payload.course_id,
            Feedback.lesson_id == payload.lesson_id if payload.lesson_id is not None else Feedback.lesson_id.is_(None),
        )
    )
    if already:
        raise HTTPException(status_code=409, detail="Bạn đã gửi đánh giá cho nội dung này; hãy sửa đánh giá hiện có.")
    cleaned = clean_text(payload.text)
    record = Feedback(
        user_id=user.id,
        course_id=payload.course_id,
        lesson_id=payload.lesson_id,
        rating=payload.rating,
        text=cleaned,
        sentiment=_predict(cleaned),
        moderation_status="visible",
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _feedback_json(db, record)


@app.put("/api/feedback/{feedback_id}")
def update_feedback(
    feedback_id: int,
    payload: FeedbackInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    record = db.get(Feedback, feedback_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá của bạn.")
    if (record.course_id, record.lesson_id) != (payload.course_id, payload.lesson_id):
        raise HTTPException(status_code=400, detail="Không thể chuyển đánh giá sang nội dung khác.")
    _feedback_ready(db, user, payload.course_id, payload.lesson_id)
    record.text = clean_text(payload.text)
    record.rating = payload.rating
    record.sentiment = _predict(record.text)
    record.moderation_status = "visible"
    record.updated_at = now_utc()
    db.commit()
    return _feedback_json(db, record)


@app.delete("/api/feedback/{feedback_id}", status_code=204)
def delete_feedback(feedback_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    record = db.get(Feedback, feedback_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá của bạn.")
    db.delete(record)
    db.commit()


@app.get("/api/courses/{course_id}/feedback")
def public_course_feedback(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if course is None or not course.is_published:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học.")
    records = db.scalars(
        select(Feedback)
        .where(
            Feedback.course_id == course_id,
            Feedback.lesson_id.is_(None),
            Feedback.moderation_status == "visible",
        )
        .order_by(Feedback.created_at.desc())
    )
    return [
        {k: v for k, v in _feedback_json(db, row).items() if k not in {"user_id"}}
        for row in records
    ]


# Administrator endpoints
@app.get("/api/admin/categories")
def admin_categories(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [category_json(item) for item in db.scalars(select(Category).order_by(Category.name))]


@app.post("/api/admin/categories", status_code=201)
def create_category(payload: CategoryInput, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.scalar(select(Category.id).where(Category.name == payload.name.strip())):
        raise HTTPException(status_code=409, detail="Danh mục đã tồn tại.")
    item = Category(name=payload.name.strip(), description=payload.description.strip())
    db.add(item)
    db.commit()
    db.refresh(item)
    return category_json(item)


@app.put("/api/admin/categories/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryInput,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    item = db.get(Category, category_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục.")
    item.name, item.description = payload.name.strip(), payload.description.strip()
    db.commit()
    return category_json(item)


@app.delete("/api/admin/categories/{category_id}", status_code=204)
def delete_category(category_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(Category, category_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục.")
    if db.scalar(select(Course.id).where(Course.category_id == category_id)):
        raise HTTPException(status_code=409, detail="Danh mục đang có khóa học; hãy chuyển hoặc xóa khóa học trước.")
    db.delete(item)
    db.commit()


@app.get("/api/admin/courses")
def admin_courses(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [course_json(db, course) for course in db.scalars(select(Course).order_by(Course.created_at.desc()))]


@app.post("/api/admin/courses", status_code=201)
def create_course(payload: CourseInput, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=400, detail="Danh mục không tồn tại.")
    course = Course(**payload.model_dump(), created_at=now_utc(), updated_at=now_utc())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course_json(db, course)


@app.put("/api/admin/courses/{course_id}")
def update_course(
    course_id: int,
    payload: CourseInput,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học.")
    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=400, detail="Danh mục không tồn tại.")
    for key, value in payload.model_dump().items():
        setattr(course, key, value)
    course.updated_at = now_utc()
    db.commit()
    return course_json(db, course)


@app.delete("/api/admin/courses/{course_id}", status_code=204)
def delete_course(course_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học.")
    lesson_ids = list(db.scalars(select(Lesson.id).where(Lesson.course_id == course_id)))
    for feedback in db.scalars(select(Feedback).where(Feedback.course_id == course_id)):
        db.delete(feedback)
    if lesson_ids:
        for progress in db.scalars(select(LessonProgress).where(LessonProgress.lesson_id.in_(lesson_ids))):
            db.delete(progress)
    for enrollment in db.scalars(select(Enrollment).where(Enrollment.course_id == course_id)):
        db.delete(enrollment)
    for lesson in db.scalars(select(Lesson).where(Lesson.course_id == course_id)):
        db.delete(lesson)
    db.delete(course)
    db.commit()


@app.post("/api/admin/courses/{course_id}/lessons", status_code=201)
def create_lesson(
    course_id: int,
    payload: LessonInput,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học.")
    lesson = Lesson(course_id=course_id, **payload.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson_json(lesson)


@app.put("/api/admin/lessons/{lesson_id}")
def update_lesson(
    lesson_id: int,
    payload: LessonInput,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")
    for feedback in db.scalars(select(Feedback).where(Feedback.lesson_id == lesson_id)):
        db.delete(feedback)
    for progress in db.scalars(select(LessonProgress).where(LessonProgress.lesson_id == lesson_id)):
        db.delete(progress)
    for key, value in payload.model_dump().items():
        setattr(lesson, key, value)
    db.commit()
    return lesson_json(lesson)


@app.delete("/api/admin/lessons/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài giảng.")
    db.delete(lesson)
    db.commit()


@app.get("/api/admin/users")
def admin_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [
        {**user_json(user), "is_active": user.is_active, "created_at": user.created_at.isoformat()}
        for user in db.scalars(select(User).order_by(User.created_at.desc()))
    ]


@app.patch("/api/admin/users/{user_id}/role")
def set_user_role(
    user_id: int,
    payload: RoleInput,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản.")
    if admin.id == user.id and payload.role != "admin":
        raise HTTPException(status_code=400, detail="Không thể tự hạ quyền tài khoản đang đăng nhập.")
    user.role = payload.role
    db.commit()
    return user_json(user)


@app.patch("/api/admin/users/{user_id}/active")
def set_user_active(
    user_id: int,
    active: bool,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản.")
    if user.id == admin.id and not active:
        raise HTTPException(status_code=400, detail="Không thể khóa tài khoản quản trị đang đăng nhập.")
    user.is_active = active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@app.get("/api/admin/feedback")
def admin_feedback(
    sentiment: int | None = Query(default=None, ge=0, le=2),
    status: str | None = Query(default=None, pattern="^(visible|hidden)$"),
    course_id: int | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    statement = select(Feedback).order_by(Feedback.created_at.desc())
    if sentiment is not None:
        statement = statement.where(Feedback.sentiment == sentiment)
    if status:
        statement = statement.where(Feedback.moderation_status == status)
    if course_id:
        statement = statement.where(Feedback.course_id == course_id)
    return [_feedback_json(db, record) for record in db.scalars(statement.limit(500))]


@app.patch("/api/admin/feedback/{feedback_id}/moderation")
def moderate_feedback(
    feedback_id: int,
    payload: ModerationInput,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    record = db.get(Feedback, feedback_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản hồi.")
    record.moderation_status = payload.status
    record.updated_at = now_utc()
    db.commit()
    return _feedback_json(db, record)


@app.delete("/api/admin/feedback/{feedback_id}", status_code=204)
def admin_delete_feedback(feedback_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    record = db.get(Feedback, feedback_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phản hồi.")
    db.delete(record)
    db.commit()


@app.get("/api/admin/dashboard")
def dashboard(
    from_date: date | None = None,
    to_date: date | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    statement = select(Feedback).where(Feedback.moderation_status == "visible")
    start = datetime.combine(from_date, datetime.min.time()) if from_date else None
    end = datetime.combine(to_date + timedelta(days=1), datetime.min.time()) if to_date else None
    if start:
        statement = statement.where(Feedback.created_at >= start)
    if end:
        statement = statement.where(Feedback.created_at < end)
    records = list(db.scalars(statement.order_by(Feedback.created_at)))
    by_course: dict[int, dict] = {}
    by_day: dict[str, dict[int, int]] = {}
    overall = {label: 0 for label in LABELS}
    for record in records:
        course = db.get(Course, record.course_id)
        title = course.title if course else f"Khóa học {record.course_id}"
        entry = by_course.setdefault(record.course_id, {"course_id": record.course_id, "course_title": title, **{f"sentiment_{i}": 0 for i in LABELS}})
        entry[f"sentiment_{record.sentiment}"] += 1
        overall[record.sentiment] += 1
        day = record.created_at.date().isoformat()
        by_day.setdefault(day, {label: 0 for label in LABELS})[record.sentiment] += 1
    courses = []
    for entry in by_course.values():
        total = sum(entry[f"sentiment_{i}"] for i in LABELS)
        courses.append({
            **entry,
            "total": total,
            "percentages": {
                i: round(entry[f"sentiment_{i}"] / total * 100, 1) if total else 0 for i in LABELS
            },
        })
    trend = [
        {"date": day, **{str(label): count for label, count in counts.items()}}
        for day, counts in sorted(by_day.items())
    ]
    total = len(records)
    return {
        "total": total,
        "overall": [
            {"id": label, "label": LABELS[label], "count": overall[label], "percent": round(overall[label] / total * 100, 1) if total else 0}
            for label in LABELS
        ],
        "courses": sorted(courses, key=lambda item: item["total"], reverse=True),
        "trend": trend,
    }


