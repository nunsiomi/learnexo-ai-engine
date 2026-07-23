import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import learning_style, learning_path, content, pipeline, videos

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
ALLOWED_ORIGINS = [
    "http://localhost:3000",   # React / Create-React-App dev server
    "http://localhost:5173",   # Vite dev server (default)
    "http://localhost:8080",   # Vite dev server (Lovable plugin variant)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]

# Production frontend origin(s) — comma-separated, set via env var rather than
# hardcoded so the same image/build works across environments (e.g. Render's
# render.yaml injects the frontend service's URL here at deploy time).
_extra_origins = os.getenv("ADDITIONAL_ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS += [origin.strip() for origin in _extra_origins.split(",") if origin.strip()]

# Also allow the frontend dev server when reached via a LAN IP (e.g. testing
# from a phone on the same network) — Vite prints one of these alongside
# localhost. DHCP means the exact IP changes, so match the private ranges
# (RFC1918) on the known dev ports instead of hardcoding one address.
LAN_ORIGIN_REGEX = (
    r"^http://(192\.168\.\d{1,3}\.\d{1,3}"
    r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})"
    r":(3000|5173|8080)$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=LAN_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "learnexo-content-engine"}

app.include_router(learning_style.router)
app.include_router(learning_path.router)
app.include_router(content.router)
app.include_router(pipeline.router)
app.include_router(videos.router)


