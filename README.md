# LearNEXO-AI — Content Engine

An **AI-powered personalized learning engine** for Nigerian secondary school students (JSS1–SS3). It takes a student's learning style and weak/strong topic profile, then produces curriculum-aligned learning paths and focused lesson content tailored to how that student learns best.

The engine is **three coordinated AI modules** — Learning Style, Learning Path, and Content — each built on the same foundation model (**LLaMA 3.3 70B via Groq**, orchestrated with LangChain and schema-constrained with Pydantic) but specialized through its own prompting and curriculum grounding. No model is trained; the engineering is the orchestration and grounding around the foundation model.

**Pilot scope: English Language and Mathematics only.**

---

## Project Status

The backend is stable through its structural cleanup pass, and the frontend
now has real accounts, a full onboarding wizard, and assesses both pilot
subjects per session.

| Area | Status |
|---|---|
| Pipeline crash on `/api/generate-learning/` | ✅ Fixed & verified |
| Curriculum grounding (Math + English) | ✅ Reconciled — every active slug maps to a real curriculum entry via its `"slug"` field |
| Security & input validation | ✅ Hardened — CORS locked to an explicit allowlist, `subject`/`class_level`/`term`/`content_depth` constrained to enums, learning-style score keys required, first-layer prompt-injection guard |
| Error handling | ✅ Cleaned up — honest 4xx vs 5xx mapping, no leaked tracebacks, YouTube failures degrade to an empty video list |
| Structural cleanup | ✅ Done. DI factories centralized, dependencies pinned, dead code and stray artifacts removed |
| Frontend, onboarding wizard | ✅ Built and working |
| Frontend, accounts (Supabase Auth) | ✅ Built and working: sign-up/sign-in, per-student profile |
| Frontend, VAK quiz | ✅ 18 questions, no style labels shown, shuffled option order |
| Frontend, two-subject assessment | ✅ Assesses Math then English per session, generates both learning paths together |
| Frontend, gamified roadmap | 🔲 Not built yet. MCQ content is ready, roadmap UI isn't |
| Deployment | 🔲 Not built yet, the only phase left |

**Known documented gaps** (not blocking): Literature has no allowlist coverage in the English pilot; `vectors` (Math) and `word_formation` (English) are genuine curriculum content gaps, not matching failures; YouTube relevance ranking is sometimes weak and is flagged for a future pass.

---

## System Architecture — The 3 Stages

```
┌──────────────────────────────┐     ┌──────────────────────────────┐     ┌──────────────────────────────┐
│  STAGE 1                     │     │  STAGE 2                     │     │  STAGE 3                     │
│  POST /api/learning-style/   │────▶│  POST /learning-path         │────▶│  POST /content               │
│        detailed              │     │                              │     │                              │
│  Scores in                   │     │  weak_topics[] +             │     │  topics[] with mastery       │
│  (visual/auditory/           │     │  strong_topics[] in          │     │  scores in                   │
│   kinesthetic + cognitive)   │     │                              │     │                              │
│                              │     │  recommended_order[] out     │     │  generated_content[] out     │
│  Friendly label + tips out   │     │  (ordered topic slugs)       │     │  (resources + explanation    │
│                              │     │                              │     │   per topic, prioritised)    │
└──────────────────────────────┘     └──────────────────────────────┘     └──────────────────────────────┘
                                                   │
                                     ┌─────────────▼─────────────┐
                                     │  POST /api/generate-       │
                                     │        learning/           │
                                     │  Stages 1 + 2 + 3 in one  │
                                     └───────────────────────────┘
```

---

## Running Locally

The backend and frontend are separate processes and both need to be running
for the wizard to work end to end.

### Backend

**Prerequisites:** Python 3.11+

```bash
# 1. Clone and enter the folder
cd LearNEXO-AI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env — add your GROQ_API_KEY (required) and YOUTUBE_API_KEY (optional)

# 4. Start the server
uvicorn main:app --reload --port 8000
```

- API base: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `GET http://localhost:8000/health`

### Frontend

**Prerequisites:** Node 22, a Supabase project (free tier is fine)

```bash
cd web

# 1. Install dependencies
npm install

# 2. Set up environment variables
cp .env.example .env
# Edit .env: add VITE_API_URL (the backend above), VITE_SUPABASE_URL, and
# VITE_SUPABASE_ANON_KEY (from your Supabase project's API settings)

# 3. Start the dev server
npm run dev
```

The dev server prints its own port (5173 by default). Sign up for an account
in the browser, then run through the wizard: profile, learning-style quiz,
Mathematics assessment, English assessment, generated paths for both subjects.

---

