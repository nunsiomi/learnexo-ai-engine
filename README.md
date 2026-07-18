# LearNexo Content Engine

AI-powered microservice that generates personalised learning content for Nigerian secondary school students (JSS1–SS3). It takes a student's learning style and weak/strong topic profile, then produces curriculum-aligned learning paths and focused lesson content tailored to how that student learns best.

**Pilot scope: English Language and Mathematics only.**

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

---

## Environment Variables

| Variable | Required | Purpose | Where to get it |
|---|---|---|---|
| `GROQ_API_KEY` | **Yes** | Powers all LLM content generation | [console.groq.com](https://console.groq.com) — free tier available |
| `YOUTUBE_API_KEY` | No | Fetches real YouTube videos for visual learners | [console.cloud.google.com](https://console.cloud.google.com) → Enable "YouTube Data API v3" |
| `GROQ_MODEL` | No | Override the default LLM model | Default: `llama-3.3-70b-versatile` |

> If `YOUTUBE_API_KEY` is missing, the `/videos` endpoint returns `503` and `resources.videos` in content responses falls back to LLM-suggested links — all other generation still works normally.

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
| `student_id` | string | No | Any identifier |

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
  "student_id": "STU-1023",
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
| `student_id` | string | No | Any identifier |

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
          { "title": "Quadratic Equations Practice", "url": "https://..." }
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

> For **visual learners** with `YOUTUBE_API_KEY` set, `resources.videos` contains real YouTube results ranked by educational quality, Nigerian channels prioritised. Without the key, the LLM suggests plausible video links.

---

### `POST /api/generate-learning/` — Full Pipeline (Stages 1 + 2 + 3)

Run all three stages in a single call. Useful for onboarding.

**Request:**
```json
{
  "student_activity": { "activity": ["watched diagrams", "drew concept maps"] },
  "subject": "English Language",
  "class_level": "JSS2",
  "weak_topics": ["tenses", "essay_writing"],
  "strong_topics": ["summary"],
  "term": "First",
  "student_id": "STU-001",
  "content_depth": "core",
  "generate_content_for_first_topic": true
}
```

**Response:** `{ learning_style, learning_path, content }` — `learning_path` is the Stage 2 response, `content` is the Stage 3 response for the first recommended topic (or `null` if `generate_content_for_first_topic` is `false`).

---

### `POST /videos` — YouTube Recommendations (standalone)

Fetch ranked YouTube videos for any topic independently.

**Request:**
```json
{ "topic": "trigonometry", "subject": "Mathematics", "class_level": "SS1", "max_results": 5 }
```

**Response per video:** `title`, `channel_name`, `url`, `thumbnail_url`, `duration_readable`, `view_count`, `relevance_score`, `why_recommended`

Requires `YOUTUBE_API_KEY`. Returns `503` if not configured.

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
    materials = item["resources"]["materials"] # [{title, url}]
    action   = item["recommended_action"]

start_here = result["recommended_start"]  # slug of the highest-priority topic
```

### 4 — Full onboarding in one call

```python
async def onboard_student(student_activity: list[str], subject: str,
                           class_level: str, weak_topics: list[str]):
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            f"{CONTENT_ENGINE_URL}/api/generate-learning/",
            json={
                "student_activity": {"activity": student_activity},
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
        if response.status_code == 503:
            return []  # YOUTUBE_API_KEY not configured
        response.raise_for_status()
        return response.json()["videos"]
```

### Error Codes

| Status | Meaning |
|---|---|
| `200` | Success |
| `422` | Invalid request — check field names, topic slugs, and allowed values |
| `500` | AI generation failed — check `GROQ_API_KEY` and Groq service status |
| `503` | YouTube API unavailable — check `YOUTUBE_API_KEY` |

---

## File Structure

```
main.py                        # FastAPI app — registers all routes, CORS
youtube_recommender.py         # YouTube Data API v3 search, filter, ranking

app/
  core/
    config.py                  # Loads env vars (GROQ_API_KEY, GROQ_MODEL)
    dependencies.py            # FastAPI dependency injection
    topics.py                  # Topic slug allowlists for English & Mathematics
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
```

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
| Language | Python 3.11+ |

---

## Curriculum Alignment

All content is aligned to the **Nigerian secondary school curriculum**:
- **WAEC** — West African Examinations Council
- **NECO** — National Examinations Council (including BECE for JSS3)
- **JAMB** — Joint Admissions and Matriculation Board

Curriculum data for JSS1–JSS3 was extracted directly from official source PDFs (New Concept Mathematics series, NGM JSS3 Teacher's Guide, Lagos State unified schemes of work, NCE SS3 Teacher's Guide). SS1–SS3 content is based on NERDC/WAEC standard curriculum knowledge.
