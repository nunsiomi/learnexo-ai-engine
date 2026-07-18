"""
YouTube Video Recommender for LearNexo — Visual Learners

Uses the YouTube Data API v3 to search for and rank educational videos
that match a Nigerian secondary school student's topic and class level.

Videos are filtered and scored to surface the most educational results:
  - Prefers channels known for Nigerian or African educational content
  - Falls back to globally trusted channels (Khan Academy, TED-Ed, etc.)
  - Filters out music, vlogs, and irrelevant content
  - Scores videos by relevance, view count, and educational signals

Requires: YOUTUBE_API_KEY environment variable
"""

import logging
import os
import re
import httpx
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# Nigerian / African educational channels to prioritise in search queries
NIGERIAN_EDU_CHANNELS = [
    "Faslearn", "Swiflearn", "EduNation", "ScholarX Africa",
    "Nigeria Education", "WAEC", "Naija Tutorials",
]

# Globally trusted educational channels (fallback boosters)
GLOBAL_EDU_CHANNELS = [
    "Khan Academy", "CrashCourse", "TED-Ed", "Professor Leonard",
    "3Blue1Brown", "Organic Chemistry Tutor", "Amoeba Sisters",
    "Tyler DeWitt", "Science ABC", "Numberphile",
]

# Keywords that signal non-educational content — used to filter results
IRRELEVANT_KEYWORDS = [
    "music", "song", "vlog", "prank", "reaction", "unboxing",
    "trailer", "movie", "comedy", "skit", "nollywood", "afrobeats",
    "remix", "funny", "gaming", "fortnite", "minecraft",
]