## Environment Variables

### Backend (`.env`)

| Variable | Required | Purpose | Where to get it |
|---|---|---|---|
| `GROQ_API_KEY` | **Yes** | Powers all LLM content generation | [console.groq.com](https://console.groq.com) — free tier available |
| `YOUTUBE_API_KEY` | No | Fetches real YouTube videos for visual learners | [console.cloud.google.com](https://console.cloud.google.com) → Enable "YouTube Data API v3" |
| `GROQ_MODEL` | No | Override the default LLM model | Default: `llama-3.3-70b-versatile` |

> If `YOUTUBE_API_KEY` is missing, videos are silently skipped. `/videos` returns an empty list and `resources.videos` in content responses falls back to LLM-suggested links. Nothing fails or returns an error; videos are supplementary, not core content.

### Frontend (`web/.env`)

| Variable | Required | Purpose |
|---|---|---|
| `VITE_API_URL` | **Yes** | The backend URL above (`http://localhost:8000` for local dev) |
| `VITE_SUPABASE_URL` | **Yes** | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | **Yes** | Your Supabase project's anon/public API key |

---

## API Endpoints

### `POST /api/learning-style/detailed` — Stage 1

Interpret a student's activity scores and return a human-readable learning style profile.

**Request:**
```json
{
  "learning_style_scores": { "visual": 75, "auditory": 50, "kinesthetic": 60 },
  "cognitive_score": 70,
  "student_profile": { "class_level": "JSS2", "subject": "Mathematics" }
}
```

**Response includes:** `learning_style`, `friendly_label`, `what_it_means`, `how_platform_adapts`, `study_tips`, `confidence`, `recommended_formats`, `risk_of_misclassification`

---

### `POST /learning-path` — Stage 2

Generate a prioritised topic order based on the student's weak and strong areas.

**Request:**
```json
{
  "learning_style": "visual",
  "subject": "Mathematics",
  "class_level": "SS1",
  "weak_topics": ["quadratic_equations", "trigonometry"],
  "strong_topics": ["fractions"],
  "term": "First"
}
```

**Fields:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `learning_style` | string | Yes | `visual`, `auditory`, `kinesthetic` |
| `subject` | string | Yes | `Mathematics` or `English Language` |
| `class_level` | string | Yes | `JSS1`, `JSS2`, `JSS3`, `SS1`, `SS2`, `SS3` |
| `weak_topics` | string[] | No | Must use valid topic slugs — see [Topic Slugs](#topic-slugs) |
| `strong_topics` | string[] | No | Must use valid topic slugs |
| `term` | string | No | `First`, `Second`, `Third` (default: `First`) |

**Response:**
```json
{
  "recommended_order": ["quadratic_equations", "trigonometry", "indices", "algebraic_expressions"],
  "strategy": "Start with quadratic equations using visual diagrams, then build up to trigonometry.",
  "focus_areas": ["quadratic_equations", "trigonometry"]
}
```

> **Note:** All strings in `recommended_order` and `focus_areas` are topic slugs from the allowlist. Invalid slugs in the request return `422` with the full valid list.

---

### `POST /content` — Stage 3

Generate focused study content for one or more topics. Topics are sorted by mastery — lowest mastery gets priority 1.

**Request:**
```json
{
  "mode": "multi_topic",
  "topics": [
    { "topic": "quadratic_equations", "mastery": 0.2, "learning_stage": "foundation" },
    { "topic": "trigonometry", "mastery": 0.4, "learning_stage": "foundation" }
  ],
  "subject": "Mathematics",
  "class_level": "SS1",
  "learning_style": "visual",
  "focus_reason": "general_assessment",
  "content_depth": "core"
}
```

**Fields:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `mode` | string | No | Always `multi_topic` (default) |
| `topics` | array | Yes | Each item: `topic` (slug), `mastery` (0.0–1.0), `learning_stage` |
| `subject` | string | Yes | `Mathematics` or `English Language` |
| `class_level` | string | Yes | `JSS1`–`SS3` |
| `learning_style` | string | Yes | `visual`, `auditory`, `kinesthetic` |
| `content_depth` | string | No | `introduction`, `core`, `advanced`, `revision` (default: `core`) |
| `focus_reason` | string | No | e.g. `general_assessment`, `exam_prep` |

**Response:**
```json
{
  "generated_content": [
    {
      "topic": "quadratic_equations",
      "priority": 1,
      "resources": {
        "videos": [
          { "title": "Solving Quadratic Equations for WAEC", "url": "https://youtube.com/..." }
        ],
        "materials": [
          { "title": "Quadratic Equations Practice", "description": "A set of past WAEC-style questions with worked solutions." }
        ]
      },
      "explanation": {
        "summary": "A quadratic equation is any equation of the form ax² + bx + c = 0.",
        "key_points": [
          "Solve by factorisation, completing the square, or the formula",
          "The discriminant b² - 4ac tells you how many real roots exist"
        ]
      },
      "recommended_action": "Watch the video first, then practise three past WAEC questions."
    }
  ],
  "recommended_start": "quadratic_equations"
}
```

> **Materials never carry a `url` field**, only `title` and `description`. This is deliberate: the LLM was inventing plausible-looking but fake resource links, so the field was removed from the schema entirely rather than adding a second search API just to validate them. Video URLs are real (from the YouTube Data API) and unaffected by this.

> For **visual learners** with `YOUTUBE_API_KEY` set, `resources.videos` contains real YouTube results ranked by educational quality, Nigerian channels prioritised. Without the key, the LLM suggests plausible video links.

---

### `POST /api/generate-learning/` — Full Pipeline (Stages 1 + 2 + 3)

Run all three stages in a single call. Useful for onboarding.

**Request:**
```json
{
  "student_activity": {
    "learning_style_scores": { "visual": 75, "auditory": 50, "kinesthetic": 60 },
    "cognitive_score": 70,
    "student_profile": { "class_level": "JSS2" }
  },
  "subject": "English Language",
  "class_level": "JSS2",
  "weak_topics": ["tenses", "essay_writing"],
  "strong_topics": ["summary"],
  "term": "First",
  "content_depth": "core",
  "generate_content_for_first_topic": true
}
```

> `student_activity` takes the exact same shape as the request body for `POST /api/learning-style/detailed` above: `learning_style_scores`, `cognitive_score`, and `student_profile`, all required. It is **not** a list of activity strings; that shape was an early design that caused every call to this endpoint to fail and was fixed in Phase 1.

**Response:** `{ learning_style, learning_path, content }` — `learning_path` is the Stage 2 response, `content` is the Stage 3 response for the first recommended topic (or `null` if `generate_content_for_first_topic` is `false`).

---

### `POST /videos` — YouTube Recommendations (standalone)

Fetch ranked YouTube videos for any topic independently.

**Request:**
```json
{ "topic": "trigonometry", "subject": "Mathematics", "class_level": "SS1", "max_results": 5 }
```

**Response per video:** `title`, `channel_name`, `url`, `thumbnail_url`, `duration_readable`, `view_count`, `relevance_score`, `why_recommended`

Requires `YOUTUBE_API_KEY`. Without it, returns an empty `videos` list (`200`, not an error). Videos are supplementary, so a missing key degrades gracefully instead of failing the request.

---

### `GET /health`
```json
{ "status": "ok", "service": "learnexo-content-engine" }
```

---

## Topic Slugs

All `weak_topics`, `strong_topics`, and `topics[].topic` values **must** use these exact slugs. Unrecognised slugs return a `422` error with the full valid list.

Every active slug maps to a real curriculum entry in `app/data/curriculum/*.json` (via that entry's `"slug"` field), so generated content is grounded in the official scheme of work rather than the model's general knowledge.

### English Language (21 active topics)

| Slug | Slug | Slug |
|---|---|---|
| `prepositions` | `tenses` | `sentence_structure` |
| `synonyms` | `antonyms` | `idioms` |
| `vocabulary_in_context` | `comprehension` | `reading_skills` |
| `summary` | `essay_writing` | `letter_writing` |
| `narrative_writing` | `descriptive_writing` | `articles` |
| `vowel_sounds` | `consonant_sounds` | `stress_jss2` |
| `stress_ss1` | `intonation_jss2` | `intonation_ss1` |

> **Class-split slugs:** `stress` and `intonation` are taught as distinct oral-English entries at two levels, so each is split — use `stress_jss2`/`intonation_jss2` for JSS2 and `stress_ss1`/`intonation_ss1` for SS1.
>
> **Reserved (not accepted):** `concord`, `inference`, `spelling`, and `word_formation` have no standalone curriculum entry to ground against and are **not** in the active allowlist — requests using them return `422`. See `ENGLISH_TOPICS_RESERVED` in `app/core/topics.py` for the per-slug reasoning.
>
> **Known scope gap:** the allowlist has no slugs for Literature content (poetry, drama, prose, folktales), even though the curriculum carries Literature topics at every class level. This is a documented, deliberate gap for the current pilot.

### Mathematics (29 active topics)

| Slug | Slug | Slug |
|---|---|---|
| `numbers_and_numeration` | `basic_operations` | `fractions` |
| `decimals` | `percentages` | `ratio_and_proportion` |
| `indices` | `logarithms` | `surds` |
| `algebraic_expressions` | `linear_equations` | `simultaneous_equations` |
| `quadratic_equations` | `inequalities` | `sets` |
| `plane_geometry` | `angles` | `circles` |
| `mensuration` | `coordinate_geometry_ss1` | `coordinate_geometry_ss2` |
| `statistics` | `probability_jss2` | `probability_ss3` |
| `sequence_arithmetic` | `sequence_geometric` | `commercial_arithmetic` |
| `matrices` | `trigonometry` | |

> **Class-split slugs:** `coordinate_geometry`, `probability`, and `sequence_and_series` are each carried at two levels, so each is split — `coordinate_geometry_ss1`/`_ss2`, `probability_jss2`/`_ss3`, and `sequence_arithmetic`/`sequence_geometric`.
>
> **Reserved (not accepted):** `logic`, `polynomials`, `triangles`, and `vectors` have no standalone curriculum entry and are **not** in the active allowlist — requests using them return `422`. See `MATHS_TOPICS_RESERVED` in `app/core/topics.py`.

---

## Backend Integration Guide

This service runs as a standalone microservice. Your backend calls it over HTTP.

### Setup

Start the engine (replace host/port for your deployment):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Set `CONTENT_ENGINE_URL` in your backend environment:
```
CONTENT_ENGINE_URL=http://content-engine:8000
```

### 1 — Generate a learning path

After a student's learning style is determined, call `/learning-path` with their weak/strong topics:

```python
import httpx

CONTENT_ENGINE_URL = "http://content-engine:8000"

async def get_learning_path(learning_style: str, subject: str, class_level: str,
                             weak_topics: list[str], strong_topics: list[str]):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{CONTENT_ENGINE_URL}/learning-path",
            json={
                "learning_style": learning_style,
                "subject": subject,
                "class_level": class_level,
                "weak_topics": weak_topics,    # e.g. ["tenses", "essay_writing"]
                "strong_topics": strong_topics, # e.g. ["summary"]
                "term": "First",
            }
        )
        response.raise_for_status()
        return response.json()
        # Returns: { recommended_order, strategy, focus_areas }
```

### 2 — Fetch content for topics

Pass topics from `recommended_order` with mastery scores:

```python
async def get_content(topics: list[dict], subject: str, class_level: str,
                       learning_style: str):
    # topics format: [{"topic": "tenses", "mastery": 0.3, "learning_stage": "foundation"}]
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{CONTENT_ENGINE_URL}/content",
            json={
                "mode": "multi_topic",
                "topics": topics,
                "subject": subject,
                "class_level": class_level,
                "learning_style": learning_style,
                "content_depth": "core",
                "focus_reason": "general_assessment",
            }
        )
        response.raise_for_status()
        return response.json()
        # Returns: { generated_content, recommended_start }
```

### 3 — Consume the content response

```python
result = await get_content(...)

for item in result["generated_content"]:
    topic    = item["topic"]           # slug string
    priority = item["priority"]        # 1 = most urgent
    summary  = item["explanation"]["summary"]
    points   = item["explanation"]["key_points"]
    videos   = item["resources"]["videos"]    # [{title, url}]
    materials = item["resources"]["materials"] # [{title, description}], no url, see note above
    action   = item["recommended_action"]

start_here = result["recommended_start"]  # slug of the highest-priority topic
```

### 4 — Full onboarding in one call

```python
async def onboard_student(learning_style_scores: dict, cognitive_score: int,
                           subject: str, class_level: str, weak_topics: list[str]):
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            f"{CONTENT_ENGINE_URL}/api/generate-learning/",
            json={
                "student_activity": {
                    "learning_style_scores": learning_style_scores,  # {"visual": .., "auditory": .., "kinesthetic": ..}
                    "cognitive_score": cognitive_score,
                    "student_profile": {"class_level": class_level},
                },
                "subject": subject,
                "class_level": class_level,
                "weak_topics": weak_topics,
                "strong_topics": [],
                "term": "First",
                "generate_content_for_first_topic": True,
            }
        )
        response.raise_for_status()
        data = response.json()
        # data["learning_style"]  → "visual" / "auditory" / "kinesthetic"
        # data["learning_path"]   → { recommended_order, strategy, focus_areas }
        # data["content"]         → { generated_content, recommended_start }
        return data
```

### 5 — Standalone video fetch

```python
async def get_videos(topic: str, subject: str, class_level: str):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{CONTENT_ENGINE_URL}/videos",
            json={"topic": topic, "subject": subject,
                  "class_level": class_level, "max_results": 5}
        )
        response.raise_for_status()
        return response.json()["videos"]  # [] if YOUTUBE_API_KEY isn't configured, not an error
```

### Error Codes

| Status | Meaning |
|---|---|
| `200` | Success |
| `422` | Invalid request — check field names, topic slugs, and allowed values |
| `500` | AI generation failed — check `GROQ_API_KEY` and Groq service status |
| `502` | The learning-style model returned output that failed schema validation. A Groq-side issue, retry |

---

## File Structure

```
main.py                        # FastAPI app — registers all routes, CORS
youtube_recommender.py         # YouTube Data API v3 search, filter, ranking

app/
  core/
    config.py                  # Loads env vars (GROQ_API_KEY, GROQ_MODEL)
    dependencies.py            # FastAPI dependency injection, all three service factories
    topics.py                  # Topic slug allowlists for English & Mathematics
    validators.py              # Shared topic-slug validation, used by all three request schemas
    security.py                # First-layer prompt-injection guard for free-text fields
  data/
    curriculum/
      mathematics.json         # Official Nigerian curriculum (JSS1–SS3, all terms)
      english_language.json    # Same structure for English Language
      raw/                     # Source PDFs (New Concept Mathematics, Lagos State
                               # schemes of work, NGM JSS3 TG, NCE SS3 TG, BECE syllabuses)
  routes/                      # HTTP handlers only — no business logic
    learning_style.py          # POST /api/learning-style/detailed
    learning_path.py           # POST /learning-path
    content.py                 # POST /content
    pipeline.py                # POST /api/generate-learning/
    videos.py                  # POST /videos
  schemas/
    learning_style.py          # Stage 1 request/response models
    pipeline.py                # Full pipeline request/response models
    videos.py                  # Video recommendation models
  services/                    # LLM chains and business logic
    learning_style_service.py  # Stage 1 — learning style interpretation
    learning_path_service.py   # Stage 2 — curriculum-aware topic ordering
    content_service.py         # Stage 3 — per-topic content generation

web/                           # React frontend, see "Frontend" below
```

---

## Frontend

A guided onboarding wizard lives in `web/` (React + TanStack Start + Vite,
Tailwind for styling). It runs entirely against the backend above and
Supabase for auth and profile data. The backend itself has no auth code and
doesn't need any.

**Flow:** sign up or sign in → profile (name, class level, term) → 18-question
learning-style quiz → Mathematics assessment → English assessment →
personalized learning paths for both subjects, shown with a subject tab
switcher.

| File | Purpose |
|---|---|
| `web/src/routes/index.tsx` | The wizard itself: profile, quiz, assessment, and results steps |
| `web/src/routes/login.tsx` / `signup.tsx` | Auth pages |
| `web/src/lib/auth-context.tsx` | Supabase session/profile context |
| `web/src/lib/supabase.ts` | Supabase client |
| `web/src/lib/quiz-data.ts` | VAK question bank, class-scoped MCQ banks, scoring helpers |
| `web/src/lib/api.ts` | All backend HTTP calls |

The learning-style quiz and the academic assessment are deliberately separate
question sets. The quiz measures how a student prefers to learn and has
nothing to do with the curriculum. The assessment measures what a student
already knows, and every question is tagged with the exact topic slug it
tests, so a wrong answer traces back to one specific curriculum topic, not a
vague overall score. See `LearNEXO-AI_Executive_Overview.md` for the full
explanation of how that tagging works end to end.

---

## Tech Stack

| Component | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| AI Model | Groq — `llama-3.3-70b-versatile` |
| AI Orchestration | LangChain + LangChain-Groq |
| Data Validation | Pydantic v2 |
| YouTube Integration | YouTube Data API v3 (`google-api-python-client`) |
| Environment Config | python-dotenv |
| Backend Language | Python 3.11+ |
| Frontend Framework | React + TanStack Start (Vite) |
| Frontend Styling | Tailwind CSS |
| Auth & Profile Storage | Supabase (Postgres + Auth, Row Level Security) |

---

## Curriculum Alignment

All content is aligned to the **Nigerian secondary school curriculum**:
- **WAEC** — West African Examinations Council
- **NECO** — National Examinations Council (including BECE for JSS3)
- **JAMB** — Joint Admissions and Matriculation Board

Curriculum data for JSS1–JSS3 was extracted directly from official source PDFs (New Concept Mathematics series, NGM JSS3 Teacher's Guide, Lagos State unified schemes of work, NCE SS3 Teacher's Guide). SS1–SS3 content is based on NERDC/WAEC standard curriculum knowledge.
