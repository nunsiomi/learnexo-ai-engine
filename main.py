from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.learning_style import router as learning_style_router
from app.routes.learning_path import router as learning_path_router
from app.routes.content import router as content_router
from app.routes.pipeline import router as pipeline_router

from app.routes import learning_path, content, videos, pipeline

app = FastAPI(
    title="LearNexo Content Engine",
    description=(
        "AI-powered content generation service for LearNexo. "
        "Determines students' learning styles from activity data and generates personalised learning paths and lesson content."
        "Generates personalised learning paths and lesson content for Nigerian "
        "secondary school students (JSS1–SS3) based on their determined learning style."
    ),
    version="1.0.1",
    contact={"name": "LearNexo AI Team"},
)

# CORS — Phase 3 hardening
# allow_origins=["*"] + allow_credentials=True is a spec-invalid combination
# (browsers reject it) and too permissive for a student-data service.
# Replaced with an explicit allowlist.
#
# NOTE: allow_credentials is removed — no current endpoint uses cookies or
# auth headers that require it. Re-add only if a future endpoint genuinely
# needs cross-origin cookie/auth support (and update origins to match).
#
# ⚠️  UPDATE THIS before deploying:
#     Replace the placeholder below with the real production frontend URL.
#     Do NOT put allow_origins=["*"] back.
ALLOWED_ORIGINS = [
    "http://localhost:3000",   # React / Create-React-App dev server
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # "https://your-learnexo-frontend.vercel.app",  # ← UPDATE BEFORE DEPLOY
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "learnexo-content-engine"}

app.include_router(learning_style_router)
app.include_router(learning_path.router)
app.include_router(content.router)
app.include_router(pipeline.router)
app.include_router(videos.router)


