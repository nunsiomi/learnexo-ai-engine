// Single source of truth for all LearNEXO backend calls.
//
// Integration points (Task 1 / Task 2):
//   - Base URL read from VITE_API_URL (set in web/.env — see web/.env.example).
//   - generateLearningPath() makes two sequential calls:
//       1. POST /learning-path  → recommended_order, strategy, focus_areas
//       2. POST /content        → generated_content[] per topic
//     Both results are merged into GenerateResponse so the existing
//     Results/TopicCard rendering in index.tsx needs no changes.
//   - If either call fails the whole function throws, which the submit handler
//     already catches and surfaces as ErrorState.

// ---------------------------------------------------------------------------
// Base URL
// ---------------------------------------------------------------------------

const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

export type LearningStyle = {
  visual: number;
  auditory: number;
  kinesthetic: number;
};

/** Shape returned by POST /api/learning-style/detailed */
export type LearningStyleResult = {
  learning_style: "visual" | "auditory" | "kinesthetic";
  friendly_label: string;
  confidence: number;
  what_it_means: string;
  how_platform_adapts: string[];
  recommended_formats: string[];
  study_tips: string[];
  explanation: string;
  risk_of_misclassification: "low" | "medium" | "high";
};

export type GenerateRequest = {
  subject: "Mathematics" | "English Language";
  class_level: "JSS1" | "JSS2" | "JSS3" | "SS1" | "SS2" | "SS3";
  term: "First" | "Second" | "Third";
  learning_style: LearningStyle;
  weak_topics: string[];
  strong_topics: string[];
};

export type VideoResource = { title: string; url: string; featured?: boolean };
export type MaterialResource = { title: string; description: string };

export type TopicContent = {
  topic: string;
  priority: number;
  explanation: {
    summary: string;
    key_points: string[];
  };
  resources: {
    videos: VideoResource[];
    materials: MaterialResource[];
  };
  recommended_action: string;
};

export type GenerateResponse = {
  recommended_order: string[];
  strategy: string;
  focus_areas: string[];
  generated_content: TopicContent[];
};

// ---------------------------------------------------------------------------
// Backend wire shapes (internal — not exported)
// ---------------------------------------------------------------------------

// POST /learning-path request/response
type LearningPathRequest = {
  learning_style: "visual" | "auditory" | "kinesthetic";
  subject: string;
  class_level: string;
  weak_topics: string[];
  strong_topics: string[];
  term: string;
};

type LearningPathResponse = {
  recommended_order: string[];
  strategy: string;
  focus_areas: string[];
};

// POST /content request/response
type ContentRequest = {
  mode: "multi_topic";
  topics: Array<{
    topic: string;
    // mastery and learning_stage are not collected by the form yet.
    // Defaulting to 0.3 / "foundation" is a reasonable placeholder that
    // produces foundation-level content for all topics in a student's weak
    // list — good for the initial assessment flow. When the form gains
    // per-topic mastery inputs, pass real values here instead.
    mastery: number;
    learning_stage: string;
  }>;
  subject: string;
  class_level: string;
  learning_style: "visual" | "auditory" | "kinesthetic";
  content_depth: "introduction" | "core" | "advanced" | "revision";
};

type ContentResponse = {
  generated_content: TopicContent[];
  recommended_start: string;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Derive the single dominant learning style label from the three scores. */
function dominantStyle(s: LearningStyle): "visual" | "auditory" | "kinesthetic" {
  const entries: [keyof LearningStyle, number][] = [
    ["visual", s.visual],
    ["auditory", s.auditory],
    ["kinesthetic", s.kinesthetic],
  ];
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0];
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    // Surface the status so error messages are debuggable in the console
    // without exposing raw backend internals to the user.
    throw new Error(`${path} responded ${res.status}`);
  }
  return (await res.json()) as T;
}

// ---------------------------------------------------------------------------
// Topic slug lists (Task 3 — read from topics.py, not guessed from memory)
// Source of truth: app/core/topics.py  ENGLISH_TOPICS / MATHS_TOPICS
// ---------------------------------------------------------------------------

