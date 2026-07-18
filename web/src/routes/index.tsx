import { createFileRoute } from "@tanstack/react-router";
import { useState, type FormEvent, type KeyboardEvent } from "react";
import {
  generateLearningPath,
  prettify,
  type GenerateRequest,
  type GenerateResponse,
} from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "LearNEXO — Personalized learning paths for Nigerian students" },
      {
        name: "description",
        content:
          "AI-powered personalized learning paths for Nigerian secondary school students (JSS1–SS3) in Mathematics and English Language.",
      },
      { property: "og:title", content: "LearNEXO" },
      {
        property: "og:description",
        content:
          "AI-powered personalized learning paths for Nigerian secondary students.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

type Status = "idle" | "loading" | "success" | "error";

const CLASS_LEVELS = ["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"] as const;
const TERMS = ["First", "Second", "Third"] as const;
const SUBJECTS = ["Mathematics", "English Language"] as const;

function Index() {
  const [subject, setSubject] = useState<(typeof SUBJECTS)[number]>("Mathematics");
  const [classLevel, setClassLevel] = useState<(typeof CLASS_LEVELS)[number]>("JSS1");
  const [term, setTerm] = useState<(typeof TERMS)[number]>("First");
  const [visual, setVisual] = useState<string>("");
  const [auditory, setAuditory] = useState<string>("");
  const [kinesthetic, setKinesthetic] = useState<string>("");
  const [weak, setWeak] = useState<string[]>([]);
  const [strong, setStrong] = useState<string[]>([]);
  const [weakDraft, setWeakDraft] = useState("");
  const [strongDraft, setStrongDraft] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<GenerateResponse | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (visual === "") errs.visual = "Required";
    if (auditory === "") errs.auditory = "Required";
    if (kinesthetic === "") errs.kinesthetic = "Required";
    if (weak.length === 0) errs.weak = "Add at least one weak topic";
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    const payload: GenerateRequest = {
      subject,
      class_level: classLevel,
      term,
      learning_style: {
        visual: Number(visual),
        auditory: Number(auditory),
        kinesthetic: Number(kinesthetic),
      },
      weak_topics: weak,
      strong_topics: strong,
    };

    await runGenerate(payload);
  };

  const runGenerate = async (payload: GenerateRequest) => {
    setStatus("loading");
    setResult(null);
    try {
      const data = await generateLearningPath(payload);
      setResult(data);
      setStatus("success");
      requestAnimationFrame(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch {
      setStatus("error");
    }
  };

  const retry = () => {
    const payload: GenerateRequest = {
      subject,
      class_level: classLevel,
      term,
      learning_style: {
        visual: Number(visual || 0),
        auditory: Number(auditory || 0),
        kinesthetic: Number(kinesthetic || 0),
      },
      weak_topics: weak,
      strong_topics: strong,
    };
    void runGenerate(payload);
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-background/70 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-navy text-navy-foreground font-bold">
              L
            </div>
            <span className="text-xl font-bold tracking-tight text-foreground">
              Lear<span className="text-accent">NEXO</span>
            </span>
          </div>
          <p className="hidden text-sm text-muted-foreground sm:block">
            AI-powered personalized learning paths for Nigerian secondary students
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-10 sm:py-16">
        <section className="mb-10 sm:mb-14">
          <h1 className="text-4xl font-bold leading-[1.1] tracking-tight text-foreground sm:text-5xl">
            Build a learning path
            <br />
            <span className="text-accent">shaped around you.</span>
          </h1>
          <p className="mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">
            Tell us your class, your subject, and how you learn best. We'll generate a focused
            plan for the topics that need the most attention this term.
          </p>
        </section>

        <form
          onSubmit={submit}
          className="rounded-3xl border border-border bg-card p-6 shadow-card sm:p-8"
        >
          <div className="grid gap-5 sm:grid-cols-3">
            <div>
              <label className="field-label" htmlFor="subject">Subject</label>
              <select
                id="subject"
                className="field-input"
                value={subject}
                onChange={(e) => setSubject(e.target.value as typeof subject)}
              >
                {SUBJECTS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="class">Class level</label>
              <select
                id="class"
                className="field-input"
                value={classLevel}
                onChange={(e) => setClassLevel(e.target.value as typeof classLevel)}
              >
                {CLASS_LEVELS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="term">Term</label>
              <select
                id="term"
                className="field-input"
                value={term}
                onChange={(e) => setTerm(e.target.value as typeof term)}
              >
                {TERMS.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div className="mt-7">
            <div className="mb-1 flex items-baseline justify-between">
              <h3 className="text-sm font-semibold text-foreground">Learning style (0–100)</h3>
              <span className="text-xs text-muted-foreground">All three required</span>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <StyleSlider label="Visual" value={visual} onChange={setVisual} error={errors.visual} />
              <StyleSlider label="Auditory" value={auditory} onChange={setAuditory} error={errors.auditory} />
              <StyleSlider label="Kinesthetic" value={kinesthetic} onChange={setKinesthetic} error={errors.kinesthetic} />
            </div>
          </div>

          <div className="mt-7 grid gap-6 sm:grid-cols-2">
            <TagInput
              label="Weak topics"
              hint="Topics you struggle with. Press Enter to add."
              tags={weak}
              setTags={setWeak}
              draft={weakDraft}
              setDraft={setWeakDraft}
              error={errors.weak}
            />
            <TagInput
              label="Strong topics"
              hint="Optional. Topics you're comfortable with."
              tags={strong}
              setTags={setStrong}
              draft={strongDraft}
              setDraft={setStrongDraft}
            />
          </div>

          <div className="mt-8 flex flex-col-reverse items-stretch gap-3 sm:flex-row sm:items-center sm:justify-end">
            <p className="text-xs text-muted-foreground sm:mr-auto">
              This page is stateless — your inputs aren't saved.
            </p>
            <button type="submit" className="btn-pill btn-pill-accent" disabled={status === "loading"}>
              {status === "loading" ? "Generating…" : "Generate My Learning Path"}
            </button>
          </div>
        </form>

        <section id="results" className="mt-10">
          {status === "loading" && <LoadingSkeleton />}
          {status === "error" && <ErrorState onRetry={retry} />}
          {status === "success" && result && <Results data={result} />}
        </section>
      </main>

      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-5xl px-5 text-center text-xs text-muted-foreground">
          © {new Date().getFullYear()} LearNEXO
        </div>
      </footer>
    </div>
  );
}

function StyleSlider({
  label, value, onChange, error,
}: { label: string; value: string; onChange: (v: string) => void; error?: string }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">{label}</label>
        <span className="text-sm tabular-nums text-muted-foreground">
          {value === "" ? "—" : value}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value === "" ? 50 : Number(value)}
        onChange={(e) => onChange(e.target.value)}
        onMouseDown={() => { if (value === "") onChange("50"); }}
        onTouchStart={() => { if (value === "") onChange("50"); }}
        className="w-full accent-[oklch(0.58_0.19_258)]"
      />
      <input
        type="number"
        min={0}
        max={100}
        value={value}
        onChange={(e) => {
          const v = e.target.value;
          if (v === "") return onChange("");
          const n = Math.max(0, Math.min(100, Number(v)));
          onChange(String(n));
        }}
        placeholder="Enter 0–100"
        className="field-input mt-2"
        aria-invalid={!!error}
      />
      {error && <p className="mt-1 text-xs text-destructive">{error}</p>}
    </div>
  );
}

function TagInput({
  label, hint, tags, setTags, draft, setDraft, error,
}: {
  label: string; hint: string;
  tags: string[]; setTags: (t: string[]) => void;
  draft: string; setDraft: (d: string) => void;
  error?: string;
}) {
  const add = () => {
    const v = draft.trim();
    if (!v) return;
    if (!tags.includes(v)) setTags([...tags, v]);
    setDraft("");
  };
  const remove = (t: string) => setTags(tags.filter((x) => x !== t));
  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      add();
    } else if (e.key === "Backspace" && draft === "" && tags.length) {
      setTags(tags.slice(0, -1));
    }
  };
  return (
    <div>
      <label className="field-label">{label}</label>
      <div
        className={`flex min-h-[3rem] flex-wrap items-center gap-2 rounded-xl border bg-card p-2 focus-within:border-accent focus-within:shadow-[0_0_0_4px_oklch(0.58_0.19_258/0.12)] ${
          error ? "border-destructive" : "border-border"
        }`}
      >
        {tags.map((t) => (
          <span key={t} className="inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-sm text-foreground">
            {t}
            <button
              type="button"
              onClick={() => remove(t)}
              className="ml-1 rounded-full text-muted-foreground hover:text-foreground"
              aria-label={`Remove ${t}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKey}
          onBlur={add}
          placeholder={tags.length === 0 ? "Type a topic and press Enter" : ""}
          className="min-w-[8rem] flex-1 border-0 bg-transparent px-2 py-1 text-sm outline-none"
        />
      </div>
      <p className={`mt-1 text-xs ${error ? "text-destructive" : "text-muted-foreground"}`}>
        {error ?? hint}
      </p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="rounded-3xl bg-navy p-8 text-navy-foreground shadow-navy sm:p-10">
      <div className="skeleton-line h-4 w-40 opacity-30" />
      <div className="mt-4 skeleton-line h-8 w-2/3 opacity-30" />
      <div className="mt-6 space-y-2">
        <div className="skeleton-line h-3 w-full opacity-20" />
        <div className="skeleton-line h-3 w-11/12 opacity-20" />
        <div className="skeleton-line h-3 w-4/5 opacity-20" />
      </div>
      <p className="mt-6 text-sm text-navy-foreground/70">
        Building your personalized plan… this can take a few seconds.
      </p>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-3xl border border-border bg-card p-8 text-center shadow-card">
      <h3 className="text-lg font-semibold text-foreground">
        Couldn't generate content right now.
      </h3>
      <p className="mt-2 text-sm text-muted-foreground">Please try again.</p>
      <button onClick={onRetry} className="btn-pill btn-pill-accent mt-5">
        Try again
      </button>
    </div>
  );
}

function Results({ data }: { data: GenerateResponse }) {
  const orderedContent = [...data.generated_content].sort((a, b) => a.priority - b.priority);
  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-navy p-7 text-navy-foreground shadow-navy sm:p-10">
        <p className="text-xs font-semibold uppercase tracking-widest text-navy-foreground/60">
          Your plan
        </p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
          Recommended Learning Path
        </h2>
        <ol className="mt-6 space-y-3">
          {data.recommended_order.map((slug, i) => (
            <li key={slug} className="flex items-start gap-3">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-sm font-bold text-accent-foreground">
                {i + 1}
              </span>
              <span className="text-lg font-medium">{prettify(slug)}</span>
            </li>
          ))}
        </ol>
        <div className="mt-7 border-t border-white/10 pt-5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-navy-foreground/60">
            Strategy
          </h3>
          <p className="mt-2 text-base leading-relaxed text-navy-foreground/90">
            {data.strategy}
          </p>
        </div>
      </div>

      {orderedContent.map((topic) => (
        <TopicCard key={topic.topic} topic={topic} />
      ))}
    </div>
  );
}

function TopicCard({ topic }: { topic: GenerateResponse["generated_content"][number] }) {
  return (
    <article className="rounded-3xl border border-border bg-card p-6 shadow-card sm:p-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-accent">
            Priority {topic.priority}
          </p>
          <h3 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            {prettify(topic.topic)}
          </h3>
        </div>
      </div>

      <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground">
        {topic.explanation.summary}
      </p>

      <div className="mt-5">
        <h4 className="text-sm font-semibold text-foreground">Key points</h4>
        <ul className="mt-2 space-y-1.5">
          {topic.explanation.key_points.map((k, i) => (
            <li key={i} className="flex gap-2 text-[15px] text-foreground">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              <span>{k}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-5 rounded-2xl border-l-4 border-accent bg-highlight p-4 text-highlight-foreground">
        <p className="text-xs font-bold uppercase tracking-widest">Recommended action</p>
        <p className="mt-1 text-[15px] font-medium">{topic.recommended_action}</p>
      </div>

      {topic.resources.videos.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-foreground">Videos</h4>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {topic.resources.videos.map((v, i) => (
              <a
                key={i}
                href={v.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group block overflow-hidden rounded-xl border border-border bg-muted transition hover:shadow-card"
              >
                <div className="relative aspect-video bg-navy">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-navy transition group-hover:scale-110">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  </div>
                  {v.featured && (
                    <span className="absolute left-2 top-2 rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold uppercase text-accent-foreground">
                      Featured
                    </span>
                  )}
                </div>
                <p className="p-2.5 text-xs font-medium text-foreground group-hover:text-accent">
                  {v.title}
                </p>
              </a>
            ))}
          </div>
        </div>
      )}

      {topic.resources.materials.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-foreground">Supplementary materials</h4>
          <ul className="mt-2 divide-y divide-border">
            {topic.resources.materials.map((m, i) => (
              <li key={i} className="py-3">
                <p className="text-[15px] font-semibold text-foreground">{m.title}</p>
                <p className="mt-0.5 text-sm text-muted-foreground">{m.description}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}
