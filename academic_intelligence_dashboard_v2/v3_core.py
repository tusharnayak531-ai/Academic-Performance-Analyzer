"""V3: user-isolated persistence, secure passwords and grade calculations."""
import hashlib
import hmac
import os
import secrets
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
COMPONENTS = ("cie", "midsem", "practical", "ese_pr", "ese")
DEFAULT_MAX = dict(cie=20, midsem=20, practical=50, ese_pr=30, ese=40)
DEFAULT_THRESHOLDS = [(90, 10), (80, 9), (70, 8), (60, 7), (50, 6), (40, 5), (0, 0)]


class User(Base):
    __tablename__ = "v3_users"
    id = Column(Integer, primary_key=True)
    username = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(300), nullable=False)


class Mark(Base):
    __tablename__ = "v3_marks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("v3_users.id"), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    subject = Column(String(180), nullable=False)
    credits = Column(Float, nullable=False, default=3)
    cie = Column(Float, default=0)
    midsem = Column(Float, default=0)
    practical = Column(Float, default=0)
    ese_pr = Column(Float, default=0)
    ese = Column(Float, default=0)
    max_cie = Column(Float, default=20)
    max_midsem = Column(Float, default=20)
    max_practical = Column(Float, default=50)
    max_ese_pr = Column(Float, default=30)
    max_ese = Column(Float, default=40)
    __table_args__ = (UniqueConstraint("user_id", "semester", "subject"),)


class Attendance(Base):
    __tablename__ = "v3_attendance"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("v3_users.id"), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    subject = Column(String(180), nullable=False)
    attended = Column(Integer, default=0)
    total = Column(Integer, default=0)
    __table_args__ = (UniqueConstraint("user_id", "semester", "subject"),)


class Assignment(Base):
    __tablename__ = "v3_assignments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("v3_users.id"), nullable=False, index=True)
    subject = Column(String(180), nullable=False)
    title = Column(String(250), nullable=False)
    due_date = Column(Date)
    status = Column(String(40), default="Pending")


class Goal(Base):
    __tablename__ = "v3_goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("v3_users.id"), nullable=False, index=True)
    title = Column(String(250), nullable=False)
    target_value = Column(Float, default=0)
    current_value = Column(Float, default=0)
    unit = Column(String(25), default="%")


class Backlog(Base):
    __tablename__ = "v3_backlogs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("v3_users.id"), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    subject = Column(String(180), nullable=False)
    component = Column(String(100), nullable=False)
    status = Column(String(30), default="Pending")
    attempts = Column(Integer, default=1)
    __table_args__ = (UniqueConstraint("user_id", "semester", "subject", "component"),)


class GradeRule(Base):
    __tablename__ = "v3_grade_rules"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("v3_users.id"), nullable=False, index=True)
    minimum = Column(Float, nullable=False)
    point = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "minimum"),)


def configured_url():
    value = os.getenv("DATABASE_URL", "").strip()
    if value.startswith("postgres://"):
        value = "postgresql+psycopg://" + value[len("postgres://"):]
    elif value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://"):]
    if value:
        return value
    return "sqlite:///" + os.getenv("V3_SQLITE_PATH", str(Path(__file__).parent / "academic_v3.db"))


def durable_storage():
    return bool(os.getenv("DATABASE_URL", "").strip() or os.getenv("V3_SQLITE_PERSISTENT", "") == "1")


def create_store(url=None):
    db_url = url or configured_url()
    engine = create_engine(db_url, pool_pre_ping=True, connect_args={"check_same_thread": False}
                           if db_url.startswith("sqlite:") else {})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False), engine


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return "pbkdf2_sha256$260000$" + salt.hex() + "$" + digest.hex()


def verify_password(password, encoded):
    try:
        algorithm, n, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(n) > 500000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(n))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError, AttributeError):
        return False


def register(session, username, password):
    username = username.strip().lower()
    if len(username) < 3 or len(username) > 120 or not all(c.isalnum() or c in "._-@" for c in username):
        raise ValueError("Username needs 3–120 letters, numbers, dots, dashes or underscores.")
    if len(password) < 8:
        raise ValueError("Password needs at least 8 characters.")
    if session.scalar(select(User).where(User.username == username)):
        raise ValueError("Username already exists.")
    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    session.flush()
    session.add_all([GradeRule(user_id=user.id, minimum=m, point=p) for m, p in DEFAULT_THRESHOLDS])
    session.commit()
    return user


def authenticate(session, username, password):
    user = session.scalar(select(User).where(User.username == username.strip().lower()))
    return user if user and verify_password(password, user.password_hash) else None


def owned(session, model, user_id):
    return session.scalars(select(model).where(model.user_id == user_id)).all()


def delete_owned(session, model, user_id, record_id):
    item = session.scalar(select(model).where(model.id == record_id, model.user_id == user_id))
    if item is None:
        return False
    session.delete(item)
    session.commit()
    return True


def validate_mark(data):
    sem, name, credits = int(data["semester"]), str(data["subject"]).strip(), float(data["credits"])
    if not name or not 1 <= sem <= 12 or not 0 <= credits <= 20:
        raise ValueError("Supply a subject, semester from 1–12 and credits from 0–20.")
    for component in COMPONENTS:
        score, maximum = float(data[component]), float(data["max_" + component])
        if not (0 <= maximum <= 200 and 0 <= score <= maximum):
            raise ValueError("Invalid " + component + " marks for " + name)


