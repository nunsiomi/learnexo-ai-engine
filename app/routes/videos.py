import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.videos import VideoRecommendRequest

logger = logging.getLogger(__name__)

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
        "Requires the YOUTUBE_API_KEY environment variable to be set. "
        "Returns an empty video list if the key is absent or the YouTube API is unavailable."
    ),
)
def videos_endpoint(request: VideoRecommendRequest):
    # Phase 4 Tasks 3+5: EnvironmentError is no longer raised by recommend_videos
    # (missing key now returns [] — see youtube_recommender._fetch_videos).
    # Generic exceptions are logged server-side; no stack traces are returned to
    # the client.
    try:
        from youtube_recommender import recommend_videos
        result = recommend_videos(
            topic=request.topic,
            subject=request.subject,
            class_level=request.class_level,
            max_results=request.max_results,
        )
        return result.model_dump()
    except Exception as exc:
        logger.error(
            "Unexpected error in /videos endpoint for topic=%r subject=%r: %s",
            request.topic, request.subject, exc, exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching video recommendations. Please try again.",
        )

