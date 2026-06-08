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


class Program(Base):
    __tablename__ = "programs"

    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    exercise_mappings = relationship("ProgramExercise", back_populates="program", cascade="all, delete-orphan")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    category = Column(Text)
    equipment = Column(Text)
    primary_muscle = Column(Text)
    secondary_muscle = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    substitutions = relationship(
        "ExerciseSubstitution",
        foreign_keys="[ExerciseSubstitution.exercise_id]",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )
    substitution_targets = relationship(
        "ExerciseSubstitution",
        foreign_keys="[ExerciseSubstitution.substitute_exercise_id]",
        back_populates="substitute_exercise",
        cascade="all, delete-orphan",
    )


class ProgramExercise(Base):
    __tablename__ = "program_exercise_mappings"

    id = Column(BigInteger, primary_key=True, index=True)
    program_id = Column(BigInteger, ForeignKey("programs.id"), nullable=False)
    exercise_id = Column(BigInteger, ForeignKey("exercises.id"), nullable=False)
    day = Column(Text)
    sequence = Column(Integer, nullable=False, default=1)
    sets = Column(Integer)
    reps = Column(Text)
    duration = Column(Text)
    notes = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    program = relationship("Program", back_populates="exercise_mappings")
    exercise = relationship("Exercise")


class Restriction(Base):
    __tablename__ = "restrictions"

    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    substitutions = relationship("ExerciseSubstitution", back_populates="restriction", cascade="all, delete-orphan")


class ExerciseSubstitution(Base):
    __tablename__ = "exercise_substitutions"

    id = Column(BigInteger, primary_key=True, index=True)
    restriction_id = Column(BigInteger, ForeignKey("restrictions.id"), nullable=False)
    exercise_id = Column(BigInteger, ForeignKey("exercises.id"), nullable=False)
    substitute_exercise_id = Column(BigInteger, ForeignKey("exercises.id"), nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    restriction = relationship("Restriction", back_populates="substitutions")
    exercise = relationship(
        "Exercise",
        foreign_keys="[ExerciseSubstitution.exercise_id]",
        back_populates="substitutions",
    )
    substitute_exercise = relationship(
        "Exercise",
        foreign_keys="[ExerciseSubstitution.substitute_exercise_id]",
        back_populates="substitution_targets",
    )


class ClassificationRule(Base):
    __tablename__ = "classification_rules"

    id = Column(BigInteger, primary_key=True, index=True)
    pbf_min = Column(Numeric, nullable=False, default=0)
    pbf_max = Column(Numeric)
    smm_key = Column(Text)
    classification = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RecommendationRule(Base):
    __tablename__ = "recommendation_rules"

    id = Column(BigInteger, primary_key=True, index=True)
    classification = Column(Text, nullable=False)
    goal_key = Column(Text)
    recommendation = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ProgramRule(Base):
    __tablename__ = "program_rules"

    id = Column(BigInteger, primary_key=True, index=True)
    classification = Column(Text, nullable=False)
    restriction_code = Column(Text)
    program_code = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
