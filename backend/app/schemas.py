from pydantic import BaseModel


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
