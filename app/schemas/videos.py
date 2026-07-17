from typing import Literal

from pydantic import BaseModel, Field

ClassLevel = Literal["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]


class VideoRecommendRequest(BaseModel):
    topic: str = Field(..., description="Topic to find YouTube videos for")
    subject: str = Field(..., description="Subject (e.g. Mathematics, English Language)")
    class_level: ClassLevel = Field(..., description="Student's class level (e.g. SS1, JSS2)")
    max_results: int = Field(5, ge=1, le=10, description="Number of videos to return (1–10)")