class YouTubeVideo(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    channel_name: str = Field(..., description="Name of the YouTube channel")
    description: str = Field(..., description="Short video description (first 250 chars)")
    url: str = Field(..., description="Full YouTube watch URL")
    thumbnail_url: str = Field(..., description="Thumbnail image URL")
    duration_iso: str = Field(
        "", description="Video duration in ISO 8601 format (e.g. PT12M30S)"
    )
    duration_readable: str = Field(
        "", description="Human-readable duration (e.g. 12 min 30 sec)"
    )
    view_count: int = Field(0, description="Number of views")
    relevance_score: float = Field(
        0.0, description="Internal relevance score (higher = better)"
    )
    why_recommended: str = Field(
        "", description="Brief explanation of why this video is recommended"
    )


class YouTubeRecommendation(BaseModel):
    topic: str
    subject: str
    class_level: str
    query_used: str = Field(..., description="The search query sent to YouTube")
    videos: List[YouTubeVideo]
    fallback_used: bool = Field(
        False,
        description="True if Nigerian-specific search returned no results and a broader search was used",
    )


def _parse_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration (PT12M30S) to '12 min 30 sec'."""
    if not iso_duration:
        return ""
    pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
    match = pattern.match(iso_duration)
    if not match:
        return iso_duration
    hours, minutes, seconds = match.groups()
    parts = []
    if hours:
        parts.append(f"{hours} hr")
    if minutes:
        parts.append(f"{minutes} min")
    if seconds:
        parts.append(f"{seconds} sec")
    return " ".join(parts) if parts else ""


def _is_relevant(title: str, description: str) -> bool:
    """Return False if the video title or description contains irrelevant keywords."""
    combined = (title + " " + description).lower()
    return not any(kw in combined for kw in IRRELEVANT_KEYWORDS)


def _score_video(title: str, channel: str, view_count: int, topic: str) -> float:
    """
    Score a video 0–10 for relevance.
    Factors: Nigerian/African channel boost, trusted global channel boost,
    view count (log-scaled), keyword match in title.
    """
    score = 0.0

    # Channel type boosts
    channel_lower = channel.lower()
    if any(nc.lower() in channel_lower for nc in NIGERIAN_EDU_CHANNELS):
        score += 3.0
    elif any(gc.lower() in channel_lower for gc in GLOBAL_EDU_CHANNELS):
        score += 2.0

    # Topic keyword in title
    topic_words = topic.lower().split()
    title_lower = title.lower()
    matches = sum(1 for w in topic_words if w in title_lower)
    score += min(matches * 0.5, 2.0)

    # Educational signals in title
    edu_signals = ["tutorial", "lesson", "explained", "learn", "study", "class",
                   "lecture", "waec", "neco", "jamb", "secondary school", "ss1",
                   "ss2", "ss3", "jss", "nigeria", "nigerian", "africa"]
    signal_hits = sum(1 for sig in edu_signals if sig in title_lower)
    score += min(signal_hits * 0.3, 1.5)

    # View count (log scale, capped at 2.0)
    if view_count > 0:
        import math
        score += min(math.log10(view_count) * 0.2, 2.0)

    return round(score, 2)


def _build_query(topic: str, subject: str, class_level: str, nigerian_first: bool = True) -> str:
    """Build a YouTube search query."""
    if nigerian_first:
        return f"{topic} {subject} {class_level} Nigeria WAEC tutorial"
    return f"{topic} {subject} secondary school tutorial explained"


def _build_why_recommended(video: dict, is_nigerian_channel: bool, topic: str) -> str:
    """Generate a short human-readable reason for recommendation."""
    channel = video.get("channel", "")
    title = video.get("title", "").lower()

    reasons = []
    if is_nigerian_channel:
        reasons.append("from a Nigerian educational channel")
    elif any(gc.lower() in channel.lower() for gc in GLOBAL_EDU_CHANNELS):
        reasons.append("from a globally trusted educational channel")

    if "waec" in title or "neco" in title or "jamb" in title:
        reasons.append("exam-focused content")
    if "tutorial" in title or "lesson" in title or "explained" in title:
        reasons.append("structured tutorial format")
    if not reasons:
        reasons.append("matches your topic and class level")

    return "Recommended because it is " + ", ".join(reasons) + "."


def _fetch_videos(query: str, max_results: int = 10) -> List[dict]:
    """Call YouTube search.list and then videos.list for details.

    Returns an empty list (rather than raising) when:
      - YOUTUBE_API_KEY is not set (Task 5 / AUDIT.md §2.3 — silent-skip
        is deliberate: videos are supplementary, a missing key should not
        block a student from getting learning content).
      - The YouTube API returns an HTTP error (quota, auth, network).
      - The API response has an unexpected shape (Task 4 / AUDIT.md §2.1).
    All failure reasons are logged at WARNING/ERROR level so they are still
    debuggable server-side without being exposed to the client (Task 3).
    """
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        # Task 5: silent-skip instead of raising EnvironmentError.
        # A missing API key is a configuration issue, not a request error.
        # Videos are supplementary — the student should still get their
        # learning content. The /videos endpoint now returns an empty list
        # rather than 503. If you need the endpoint to be strict, change
        # this return to: raise EnvironmentError("YOUTUBE_API_KEY not set")
        logger.warning(
            "YOUTUBE_API_KEY is not set. YouTube video recommendations "
            "are disabled. Set the key in your .env file to enable them."
        )
        return []

    # Step 1: Search
    try:
        search_resp = httpx.get(
            f"{YOUTUBE_API_BASE}/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "videoCategoryId": "27",  # Education category
                "relevanceLanguage": "en",
                "maxResults": max_results,
                "safeSearch": "strict",
                "key": api_key,
            },
            timeout=15,
        )
        search_resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Task 3/4: HTTP error from the YouTube API (quota, auth, etc.).
        # Log server-side but return empty list so the caller degrades gracefully.
        logger.error(
            "YouTube search request failed with HTTP %s for query %r: %s",
            exc.response.status_code, query, exc,
        )
        return []
    except httpx.RequestError as exc:
        # Network-level error (timeout, DNS, etc.).
        logger.error("YouTube search network error for query %r: %s", query, exc)
        return []

    search_data = search_resp.json()
    items = search_data.get("items", [])

    if not items:
        return []

    # Task 4: .get() guard already present on videoId extraction (line below).
    # Any item without a videoId is skipped rather than raising KeyError.
    video_ids = [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]

    # Step 2: Get full details (duration, view count)
    try:
        details_resp = httpx.get(
            f"{YOUTUBE_API_BASE}/videos",
            params={
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(video_ids),
                "key": api_key,
            },
            timeout=15,
        )
        details_resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "YouTube video-details request failed with HTTP %s: %s",
            exc.response.status_code, exc,
        )
        return []
    except httpx.RequestError as exc:
        logger.error("YouTube video-details network error: %s", exc)
        return []

    details_data = details_resp.json()

    results = []
    for item in details_data.get("items", []):
        # Task 4: wrap each item in try/except so a malformed single item
        # does not abort the entire result set.
        try:
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            title = snippet.get("title", "")
            description = snippet.get("description", "")[:300]
            channel = snippet.get("channelTitle", "")
            duration_iso = content.get("duration", "")
            # Task 4: stats.get("viewCount") may be missing or non-numeric
            # (e.g. views disabled). Guard with int(... or 0).
            try:
                view_count = int(stats.get("viewCount") or 0)
            except (ValueError, TypeError):
                view_count = 0
            thumbnails = snippet.get("thumbnails", {})
            thumbnail = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
                or ""
            )

            # Task 4: item["id"] was direct indexing — now .get() with fallback.
            results.append({
                "video_id": item.get("id", ""),
                "title": title,
                "channel": channel,
                "description": description,
                "duration_iso": duration_iso,
                "view_count": view_count,
                "thumbnail": thumbnail,
            })
        except Exception as exc:  # noqa: BLE001
            # A malformed item degrades to being skipped, not a crash.
            logger.warning("Skipping malformed YouTube video item: %s", exc)
            continue

    return results


def recommend_videos(
    topic: str,
    subject: str,
    class_level: str,
    max_results: int = 5,
) -> YouTubeRecommendation:
    """
    Search YouTube for educational videos matching a topic and return
    the top results scored and ranked for a Nigerian secondary school student.

    Args:
        topic: The lesson topic (e.g. "Photosynthesis", "Quadratic Equations")
        subject: Subject name (e.g. "Biology", "Mathematics")
        class_level: Nigerian class level (e.g. "SS1", "JSS3")
        max_results: Number of videos to return (default 5, max 10)

    Returns:
        YouTubeRecommendation with ranked, filtered, annotated video list.
    """
    max_results = min(max_results, 10)
    fallback_used = False

    # Try Nigerian-first query
    query = _build_query(topic, subject, class_level, nigerian_first=True)
    raw_videos = _fetch_videos(query, max_results=15)

    # If too few results, fall back to broader query
    if len(raw_videos) < 3:
        fallback_used = True
        query = _build_query(topic, subject, class_level, nigerian_first=False)
        raw_videos = _fetch_videos(query, max_results=15)

    # Filter irrelevant content
    filtered = [
        v for v in raw_videos
        if _is_relevant(v["title"], v["description"])
    ]

    # Score and sort
    scored = []
    for v in filtered:
        is_nigerian = any(nc.lower() in v["channel"].lower() for nc in NIGERIAN_EDU_CHANNELS)
        score = _score_video(v["title"], v["channel"], v["view_count"], topic)
        why = _build_why_recommended(v, is_nigerian, topic)
        scored.append((score, v, why))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_results]

    videos = []
    for score, v, why in top:
        videos.append(YouTubeVideo(
            video_id=v["video_id"],
            title=v["title"],
            channel_name=v["channel"],
            description=v["description"],
            url=f"https://www.youtube.com/watch?v={v['video_id']}",
            thumbnail_url=v["thumbnail"],
            duration_iso=v["duration_iso"],
            duration_readable=_parse_duration(v["duration_iso"]),
            view_count=v["view_count"],
            relevance_score=score,
            why_recommended=why,
        ))

    return YouTubeRecommendation(
        topic=topic,
        subject=subject,
        class_level=class_level,
        query_used=query,
        videos=videos,
        fallback_used=fallback_used,
    )
