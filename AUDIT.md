# LearNEXO-AI — Codebase Audit

Audit only — no code was changed. Line numbers reference the state of the repo at audit time.
Severity legend: **Breaking** (endpoint cannot succeed / crashes) · **High** · **Medium** · **Low**.

---

## Pass 1: Structural Audit

### 1. Actual request flow (route → service → external calls)

| Route (method + path) | Handler file | Service class | External calls |
|---|---|---|---|
| `POST /api/learning-style/detailed` | [learning_style.py:11](app/routes/learning_style.py#L11) | `LearningStyleService.evaluate` ([learning_style_service.py:79](app/services/learning_style_service.py#L79)) | Groq LLM (`PydanticOutputParser`) |
| `POST /learning-path` and `/learning-path/` | [learning_path.py:65-77](app/routes/learning_path.py#L65-L77) | `LearningPathService.generate` ([learning_path_service.py:119](app/services/learning_path_service.py#L119)) | File read of curriculum JSON ([learning_path_service.py:28](app/services/learning_path_service.py#L28)); Groq LLM |
| `POST /content` and `/content/` | [content.py:76](app/routes/content.py#L76) | `ContentService.generate` ([content_service.py:182](app/services/content_service.py#L182)) | Groq LLM (once per topic); YouTube API for visual learners ([content_service.py:116](app/services/content_service.py#L116)) |
| `POST /api/generate-learning/` | [pipeline.py:31](app/routes/pipeline.py#L31) | All three services | Groq LLM ×N; YouTube API |
| `POST /videos` | [videos.py:24](app/routes/videos.py#L24) | *(module fn)* `recommend_videos` ([youtube_recommender.py:248](youtube_recommender.py#L248)) | YouTube Data API v3 ×2 (`search.list`, `videos.list`) |
| `GET /health` | [main.py:31](main.py#L31) | — | none |

External-call surface: **Groq** via `langchain-groq` in all three services; **YouTube Data API v3** via `httpx` in `youtube_recommender._fetch_videos`; **local filesystem** read of `mathematics.json` / `english_language.json`.

### 2. Deviations from the routes → services → config/data three-layer architecture

- **High — Business logic in the route/schema layer.** Topic-slug validation (a domain rule) lives in Pydantic `model_validator`s inside the route/schema layer, not the service layer: [content.py:37-47](app/routes/content.py#L37-L47), [learning_path.py:36-52](app/routes/learning_path.py#L36-L52), [pipeline.py schema:18-34](app/schemas/pipeline.py#L18-L34). The services themselves do **not** re-validate slugs, so any caller reaching a service directly (e.g. the pipeline calling `stage3.generate`) bypasses the rule entirely.
- **Medium — DI helpers scattered instead of centralized.** `app/core/dependencies.py` only defines `get_learning_style_service`. `get_content_service` is redefined in [content.py:55](app/routes/content.py#L55) **and** [pipeline.py:17](app/routes/pipeline.py#L17); `get_learning_path_service` in [learning_path.py:61](app/routes/learning_path.py#L61) **and** [pipeline.py:13](app/routes/pipeline.py#L13). Three different patterns for the same concern.
- **Medium — Route reaches around the service.** `videos.py` imports `recommend_videos` directly from the top-level `youtube_recommender` module ([videos.py:26](app/routes/videos.py#L26)); there is no `services/` wrapper, unlike every other endpoint. `youtube_recommender.py` also sits at repo root rather than under `app/`.
- **Low — Schema layering inconsistent.** `content.py` defines its request/response models *inside the route file* ([content.py:17-52](app/routes/content.py#L17-L52)) while `learning_style`/`videos`/`pipeline` use `app/schemas/`. `TopicInput`, `ResourceItem`, etc. are defined in the *service* file ([content_service.py:18-51](app/services/content_service.py#L18-L51)).

### 3. Dead code

- **Medium — Unused imports in `main.py`.** Lines [main.py:3-6](main.py#L3-L6) import `learning_style_router`, `learning_path_router`, `content_router`, `pipeline_router`; then [main.py:8](main.py#L8) re-imports the modules. Registration uses a mix: `learning_style_router` (alias) but `learning_path.router` / `content.router` / `pipeline.router` (module attr). `learning_path_router`, `content_router`, `pipeline_router` are imported but **never used**.
- **Low — `LearningStyleResponse`** ([learning_style.py:48-49](app/schemas/learning_style.py#L48-L49)) is defined but never imported or returned anywhere.
- **Low — `StudentActivity`** ([learning_style.py:8-9](app/schemas/learning_style.py#L8-L9)) is used only as the pipeline input type, but its single field (`activity`) is never actually consumed (see Pass 2 — Breaking). Effectively dead in practice.
- **Low — `student_id`** is accepted by every endpoint/service and threaded through call signatures but never used (not logged, stored, or returned). e.g. [content_service.py:190](app/services/content_service.py#L190), [learning_path_service.py:126](app/services/learning_path_service.py#L126).
- **Low — Stray non-source files tracked/present:** `sample.txt` (tracked in git), `server.log`, `server_run.log` (gitignored but present). The `evaluation/` directory is offline research tooling, not part of the served app.

### 4. Duplicated logic that should be shared

- **High — Topic-slug validation block is copy-pasted three times** with identical structure: [content.py:37-47](app/routes/content.py#L37-L47), [learning_path.py:36-52](app/routes/learning_path.py#L36-L52), [pipeline.py:18-34](app/schemas/pipeline.py#L18-L34). Should be one reusable validator.
- **Medium — DI factory functions duplicated** (`get_content_service`, `get_learning_path_service`) — see Pass 1.2.
- **Medium — `LearningStyle` / `ClassLevel` / `TermName` `Literal` aliases redeclared** in at least five files ([content.py:13-14](app/routes/content.py#L13-L14), [learning_path.py:10-12](app/routes/learning_path.py#L10-L12), [content_service.py:13-15](app/services/content_service.py#L13-L15), [learning_path_service.py:15-17](app/services/learning_path_service.py#L15-L17), [videos.py schema:5](app/schemas/videos.py#L5)) instead of one shared enum module.
- **Low — `load_dotenv()` called twice**: [config.py:4](app/core/config.py#L4) and [youtube_recommender.py:23](youtube_recommender.py#L23).
- **Low — `.setdefault` fallback-shaping** logic repeated in `content_service._generate_single` ([content_service.py:176-178](app/services/content_service.py#L176-L178)) and `learning_path_service.generate` ([learning_path_service.py:171-173](app/services/learning_path_service.py#L171-L173)).

---

## Pass 2: Bug Audit

### 1. External calls without error handling

| Call | Location | Handling |
|---|---|---|
| Groq LLM `chain.invoke` (Stage 1) | [learning_style_service.py:80](app/services/learning_style_service.py#L80) | **None.** The route [learning_style.py:11-16](app/routes/learning_style.py#L11-L16) has **no try/except** → any LLM/parse error propagates as an unformatted **500**. |
| Groq LLM `chain.invoke` (path) | [learning_path_service.py:156](app/services/learning_path_service.py#L156) | Service unguarded; route wraps in try/except → 500 "Failed to generate learning path". |
| Groq LLM `chain.invoke` (content, per-topic) | [content_service.py:151](app/services/content_service.py#L151) | Service unguarded; route wraps → but re-mapped incorrectly (see 2 below). |
| YouTube `httpx.get` search | [youtube_recommender.py:180](youtube_recommender.py#L180) | `raise_for_status()` at :194 — network/HTTP errors raised. Caught only when called from `content_service._fetch_youtube_videos` ([content_service.py:138](app/services/content_service.py#L138), broad `except Exception → None`). When called from `/videos` route it surfaces (leaked trace, see Pass 4). |
| YouTube `httpx.get` details | [youtube_recommender.py:204](youtube_recommender.py#L204) | Same as above. |
| `video_ids = [...]` / `item["id"]["videoId"]` | [youtube_recommender.py:201](youtube_recommender.py#L201), [:236](youtube_recommender.py#L236) | Unguarded dict/key indexing on external JSON; malformed response → `KeyError`. |
| Curriculum file read | [learning_path_service.py:35-39](app/services/learning_path_service.py#L35-L39) | Guarded — broad `except Exception → []` (safe, but silently swallows a corrupt/missing file). |

### 2. Places a response schema can fail to validate

- **High — Stage 1 uses strict `PydanticOutputParser`** ([learning_style_service.py:60](app/services/learning_style_service.py#L60)). If the LLM returns `confidence` outside 0–1, a `learning_style` not in `{visual,auditory,kinesthetic}`, `risk_of_misclassification` not in `{low,medium,high}`, or omits any required field, the parser raises `OutputParserException`. **The route has no handler → 500.** This is the strictest validation path in the app and the most fragile.
- **Medium — `content_endpoint` mis-maps internal errors.** `ContentService._generate_single` raises `ValueError("Invalid content response…")` ([content_service.py:165](app/services/content_service.py#L165)) when the LLM returns a non-dict. The route treats *all* `ValueError` as **400 Bad Request** ([content.py:96-97](app/routes/content.py#L96-L97)), so an LLM-side failure is reported to the client as *their* bad input.
- **Low — Lenient parsers hide bad data.** `learning_path` and `content` use `JsonOutputParser` (parses JSON, does **not** enforce the pydantic schema). `ContentResponse.generated_content` is typed `list[dict[str, Any]]` ([content.py:51](app/routes/content.py#L51)) and `GenerateLearningResponse.learning_path` is `dict[str, Any]` ([pipeline.py schema:39](app/schemas/pipeline.py#L39)) — malformed LLM output passes through unvalidated to the client instead of failing loudly.

### 3. Config / env vars read without fallback or clear error

- **Good — `GROQ_API_KEY`**: [config.py:6-8](app/core/config.py#L6-L8) raises a clear `RuntimeError` at import if missing (fails fast at startup).
- **Medium — `YOUTUBE_API_KEY`** read three ways with inconsistent behavior: `os.getenv` → silent `None`/skip in [content_service.py:122](app/services/content_service.py#L122); `os.environ.get` → raises `EnvironmentError` in [youtube_recommender.py:173-177](youtube_recommender.py#L173-L177). Same missing key = silently-degrade in one path, 503 in another.
- **Low — `GROQ_MODEL`** has a hardcoded default `llama-3.3-70b-versatile` ([config.py:10](app/core/config.py#L10)). If that model is decommissioned by Groq, every LLM call fails at runtime (see Pass 2.4).
- **Low — `PORT`** documented in `.env.example` but never read anywhere in code.

### 4. Where a 500 can realistically originate — ranked

> ### 🔴 TOP SUSPECT for your current 500 — `POST /api/generate-learning/` is guaranteed to crash
> [pipeline.py:39](app/routes/pipeline.py#L39) calls `stage1.evaluate(payload.student_activity)`, passing a `StudentActivity` object (fields: `activity` only). But `LearningStyleService.evaluate` reads `data.student_profile`, `data.learning_style_scores`, and `data.cognitive_score` ([learning_style_service.py:81-85](app/services/learning_style_service.py#L81-L85)) — **none of which exist on `StudentActivity`** ([learning_style.py:8-9](app/schemas/learning_style.py#L8-L9)). Confirmed at audit time: all three attributes are absent → `AttributeError` → caught at [pipeline.py:76](app/routes/pipeline.py#L76) → **HTTP 500 "Failed to run full learning pipeline"** on *every* request. The `sample.txt` payload uses exactly this `student_activity` shape, so a user following the sample hits this immediately. **This endpoint cannot succeed in its current form.**

Remaining 500 sources, by likelihood:

2. **Stage 1 strict-parser / unguarded route** — `POST /api/learning-style/detailed` has no try/except; any Groq error or schema-validation miss → raw 500 ([learning_style.py:11](app/routes/learning_style.py#L11), [learning_style_service.py:80](app/services/learning_style_service.py#L80)).
3. **Deprecated/unavailable Groq model or unpinned dependency** — `requirements.txt` pins **no versions** (`langchain`, `langchain-core`, `langchain-groq` all floating). A Groq model retirement or a breaking `langchain` release makes *all* LLM endpoints 500. Recent commits ("Updated AI models", "Made updates to AI models") suggest model churn — verify `GROQ_MODEL` is a currently-served Groq model.
4. **YouTube `KeyError`/HTTP errors** on `/videos` — malformed API response or quota/403 → 500 with leaked traceback ([videos.py:39-43](app/routes/videos.py#L39-L43), [youtube_recommender.py:201/236](youtube_recommender.py#L201)).
5. **LLM non-dict output** in learning-path/content — surfaces as 500 (path) or mis-labeled 400 (content).

---

## Pass 3: Data Audit

> **RESOLVED (post-audit).** The namespace gap below was closed by adding an explicit `"slug"` field to each grounded curriculum entry and reconciling the allowlist against it. English is now **21 active slugs** (4 reserved: `concord`, `inference`, `spelling`, `word_formation`); Mathematics is **29 active slugs** (4 reserved: `logic`, `polynomials`, `triangles`, `vectors`). `stress`/`intonation` and `coordinate_geometry`/`probability`/`sequence_and_series` were split into class-specific variants to match how the curriculum carries them. See `app/core/topics.py` and the `"slug"` fields in `app/data/curriculum/*.json`. The original findings are retained below for the audit record.

The **allowlist** (`app/core/topics.py`) uses short slugs (`quadratic_equations`, `concord`); the **curriculum JSONs** originally used full descriptive titles (`"Quadratic Equations"`, `"Development of Numbers and Numerals"`) with no explicit link. At audit time they were effectively **two disjoint namespaces**, which drove most findings below.

### 1. Allowlist topics with no matching curriculum entry

- **High — English: 0 of 23 allowlist slugs match any curriculum `topic` title** (normalized exact-match). Even by loose substring, **11/23 have no curriculum match at all**: `concord`, `articles`, `sentence_structure`, `inference`, `vocabulary_in_context`, `reading_skills`, `word_formation`, `spelling`, `essay_writing`, `narrative_writing`, `descriptive_writing`. The English curriculum bundles skills into composite unit titles (e.g. *"Parts of Speech (1): Nouns, Pronouns and Verbs"*), so per-skill slugs never line up. *(Resolved via `"slug"` fields — the 21 active slugs now each map to a real entry; the 4 unmappable ones were moved to `ENGLISH_TOPICS_RESERVED`.)*
- **High — Mathematics: only 4 of 30 slugs match** (`probability`, `quadratic_equations`, `sets`, `simultaneous_equations`). **8/30 have no curriculum match even by substring**: `numbers_and_numeration`, `ratio_and_proportion`, `polynomials`, `logic`, `plane_geometry`, `triangles`, `vectors`, `sequence_and_series`. *(Resolved via `"slug"` fields — 29 active slugs now map; `logic`/`polynomials`/`triangles`/`vectors` moved to `MATHS_TOPICS_RESERVED`.)*

**Impact (original):** `LearningPathService` injects *both* the slug list and the curriculum titles into the prompt ([learning_path_service.py:140-154](app/services/learning_path_service.py#L140-L154)) and orders the LLM to output slugs. The two lists described different granularities, so the "curriculum reference" was largely non-actionable and the model got contradictory guidance. *(Now the injected slugs are the same ones tagged on curriculum entries, so the reference is actionable.)*

### 2. Curriculum topics not in the allowlist

- **High — The vast majority.** 82 Mathematics and 72 English curriculum entries exist; only a handful normalize to any allowlist slug. Essentially every curriculum title (e.g. *"Number Base System"*, *"Oral English: Vowel Sounds (Continued) and Tenses"*) is absent from the allowlist. `LearningPathResponse.recommended_order` is **not** re-validated against the allowlist, so the LLM can emit curriculum-style names that later fail `/content`'s strict slug validation.

### 3. Duplicate topic identifiers within a subject

- **Medium — Mathematics `mathematics.json`:** `"Areas of Plane Shapes"` appears in **JSS1/Third and JSS3/First**; `"Probability"` appears in **JSS2/Third and SS3/First**. English has no duplicate titles. (Spiral-curriculum repetition may be intentional, but identical titles across levels are ambiguous identifiers — no per-entry ID field exists to disambiguate.)

### 4. Inconsistent field structure between entries

- **Low — Good news:** structurally consistent. All 82 Maths and 72 English entries share exactly `{topic, subtopics, learning_objectives, estimated_hours, exam_relevance}`. No missing/extra keys detected. (The inconsistency is *between the allowlist and curriculum namespaces*, per 3.1–3.2, not within the JSON.)

### 5. Placeholder / test data that shouldn't be in production

- **Medium — `sample.txt`** (tracked in git) contains example request payloads — dev scratch, not production content.
- **Low — `evaluation/` results CSVs and reports** (`per_topic_8b.csv`, `summary_70b.csv`, etc.) are research artifacts shipped in the repo.
- **Low — `server.log` / `server_run.log`** runtime logs present in the working tree.

---

## Pass 4: Security & Config Audit

### 1. Hardcoded secrets

- **Good — No API keys hardcoded.** `GROQ_API_KEY`/`GROQ_MODEL` via env ([config.py:6-10](app/core/config.py#L6-L10)); `YOUTUBE_API_KEY` via `os.getenv`/`os.environ` ([content_service.py:122](app/services/content_service.py#L122), [youtube_recommender.py:173](youtube_recommender.py#L173)). `.env.example` contains only placeholders.

### 2. CORS configuration

- **High — Over-permissive and technically invalid combo.** [main.py:22-28](main.py#L22-L28) sets `allow_origins=["*"]` **together with** `allow_credentials=True`. Per the CORS spec browsers reject a wildcard origin when credentials are allowed, and `allow_methods=["*"]` + `allow_headers=["*"]` opens every method/header to any site. For a student-data service this is too broad — restrict to known frontend origins and drop credentials or name explicit origins.

### 3. Input reaching the LLM without validation

- **Medium — `POST /content` accepts arbitrary `subject`.** `invalid_topics` returns `[]` for any unknown subject ([topics.py:76-77](app/core/topics.py#L76-L77)), so the topic validator is a no-op for non-pilot subjects, and `ContentService.generate` has no subject allowlist (unlike `LearningPathService`'s `PILOT_SUBJECTS` guard at [learning_path_service.py:133](app/services/learning_path_service.py#L133)). Any subject string flows straight into the prompt.
- **Medium — Pipeline schema under-validates.** `GenerateLearningRequest.class_level`, `.term`, `.content_depth` are plain `str` ([pipeline.py schema:10-13](app/schemas/pipeline.py#L10-L13)) — not the `Literal` enums used elsewhere — so unconstrained strings reach the curriculum lookup and prompts.
- **Medium — Free-text fields are prompt-injectable.** `student_profile` (arbitrary `dict`, [learning_style.py:15](app/schemas/learning_style.py#L15)), `focus_reason`, `content_depth`, and `topic`/`subject` strings are interpolated into prompt templates ([learning_style_service.py:81](app/services/learning_style_service.py#L81), [content_service.py:151-161](app/services/content_service.py#L151-L161)) with no sanitization — a crafted value can steer the model.
- **Low — `learning_style_scores: Dict[str,int]`** ([learning_style.py:13](app/schemas/learning_style.py#L13)) doesn't constrain keys to `visual/auditory/kinesthetic`, so nonsense score maps are accepted.

### 4. .env / credential files in git

- **Good — `.env` is git-ignored** ([.gitignore:10](.gitignore#L10)) and confirmed **not tracked** (`git ls-files` shows only `.env.example`). `.venv/`, `*.log`, `__pycache__/` also ignored.
- **Low — `CLAUDE.md` is git-ignored** ([.gitignore:18](.gitignore#L18)) — intentional but worth noting (project docs excluded from the repo).
- **Note:** a local `.env` exists in the working directory. It is ignored, so it won't be committed — but confirm it was never committed in earlier history if the key is sensitive.

---

## Prioritized Fix List

Ordered: most-likely cause of your current 500 first, then by severity.

1. **[Breaking] Fix the pipeline Stage-1 input mismatch.** `/api/generate-learning/` passes `StudentActivity` (only `.activity`) to `evaluate()`, which reads `.student_profile`/`.learning_style_scores`/`.cognitive_score` → `AttributeError` → 500 on every call. Align `GenerateLearningRequest.student_activity` with `LearningStyleRequest`'s fields (or change `evaluate` to consume `activity`). — [pipeline.py:39](app/routes/pipeline.py#L39), [learning_style_service.py:81-85](app/services/learning_style_service.py#L81-L85), [learning_style.py:8-15](app/schemas/learning_style.py#L8-L15)
2. **[Breaking→High] Add error handling to `/api/learning-style/detailed`.** No try/except; strict `PydanticOutputParser` turns any LLM/schema miss into a raw 500. Wrap and map to 502/422. — [learning_style.py:11-16](app/routes/learning_style.py#L11-L16)
3. **[High] Verify `GROQ_MODEL` is a live Groq model and pin dependencies.** Floating `langchain*` versions + a possibly-retired model make all LLM endpoints 500-prone. Pin versions in `requirements.txt` and confirm the model name against Groq's current catalog. — [config.py:10](app/core/config.py#L10), `requirements.txt`
4. **[High] ✅ DONE — Reconcile allowlist slugs with curriculum titles.** Two disjoint namespaces (English 0/23 exact match; Maths 4/30) made learning-path prompts contradictory. **Resolved:** a `"slug"` field was added to each grounded curriculum entry and the allowlist reconciled to it — English 21 active / 4 reserved, Maths 29 active / 4 reserved, with class-split variants. Remaining follow-up: `recommended_order` is still not re-validated against the allowlist (see Pass 3.2). — [topics.py](app/core/topics.py), [learning_path_service.py:140-154](app/services/learning_path_service.py#L140-L154)
5. **[High] Tighten CORS.** Replace `allow_origins=["*"]` + `allow_credentials=True` with explicit frontend origins. — [main.py:22-28](main.py#L22-L28)
6. **[High] De-duplicate the topic-slug validator** into one shared function (currently copy-pasted 3×). — [content.py:37-47](app/routes/content.py#L37-L47), [learning_path.py:36-52](app/routes/learning_path.py#L36-L52), [pipeline.py schema:18-34](app/schemas/pipeline.py#L18-L34)
7. **[Medium] Fix `/content` error mapping** — internal LLM `ValueError` is returned to clients as 400. — [content.py:96-97](app/routes/content.py#L96-L97), [content_service.py:165](app/services/content_service.py#L165)
8. **[Medium] Stop leaking stack traces** from `/videos` 500 responses. — [videos.py:39-43](app/routes/videos.py#L39-L43)
9. **[Medium] Validate `subject`/`class_level`/`term`/`content_depth`** in `/content` and the pipeline schema (use the `Literal` enums; add a `PILOT_SUBJECTS` guard to `ContentService`). — [content_service.py](app/services/content_service.py), [pipeline.py schema:10-13](app/schemas/pipeline.py#L10-L13)
10. **[Medium] Centralize DI factories** (`get_content_service`, `get_learning_path_service`) into `app/core/dependencies.py`; remove duplicates. — [pipeline.py:13-18](app/routes/pipeline.py#L13-L18)
11. **[Medium] Guard/parse YouTube JSON** access (`item["id"]["videoId"]`, `item["id"]`) against malformed responses. — [youtube_recommender.py:201/236](youtube_recommender.py#L201)
12. **[Medium] Disambiguate duplicate curriculum titles** (`"Areas of Plane Shapes"`, `"Probability"`) or add per-entry IDs. — `mathematics.json`
13. **[Low] Remove dead code/imports:** unused router aliases in `main.py`, `LearningStyleResponse`, unused `student_id` threading. — [main.py:3-6](main.py#L3-L6), [learning_style.py:48-49](app/schemas/learning_style.py#L48-L49)
14. **[Low] Remove stray artifacts** from the repo/working tree: `sample.txt` (tracked), `server.log`, `server_run.log`, `evaluation/results/*`.
15. **[Low] Unify env-key handling** for `YOUTUBE_API_KEY` (consistent missing-key behavior) and consolidate duplicate `load_dotenv()`. — [content_service.py:122](app/services/content_service.py#L122), [youtube_recommender.py:23/173](youtube_recommender.py#L173)
16. **[Low] Consider prompt-injection hardening** for free-text `student_profile`/`focus_reason`/`topic` fields interpolated into prompts.