def stage_mark(session, user_id, data):
    validate_mark(data)
    semester, subject = int(data["semester"]), str(data["subject"]).strip()
    item = session.scalar(select(Mark).where(Mark.user_id == user_id,
                                             Mark.semester == semester, Mark.subject == subject))
    if item is None:
        item = Mark(user_id=user_id, semester=semester, subject=subject)
        session.add(item)
    for field in ("semester", "subject", "credits") + COMPONENTS + tuple("max_" + k for k in COMPONENTS):
        setattr(item, field, data[field])
    return item


def save_mark(session, user_id, data):
    item = stage_mark(session, user_id, data)
    session.commit()
    return item


def import_marks(session, user_id, frame):
    needed = ("semester", "subject", "credits") + COMPONENTS + tuple("max_" + k for k in COMPONENTS)
    missing = set(needed) - set(frame.columns)
    if missing or frame.empty or frame[list(needed)].isnull().any().any():
        raise ValueError("CSV must contain all V3 mark columns, valid rows and no blanks.")
    seen = set()
    # Validate entire file before any writes, including duplicates.
    for _, row in frame.iterrows():
        data = row.to_dict()
        validate_mark(data)
        key = (int(data["semester"]), str(data["subject"]).strip())
        if key in seen:
            raise ValueError("Duplicate CSV subject: " + str(key))
        seen.add(key)
    for _, row in frame.iterrows():
        stage_mark(session, user_id, row.to_dict())
    session.commit()
    return len(frame)


def rules(session, user_id):
    return sorted([(float(r.minimum), float(r.point)) for r in owned(session, GradeRule, user_id)],
                  key=lambda x: -x[0])


def grade_point(percent, thresholds):
    for boundary, point in sorted(thresholds, key=lambda x: -x[0]):
        if percent >= boundary:
            return float(point)
    return 0.0


def marks_frame(records, thresholds):
    fields = ("id", "semester", "subject", "credits") + COMPONENTS + tuple("max_" + k for k in COMPONENTS)
    df = pd.DataFrame([{key: getattr(mark, key) for key in fields} for mark in records], columns=list(fields))
    if df.empty:
        return df
    for field in COMPONENTS + tuple("max_" + k for k in COMPONENTS) + ("credits",):
        df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0)
    df["obtained"] = df[list(COMPONENTS)].sum(axis=1)
    df["maximum"] = df[["max_" + k for k in COMPONENTS]].sum(axis=1)
    df["percentage"] = np.where(df.maximum > 0, df.obtained / df.maximum * 100, 0)
    df["grade_point"] = df.percentage.apply(lambda p: grade_point(p, thresholds))
    df["status"] = np.where(df.grade_point > 0, "Pass (estimated)", "Review")
    return df


def summary(df):
    if df.empty:
        return pd.DataFrame(columns=["semester", "percentage", "sgpa", "credits"])
    temp = df.copy()
    temp["weighted"] = temp.grade_point * temp.credits
    out = temp.groupby("semester", as_index=False).agg(percentage=("percentage", "mean"),
                weighted=("weighted", "sum"), credits=("credits", "sum"))
    out["sgpa"] = np.where(out.credits > 0, out.weighted / out.credits, 0)
    return out.drop(columns=["weighted"])


def cgpa(df):
    return float((df.grade_point * df.credits).sum() / df.credits.sum()) if not df.empty and df.credits.sum() > 0 else 0.0


def required_marks(current, completed_max, remaining_max, target_percentage):
    if min(current, completed_max, remaining_max) < 0 or current > completed_max:
        raise ValueError("Current marks cannot exceed completed maximum.")
    if not 0 <= target_percentage <= 100:
        raise ValueError("Target must be 0–100%.")
    required = (completed_max + remaining_max) * target_percentage / 100 - current
    return {"required": max(0.0, required), "possible": required <= remaining_max,
            "maximum_percentage": 100 * (current + remaining_max) / (completed_max + remaining_max)
            if completed_max + remaining_max else 0}


def plan_target(df, thresholds, semester, target_sgpa):
    current = df[df.semester == semester] if not df.empty else pd.DataFrame()
    if current.empty:
        return pd.DataFrame()
    rows = []
    for _, x in current.iterrows():
        gap = max(0.0, x.maximum * 0.80 - x.obtained)
        rows.append({"Subject": x.subject, "Current %": round(x.percentage, 1),
                     "Current GP": x.grade_point, "Marks to 9 GP (demo scale)": round(gap, 1),
                     "Available marks": round(max(0.0, x.maximum - x.obtained), 1)})
    return pd.DataFrame(rows)


def predict_subjects(df):
    if df.empty:
        return pd.DataFrame()
    rows = []
    for subject, group in df.groupby("subject"):
        group = group.sort_values("semester")
        if len(group) < 2 or group.semester.nunique() < 2:
            continue
        x, y = group.semester.to_numpy(float), group.percentage.to_numpy(float)
        slope = float(np.polyfit(x, y, 1)[0])
        rows.append({"Subject": subject, "Latest %": round(y[-1], 1),
                     "Next estimated %": round(float(np.clip(y[-1] + slope, 0, 100)), 1),
                     "History": len(group)})
    return pd.DataFrame(rows)
