from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator


class QuestGenerateRequest(BaseModel):
    location: str = Field(..., min_length=2, description="City or region name")
    available_time: int = Field(
        ...,
        ge=15,
        le=180,
        description="Time available in minutes (15–180)",
    )
    activity: str = Field(..., min_length=2, description="Activity type e.g., walking, hiking")
    difficulty: str = Field(..., min_length=2, description="Difficulty level e.g., easy, moderate, hard")
    interests: Optional[str] = Field("", description="Optional user interests e.g., nature, photography")

    @field_validator("location", "activity", "difficulty")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return value.strip()


class QuestResponse(BaseModel):
    id: Optional[str] = None
    quest_id: Optional[str] = None
    title: str
    location: str
    address: Optional[str] = None
    estimated_duration: int
    difficulty: str
    description: str
    objectives: List[str]
    safety_note: str


class QuestCompletionRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(completed|partially_completed|not_completed)$",
        description="Allowed statuses: completed, partially_completed, not_completed",
    )
    reflection: Optional[str] = Field(None, max_length=1000)


class QuestCompletionResponse(BaseModel):
    quest_id: str
    completion_status: str
    reflection: Optional[str] = None
    completed_at: Optional[str] = None


class QuestDetailResponse(BaseModel):
    id: str
    quest_id: str
    user_preferences: dict
    selected_location: Optional[Any] = None
    quest: QuestResponse
    completion_status: str
    reflection: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
