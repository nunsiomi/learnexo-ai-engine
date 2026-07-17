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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "learnexo-content-engine"}

app.include_router(learning_style_router)
app.include_router(learning_path.router)
app.include_router(content.router)
app.include_router(pipeline.router)
app.include_router(videos.router)


