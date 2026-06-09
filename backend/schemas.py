from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerateEpisodeRequest(BaseModel):
    pbf: float
    smm: str
    goal: str
    restriction: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    assessment_title: Optional[str] = None


class GenerateEpisodeResponse(BaseModel):
    classification: str
    recommendation: str
    program: str
    episode_id: Optional[int] = None
    assessment_id: Optional[int] = None


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "CLIENT"


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class GenerateWorkoutRequest(BaseModel):
    program: str
    goal: str
    restriction: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    episode_id: Optional[int] = None


class WorkoutResponse(BaseModel):
    workout_id: int = Field(alias="id")
    user_id: Optional[int] = None
    episode_id: Optional[int] = None
    program: str
    details: dict

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OutcomeResponse(BaseModel):
    id: int
    episode_id: int
    name: str
    result: dict
    score: Optional[float]

    class Config:
        from_attributes = True


class EpisodeResponse(BaseModel):
    id: int
    assessment_id: int
    name: str
    sequence: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    outcomes: list[OutcomeResponse] = []

    class Config:
        from_attributes = True
