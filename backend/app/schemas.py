from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Topic(BaseModel):
    id: int
    title: str
    description: str | None = None
    icon: str | None = None
    order: int
    is_published: bool


class Lesson(BaseModel):
    id: int
    topic_id: int
    title: str
    order: int
    content: list
    is_published: bool


class Quiz(BaseModel):
    id: int
    lesson_id: int | None = None
    title: str
    questions: list
    is_published: bool


class LessonStep(BaseModel):
    """One card of a lesson: text with an optional emoji and an optional picture."""

    type: Literal["text", "image"] = "text"
    text: str = ""
    emoji: str | None = None
    image_url: str | None = None


class QuizQuestion(BaseModel):
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2)
    correct_index: int
    explanation: str | None = None

    @model_validator(mode="after")
    def correct_index_in_range(self):
        if not 0 <= self.correct_index < len(self.options):
            raise ValueError("correct_index must point to one of the options")
        return self


class TopicCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    icon: str | None = None
    order: int = 0
    is_published: bool = False


class LessonCreate(BaseModel):
    topic_id: int
    title: str = Field(min_length=1)
    order: int = 0
    content: list[LessonStep] = []
    is_published: bool = False


class QuizCreate(BaseModel):
    lesson_id: int | None = None
    title: str = Field(min_length=1)
    questions: list[QuizQuestion] = []
    is_published: bool = False


class BroadcastIn(BaseModel):
    text: str = Field(min_length=1)
    only_inactive_days: int | None = Field(default=None, ge=1)


class ProgressIn(BaseModel):
    lesson_id: int | None = None
    quiz_id: int | None = None
    quiz_score: int | None = None


class ProgressOut(BaseModel):
    lesson_id: int | None = None
    quiz_id: int | None = None
    quiz_score: int | None = None
    completed_at: str | None = None
    last_activity_at: str


class NotificationsIn(BaseModel):
    enabled: bool
