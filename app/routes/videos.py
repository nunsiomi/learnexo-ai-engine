import traceback
from fastapi import APIRouter, HTTPException

from app.schemas.videos import VideoRecommendRequest

router = APIRouter(
    prefix="/videos",
    tags=["YouTube Videos — Visual Learners"],
)


@router.post(
    "",
    summary="Recommend YouTube videos for a topic",
    description=(
        "Searches YouTube for educational videos matching the topic, subject, and class level. "
        "Results are filtered for educational relevance and ranked — Nigerian/African channels "
        "are prioritised, then globally trusted channels (Khan Academy, CrashCourse, TED-Ed, etc.). "
        "Each video includes title, channel, URL, thumbnail, duration, view count, and a short "
        "explanation of why it was recommended. "
        "Requires the YOUTUBE_API_KEY environment variable to be set."
    ),
)
def videos_endpoint(request: VideoRecommendRequest):
    try:
        from youtube_recommender import recommend_videos
        result = recommend_videos(
            topic=request.topic,
            subject=request.subject,
            class_level=request.class_level,
            max_results=request.max_results,
        )
        return result.model_dump()
    except EnvironmentError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": str(e)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "trace": traceback.format_exc()},
        )
