// Single source of truth for the LearNEXO backend call.
// To swap the mock for a real API, replace the body of `generateLearningPath`
// with a fetch() to your endpoint. Keep the input/output shapes identical.

export type LearningStyle = {
  visual: number;
  auditory: number;
  kinesthetic: number;
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

// TODO: replace with real endpoint, e.g.
// const API_URL = "https://your-api.example.com/generate";
const USE_MOCK = true;

export async function generateLearningPath(
  input: GenerateRequest,
): Promise<GenerateResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 1600));
    // Uncomment to test error state:
    // throw new Error("mock failure");
    return mockResponse(input);
  }

  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return (await res.json()) as GenerateResponse;
}

function mockResponse(input: GenerateRequest): GenerateResponse {
  const weak = input.weak_topics.length
    ? input.weak_topics
    : ["algebraic_expressions", "linear_equations", "word_problems"];
  const order = weak.slice(0, 3);
  return {
    recommended_order: order,
    strategy:
      `Based on your ${input.class_level} ${input.term} term ${input.subject} profile, ` +
      `we're prioritizing your weakest areas first while reinforcing them with ` +
      `${dominantStyle(input.learning_style)}-focused resources. Work through ` +
      `topics in the order shown, complete each recommended action before moving on, ` +
      `and revisit the key points at the end of each week.`,
    focus_areas: order,
    generated_content: order.map((slug, i) => ({
      topic: slug,
      priority: i + 1,
      explanation: {
        summary:
          `${prettify(slug)} is a foundational topic for ${input.class_level}. ` +
          `Mastering it will unlock several later concepts and directly improve your ` +
          `performance in ${input.term.toLowerCase()} term assessments.`,
        key_points: [
          `Understand the core definition of ${prettify(slug).toLowerCase()}.`,
          "Practice at least 10 problems before attempting past questions.",
          "Learn to identify this topic inside worded questions.",
          "Review common mistakes and how to avoid them.",
        ],
      },
      resources: {
        videos: [
          {
            title: `${prettify(slug)} — Full Lesson`,
            url: "https://www.youtube.com/results?search_query=" + encodeURIComponent(prettify(slug)),
            featured: true,
          },
          {
            title: `${prettify(slug)} — Worked Examples`,
            url: "https://www.youtube.com/results?search_query=" + encodeURIComponent(prettify(slug) + " examples"),
          },
          {
            title: `${prettify(slug)} — Quick Recap`,
            url: "https://www.youtube.com/results?search_query=" + encodeURIComponent(prettify(slug) + " summary"),
          },
        ],
        materials: [
          {
            title: `${prettify(slug)} — Practice Worksheet`,
            description:
              "A printable set of 15 graded questions moving from easy to WAEC-standard difficulty.",
          },
          {
            title: `${prettify(slug)} — Concept Notes`,
            description:
              "Condensed one-page notes covering definitions, formulas, and worked steps.",
          },
        ],
      },
      recommended_action:
        i === 0
          ? "Start here today. Watch the full lesson, then attempt the first 5 practice questions."
          : `After completing topic ${i}, spend 30–45 minutes on this one before moving on.`,
    })),
  };
}

function prettify(slug: string) {
  return slug
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

function dominantStyle(s: LearningStyle) {
  const entries: [string, number][] = [
    ["visual", s.visual],
    ["auditory", s.auditory],
    ["kinesthetic", s.kinesthetic],
  ];
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0];
}

export { prettify };