export const TOPIC_SLUGS: Record<"Mathematics" | "English Language", string[]> = {
  "English Language": [
    "prepositions",
    "tenses",
    "sentence_structure",
    "synonyms",
    "antonyms",
    "idioms",
    "vocabulary_in_context",
    "comprehension",
    "reading_skills",
    "summary",
    "essay_writing",
    "letter_writing",
    "narrative_writing",
    "descriptive_writing",
    "articles",
    "vowel_sounds",
    "consonant_sounds",
    "stress_jss2",
    "stress_ss1",
    "intonation_jss2",
    "intonation_ss1",
  ],
  Mathematics: [
    "numbers_and_numeration",
    "basic_operations",
    "fractions",
    "decimals",
    "percentages",
    "ratio_and_proportion",
    "indices",
    "logarithms",
    "surds",
    "algebraic_expressions",
    "linear_equations",
    "simultaneous_equations",
    "quadratic_equations",
    "inequalities",
    "sets",
    "plane_geometry",
    "angles",
    "circles",
    "mensuration",
    "coordinate_geometry_ss1",
    "coordinate_geometry_ss2",
    "statistics",
    "probability_jss2",
    "probability_ss3",
    "sequence_arithmetic",
    "sequence_geometric",
    "commercial_arithmetic",
    "matrices",
    "trigonometry",
  ],
};

// ---------------------------------------------------------------------------
// Learning style evaluation (Step 2 of the onboarding wizard)
// ---------------------------------------------------------------------------

/**
 * Post pre-computed VAK scores (from the quiz) to the backend and get back
 * the full friendly LearningStyleEvaluation (label, tips, etc.).
 */
export async function evaluateLearningStyle(
  scores: LearningStyle,
): Promise<LearningStyleResult> {
  return postJson<LearningStyleResult>("/api/learning-style/detailed", {
    learning_style_scores: scores,
    cognitive_score: Math.round((scores.visual + scores.auditory + scores.kinesthetic) / 3),
    student_profile: {},
  });
}

// ---------------------------------------------------------------------------
// Main exported function (Task 2)
// ---------------------------------------------------------------------------

export async function generateLearningPath(
  input: GenerateRequest,
): Promise<GenerateResponse> {
  const style = dominantStyle(input.learning_style);

  // --- Call 1: learning path ---
  const pathBody: LearningPathRequest = {
    learning_style: style,
    subject: input.subject,
    class_level: input.class_level,
    weak_topics: input.weak_topics,
    strong_topics: input.strong_topics,
    term: input.term,
  };
  const pathData = await postJson<LearningPathResponse>("/learning-path", pathBody);

  // --- Call 2: content for every topic in the recommended order ---
  // We use all topics from recommended_order. If the list is empty (the
  // backend returned nothing), bail early with an empty content set.
  const topicsToFetch = pathData.recommended_order;
  if (topicsToFetch.length === 0) {
    return {
      recommended_order: [],
      strategy: pathData.strategy,
      focus_areas: pathData.focus_areas,
      generated_content: [],
    };
  }

  const contentBody: ContentRequest = {
    mode: "multi_topic",
    topics: topicsToFetch.map((slug) => ({
      topic: slug,
      mastery: 0.3,        // placeholder — form doesn't collect per-topic mastery yet
      learning_stage: "foundation", // placeholder — same rationale
    })),
    subject: input.subject,
    class_level: input.class_level,
    learning_style: style,
    content_depth: "core",
  };
  const contentData = await postJson<ContentResponse>("/content", contentBody);

  // Merge into the flat shape the Results/TopicCard components expect.
  return {
    recommended_order: pathData.recommended_order,
    strategy: pathData.strategy,
    focus_areas: pathData.focus_areas,
    generated_content: contentData.generated_content,
  };
}

// ---------------------------------------------------------------------------
// Utility — exported because index.tsx uses it to prettify slug display
// ---------------------------------------------------------------------------

export function prettify(slug: string): string {
  return slug
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}
