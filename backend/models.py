from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(Text, unique=True, nullable=False)
    email = Column(Text, unique=True)
    hashed_password = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(Text, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="assessments")
    episodes = relationship("Episode", back_populates="assessment", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(BigInteger, primary_key=True, index=True)
    assessment_id = Column(BigInteger, ForeignKey("assessments.id"), nullable=False)
    name = Column(Text, nullable=False)
    sequence = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    assessment = relationship("Assessment", back_populates="episodes")
    outcomes = relationship("Outcome", back_populates="episode", cascade="all, delete-orphan")


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(BigInteger, primary_key=True, index=True)
    episode_id = Column(BigInteger, ForeignKey("episodes.id"), nullable=False)
    name = Column(Text, nullable=False)
    result = Column(JSON)
    score = Column(Numeric)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    episode = relationship("Episode", back_populates="outcomes")


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    episode_id = Column(BigInteger, ForeignKey("episodes.id"), nullable=True)
    program = Column(Text, nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    episode = relationship("Episode")
    user = relationship("User")
