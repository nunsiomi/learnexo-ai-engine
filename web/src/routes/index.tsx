import { createFileRoute, Link, Navigate } from "@tanstack/react-router";
import { useState, useRef, useEffect, type FormEvent } from "react";
import {
  generateLearningPath,
  evaluateLearningStyle,
  prettify,
  TOPIC_SLUGS,
  type LearningStyleResult,
  type GenerateResponse,
} from "@/lib/api";
import {
  STYLE_QUESTIONS,
  tallyStyleScores,
  tallyTopicScores,
  getQuestions,
  shuffledStyleOrder,
  type StyleChoice,
  type MCQOption,
} from "@/lib/quiz-data";
import { useAuth } from "@/lib/auth-context";
import { supabase } from "@/lib/supabase";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "LearNEXO · Personalized learning paths for Nigerian students" },
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

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type Subject = "Mathematics" | "English Language";
type ClassLevel = "JSS1" | "JSS2" | "JSS3" | "SS1" | "SS2" | "SS3";
type Term = "First" | "Second" | "Third";
type WizardStep = "profile" | "quiz" | "quiz-result" | "assessment" | "assessment-result" | "results";
type GenerateStatus = "idle" | "loading" | "success" | "error";

const CLASS_LEVELS: ClassLevel[] = ["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"];
const TERMS: Term[] = ["First", "Second", "Third"];
const SUBJECTS: Subject[] = ["Mathematics", "English Language"];

// Emoji for style types
const STYLE_EMOJI: Record<StyleChoice, string> = {
  visual: "🎨",
  auditory: "🎧",
  kinesthetic: "⚡",
};
const STYLE_COLOR: Record<StyleChoice, string> = {
  visual: "oklch(0.6 0.2 150)",
  auditory: "oklch(0.6 0.2 40)",
  kinesthetic: "oklch(0.58 0.19 258)",
};

// ---------------------------------------------------------------------------
// Root component — wizard state machine
// ---------------------------------------------------------------------------

function Index() {
  const { user, profile, loading: authLoading } = useAuth();

  // Profile
  const [classLevel, setClassLevel] = useState<ClassLevel>("JSS1");
  const [term, setTerm] = useState<Term>("First");
  const metaFirstName = (user?.user_metadata as { first_name?: string } | undefined)?.first_name?.trim();
  const displayName = metaFirstName || profile?.full_name?.trim().split(" ")[0] || "there";

  // Prefill class level from the student's saved profile once it loads.
  useEffect(() => {
    if (
      profile?.default_class_level &&
      (CLASS_LEVELS as string[]).includes(profile.default_class_level)
    ) {
      setClassLevel(profile.default_class_level as ClassLevel);
    }
  }, [profile]);

  // Quiz
  const [quizAnswers, setQuizAnswers] = useState<StyleChoice[]>([]);
  const [styleResult, setStyleResult] = useState<LearningStyleResult | null>(null);
  const [styleScores, setStyleScores] = useState<{ visual: number; auditory: number; kinesthetic: number } | null>(null);
  const [styleLoading, setStyleLoading] = useState(false);
  const [styleError, setStyleError] = useState(false);

  // Assessment — Phase 10: both subjects are assessed per session, in a fixed
  // order (SUBJECTS). Per-subject results are accumulated keyed by subject so
  // switching subjects never loses or bleeds data between them.
  const [subjectIndex, setSubjectIndex] = useState(0);
  const currentSubject = SUBJECTS[subjectIndex];
  const isLastSubject = subjectIndex === SUBJECTS.length - 1;

  const [weakBySubject, setWeakBySubject] = useState<Partial<Record<Subject, string[]>>>({});
  const [strongBySubject, setStrongBySubject] = useState<Partial<Record<Subject, string[]>>>({});
  const [aiWeakBySubject, setAiWeakBySubject] = useState<Partial<Record<Subject, string[]>>>({});
  const [aiStrongBySubject, setAiStrongBySubject] = useState<Partial<Record<Subject, string[]>>>({});

  const weakTopics = weakBySubject[currentSubject] ?? [];
  const strongTopics = strongBySubject[currentSubject] ?? [];
  const aiWeakTopics = aiWeakBySubject[currentSubject] ?? [];
  const aiStrongTopics = aiStrongBySubject[currentSubject] ?? [];

  const setWeakTopics = (topics: string[]) =>
    setWeakBySubject((prev) => ({ ...prev, [currentSubject]: topics }));
  const setStrongTopics = (topics: string[]) =>
    setStrongBySubject((prev) => ({ ...prev, [currentSubject]: topics }));

  // Results — one GenerateResponse per subject, both populated together once
  // the second (last) subject's assessment is confirmed.
  const [generateStatus, setGenerateStatus] = useState<GenerateStatus>("idle");
  const [resultsBySubject, setResultsBySubject] = useState<Partial<Record<Subject, GenerateResponse>>>({});

  // Wizard step
  const [step, setStep] = useState<WizardStep>("profile");

  // ---- handlers ----

  const handleProfileNext = () => setStep("quiz");

  const handleQuizComplete = async (answers: StyleChoice[]) => {
    setQuizAnswers(answers);
    const scores = tallyStyleScores(answers);
    setStyleScores(scores);
    setStyleLoading(true);
    setStyleError(false);
    try {
      const res = await evaluateLearningStyle(scores);
      setStyleResult(res);
    } catch {
      setStyleError(true);
    } finally {
      setStyleLoading(false);
      setStep("quiz-result");
    }
  };

  const handleQuizResultNext = () => setStep("assessment");

  const handleAssessmentComplete = (answers: Record<number, MCQOption>) => {
    const { weak, strong } = tallyTopicScores(answers, currentSubject, classLevel);
    setAiWeakBySubject((prev) => ({ ...prev, [currentSubject]: weak }));
    setAiStrongBySubject((prev) => ({ ...prev, [currentSubject]: strong }));
    setWeakBySubject((prev) => ({ ...prev, [currentSubject]: weak }));
    setStrongBySubject((prev) => ({ ...prev, [currentSubject]: strong }));
    setStep("assessment-result");
  };

  // Called from AssessmentResultEditor's "Generate"/"Continue" button. For
  // the first subject this just advances the queue to the next subject's
  // assessment — no API call yet. Only once the LAST subject is confirmed do
  // both subjects' learning paths get generated together, in parallel.
  const handleAssessmentResultNext = async () => {
    if (!isLastSubject) {
      setSubjectIndex((i) => i + 1);
      setStep("assessment");
      return;
    }

    setGenerateStatus("loading");
    setResultsBySubject({});
    try {
      const learningStyle = styleScores ?? { visual: 60, auditory: 20, kinesthetic: 20 };
      const entries = await Promise.all(
        SUBJECTS.map(async (subj) => {
          const data = await generateLearningPath({
            subject: subj,
            class_level: classLevel,
            term,
            learning_style: learningStyle,
            weak_topics: weakBySubject[subj] ?? [],
            strong_topics: strongBySubject[subj] ?? [],
          });
          return [subj, data] as const;
        })
      );
      setResultsBySubject(Object.fromEntries(entries));
      setGenerateStatus("success");
      setStep("results");
      requestAnimationFrame(() =>
        document.getElementById("results-top")?.scrollIntoView({ behavior: "smooth", block: "start" })
      );
    } catch {
      setGenerateStatus("error");
    }
  };

  const restart = () => {
    setStep("profile");
    setSubjectIndex(0);
    setQuizAnswers([]);
    setStyleResult(null);
    setStyleScores(null);
    setWeakBySubject({});
    setStrongBySubject({});
    setAiWeakBySubject({});
    setAiStrongBySubject({});
    setResultsBySubject({});
    setGenerateStatus("idle");
  };

  // ---- step order for the progress indicator ----
  const STEP_LABELS: { key: WizardStep; label: string }[] = [
    { key: "profile", label: "Profile" },
    { key: "quiz", label: "Learning Style" },
    { key: "assessment", label: `Assessment ${subjectIndex + 1}/${SUBJECTS.length}` },
    { key: "results", label: "Your Path" },
  ];
  const stepIndex = (s: WizardStep) => {
    if (s === "quiz-result") return 1;
    if (s === "assessment-result") return 2;
    return STEP_LABELS.findIndex((x) => x.key === s);
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-navy text-navy-foreground font-bold text-lg">
              L
            </div>
            <span className="text-xl font-bold tracking-tight text-foreground">
              Lear<span className="text-accent">NEXO</span>
            </span>
          </Link>
          <div className="flex items-center gap-4">
            {step !== "profile" && step !== "results" && (
              <button
                onClick={restart}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                ← Start over
              </button>
            )}
            <button
              onClick={() => supabase.auth.signOut()}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>

        {/* Progress indicator */}
        {step !== "results" && (
          <div className="mx-auto max-w-3xl px-5 pb-3">
            <div className="flex items-center gap-0">
              {STEP_LABELS.map((s, i) => {
                const current = stepIndex(step);
                const done = i < current;
                const active = i === current;
                return (
                  <div key={s.key} className="flex flex-1 items-center">
                    <div className="flex flex-col items-center gap-1">
                      <div
                        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold transition-all duration-300 ${
                          done
                            ? "bg-accent text-accent-foreground"
                            : active
                            ? "bg-navy text-navy-foreground ring-2 ring-accent/40"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {done ? "✓" : i + 1}
                      </div>
                      <span
                        className={`text-[10px] font-semibold uppercase tracking-wider hidden sm:block ${
                          active ? "text-foreground" : "text-muted-foreground"
                        }`}
                      >
                        {s.label}
                      </span>
                    </div>
                    {i < STEP_LABELS.length - 1 && (
                      <div className={`flex-1 h-0.5 mx-1 rounded-full transition-colors duration-500 ${done ? "bg-accent" : "bg-border"}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </header>

      <main className="mx-auto max-w-3xl px-5 py-10">
        {step === "profile" && (
          <ProfileStep
            name={displayName}
            classLevel={classLevel} setClassLevel={setClassLevel}
            term={term} setTerm={setTerm}
            onNext={handleProfileNext}
          />
        )}
        {step === "quiz" && (
          <LearningStyleQuiz onComplete={handleQuizComplete} />
        )}
        {step === "quiz-result" && (
          <QuizResultCard
            name={displayName}
            result={styleResult}
            scores={styleScores}
            loading={styleLoading}
            error={styleError}
            onNext={handleQuizResultNext}
          />
        )}
        {step === "assessment" && (
          <AcademicAssessment
            key={currentSubject}
            subject={currentSubject}
            classLevel={classLevel}
            subjectIndex={subjectIndex}
            onComplete={handleAssessmentComplete}
          />
        )}
        {step === "assessment-result" && (
          <AssessmentResultEditor
            key={currentSubject}
            name={displayName}
            subject={currentSubject}
            aiWeak={aiWeakTopics}
            aiStrong={aiStrongTopics}
            weak={weakTopics}
            setWeak={setWeakTopics}
            strong={strongTopics}
            setStrong={setStrongTopics}
            status={generateStatus}
            isLastSubject={isLastSubject}
            nextSubject={isLastSubject ? undefined : SUBJECTS[subjectIndex + 1]}
            onGenerate={handleAssessmentResultNext}
          />
        )}
        {step === "results" && Object.keys(resultsBySubject).length > 0 && (
          <div id="results-top">
            {generateStatus === "error" && <ErrorState onRetry={handleAssessmentResultNext} />}
            {generateStatus === "success" && (
              <Results
                name={displayName}
                dataBySubject={resultsBySubject as Record<Subject, GenerateResponse>}
                onRestart={restart}
              />
            )}
          </div>
        )}
        {step === "results" && generateStatus === "loading" && <LoadingSkeleton />}
      </main>

      <footer className="border-t border-border py-8 mt-10">
        <div className="mx-auto max-w-3xl px-5 text-center text-xs text-muted-foreground">
          © {new Date().getFullYear()} LearNEXO · AI-powered learning for Nigerian secondary students
        </div>
      </footer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 1 — Profile Setup
// ---------------------------------------------------------------------------

function ProfileStep({
  name,
  classLevel, setClassLevel,
  term, setTerm,
  onNext,
}: {
  name: string;
  classLevel: ClassLevel; setClassLevel: (c: ClassLevel) => void;
  term: Term; setTerm: (t: Term) => void;
  onNext: () => void;
}) {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-10">
        <p className="text-xs font-bold uppercase tracking-widest text-accent mb-3">Step 1 of 3</p>
        <h1 className="text-4xl font-bold leading-tight tracking-tight text-foreground sm:text-5xl">
          Hi {name}, let's <span className="text-accent">get started.</span>
        </h1>
        <p className="mt-4 text-base text-muted-foreground sm:text-lg max-w-xl">
          Confirm your class and term. Then we'll figure out how you learn best and where to focus your energy across both Mathematics and English Language.
        </p>
      </div>

      <div className="rounded-3xl border border-border bg-card p-6 shadow-card sm:p-8 space-y-6">
        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="class">Class level</label>
            <select
              id="class"
              className="field-input"
              value={classLevel}
              onChange={(e) => setClassLevel(e.target.value as ClassLevel)}
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
              onChange={(e) => setTerm(e.target.value as Term)}
            >
              {TERMS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>

        <div className="rounded-2xl bg-muted p-4 text-sm text-muted-foreground leading-relaxed">
          <span className="font-semibold text-foreground">What happens next? </span>
          You'll take a short learning-style quiz, then a quick assessment in each subject, and we'll generate a fully personalised learning path for you.
        </div>

        <div className="flex justify-end">
          <button id="profile-next" onClick={onNext} className="btn-pill btn-pill-accent">
            Start Learning Style Quiz →
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2 — Learning Style Quiz
// ---------------------------------------------------------------------------

const OPTION_MARKERS = ["A", "B", "C"];

function LearningStyleQuiz({ onComplete }: { onComplete: (answers: StyleChoice[]) => void }) {
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<StyleChoice[]>([]);
  const [selected, setSelected] = useState<StyleChoice | null>(null);
  const [animating, setAnimating] = useState(false);
  const [seed] = useState(() => Math.floor(Math.random() * 1_000_000_000));

  const question = STYLE_QUESTIONS[current];
  const total = STYLE_QUESTIONS.length;
  const progress = ((current) / total) * 100;
  const optionOrder = shuffledStyleOrder(seed, question.id);

  const choose = (choice: StyleChoice) => {
    if (animating) return;
    setSelected(choice);
    setAnimating(true);
    setTimeout(() => {
      const next = [...answers, choice];
      setAnswers(next);
      setSelected(null);
      setAnimating(false);
      if (current + 1 < total) {
        setCurrent(current + 1);
      } else {
        onComplete(next);
      }
    }, 350);
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8">
        <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Learning Style Test</p>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
          How do you learn best?
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Pick the option that feels most like you. There are no wrong answers.
        </p>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex justify-between text-xs text-muted-foreground mb-2">
          <span>Question {current + 1} of {total}</span>
          <span>{Math.round(progress)}% complete</span>
        </div>
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-accent transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className={`rounded-3xl border border-border bg-card p-6 shadow-card sm:p-8 transition-opacity duration-300 ${animating ? "opacity-40" : "opacity-100"}`}>
        <p className="text-lg font-semibold text-foreground mb-6 leading-snug">
          {question.scenario}
        </p>

        <div className="space-y-3">
          {optionOrder.map((style, idx) => (
            <button
              key={style}
              id={`quiz-option-${style}`}
              onClick={() => choose(style)}
              disabled={animating}
              className={`w-full text-left rounded-2xl border-2 p-4 transition-all duration-200 group ${
                selected === style
                  ? "border-accent bg-accent/10 scale-[0.99]"
                  : "border-border bg-card hover:border-accent/50 hover:bg-muted/60 hover:scale-[0.995]"
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold transition-colors duration-200 ${
                    selected === style
                      ? "bg-accent text-accent-foreground"
                      : "bg-muted text-muted-foreground group-hover:bg-accent/20"
                  }`}
                >
                  {OPTION_MARKERS[idx]}
                </span>
                <p className="text-sm font-medium text-foreground leading-snug">
                  {question.options[style]}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quiz Result Card (shown after quiz + API call)
// ---------------------------------------------------------------------------

function QuizResultCard({
  name, result, scores, loading, error, onNext,
}: {
  name: string;
  result: LearningStyleResult | null;
  scores: { visual: number; auditory: number; kinesthetic: number } | null;
  loading: boolean;
  error: boolean;
  onNext: () => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-5 py-20 animate-in fade-in duration-300">
        <div className="h-12 w-12 rounded-full border-4 border-border border-t-accent animate-spin" />
        <p className="text-sm text-muted-foreground">Analysing your learning style, {name}…</p>
      </div>
    );
  }

  const style = result?.learning_style ?? "visual";
  const emoji = STYLE_EMOJI[style];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8">
        <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Result</p>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">Your Learning Style</h2>
      </div>

      {error || !result ? (
        <div className="rounded-3xl bg-navy p-8 text-navy-foreground text-center">
          <p className="text-lg font-bold mb-2">Couldn't connect to the AI right now.</p>
          <p className="text-sm text-navy-foreground/70 mb-6">
            We'll use your quiz answers directly to personalise your path.
          </p>
          {scores && (
            <div className="flex justify-center gap-6 mb-6">
              {(["visual", "auditory", "kinesthetic"] as StyleChoice[]).map((s) => (
                <div key={s} className="text-center">
                  <p className="text-2xl font-bold">{scores[s]}</p>
                  <p className="text-xs uppercase tracking-widest text-navy-foreground/60 capitalize">{s}</p>
                </div>
              ))}
            </div>
          )}
          <button id="quiz-result-next-fallback" onClick={onNext} className="btn-pill btn-pill-accent">
            Continue to Assessment →
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="rounded-3xl bg-navy p-8 text-navy-foreground shadow-navy sm:p-10">
            <div className="flex items-center gap-4 mb-5">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl text-3xl" style={{ background: `${STYLE_COLOR[style]}25` }}>
                {emoji}
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-navy-foreground/60 mb-1">You are a</p>
                <h3 className="text-3xl font-bold tracking-tight">{result.friendly_label}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <div className="h-1.5 w-24 rounded-full bg-white/20 overflow-hidden">
                    <div className="h-full rounded-full bg-accent" style={{ width: `${result.confidence * 100}%` }} />
                  </div>
                  <span className="text-xs text-navy-foreground/60">{Math.round(result.confidence * 100)}% confidence</span>
                </div>
              </div>
            </div>

            <p className="text-base leading-relaxed text-navy-foreground/90 mb-6">{result.what_it_means}</p>

            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-navy-foreground/60 mb-3">How LearNEXO adapts for you</p>
              <ul className="space-y-2">
                {result.how_platform_adapts.map((tip, i) => (
                  <li key={i} className="flex gap-2 text-sm text-navy-foreground/85">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="rounded-3xl border border-border bg-card p-6 shadow-card">
            <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">Your study tips</p>
            <div className="grid gap-3 sm:grid-cols-3">
              {result.study_tips.map((tip, i) => (
                <div key={i} className="rounded-2xl bg-muted p-4">
                  <p className="text-xs font-bold text-accent mb-1">Tip {i + 1}</p>
                  <p className="text-sm text-foreground leading-snug">{tip}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end">
            <button id="quiz-result-next" onClick={onNext} className="btn-pill btn-pill-accent">
              Take Academic Assessment →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3 — Academic Assessment (MCQ)
// ---------------------------------------------------------------------------

function AcademicAssessment({
  subject, classLevel, subjectIndex, onComplete,
}: {
  subject: Subject;
  classLevel: ClassLevel;
  subjectIndex: number;
  onComplete: (answers: Record<number, MCQOption>) => void;
}) {
  const questions = getQuestions(subject, classLevel);
  const [answers, setAnswers] = useState<Record<number, MCQOption>>({});
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const answered = Object.keys(answers).length;
  const total = questions.length;
  const allAnswered = answered === total;

  const pick = (qId: number, opt: MCQOption) => {
    setAnswers((prev) => ({ ...prev, [qId]: opt }));
    setError("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!allAnswered) {
      setError(`Please answer all ${total} questions before continuing.`);
      return;
    }
    setSubmitted(true);
    onComplete(answers);
  };

  const OPTIONS: MCQOption[] = ["A", "B", "C", "D"];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8">
        <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">
          Academic Assessment · Subject {subjectIndex + 1} of {SUBJECTS.length}
        </p>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
          {subject} · {classLevel}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Answer all {total} questions. Your results will identify your strong and weak areas so we can build the right learning path.
        </p>
      </div>

      {/* Mini progress */}
      <div className="mb-6 flex items-center gap-3">
        <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-accent transition-all duration-500"
            style={{ width: `${(answered / total) * 100}%` }}
          />
        </div>
        <span className="text-xs text-muted-foreground whitespace-nowrap">{answered}/{total} answered</span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {questions.map((q, idx) => (
          <div
            key={q.id}
            className={`rounded-3xl border bg-card p-5 shadow-card sm:p-6 transition-colors duration-200 ${
              answers[q.id] ? "border-accent/30" : "border-border"
            }`}
          >
            <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">
              Question {idx + 1}
            </p>
            <p className="text-base font-semibold text-foreground mb-4 leading-snug">
              {q.question}
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {OPTIONS.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  id={`q${q.id}-${opt}`}
                  onClick={() => pick(q.id, opt)}
                  className={`text-left rounded-xl border-2 px-4 py-3 text-sm font-medium transition-all duration-150 ${
                    answers[q.id] === opt
                      ? "border-accent bg-accent/10 text-foreground"
                      : "border-border bg-card text-muted-foreground hover:border-accent/40 hover:text-foreground"
                  }`}
                >
                  <span className="font-bold mr-2">{opt}.</span>
                  {q.options[opt]}
                </button>
              ))}
            </div>
          </div>
        ))}

        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            id="assessment-submit"
            disabled={submitted}
            className="btn-pill btn-pill-accent"
          >
            {submitted ? "Scoring…" : "See My Results →"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3 result + topic editor — user can add/remove AI-determined topics
// ---------------------------------------------------------------------------

function AssessmentResultEditor({
  name, subject, aiWeak, aiStrong,
  weak, setWeak, strong, setStrong,
  status, isLastSubject, nextSubject, onGenerate,
}: {
  name: string;
  subject: Subject;
  aiWeak: string[];
  aiStrong: string[];
  weak: string[];
  setWeak: (t: string[]) => void;
  strong: string[];
  setStrong: (t: string[]) => void;
  status: GenerateStatus;
  isLastSubject: boolean;
  nextSubject?: Subject;
  onGenerate: () => void;
}) {
  const buttonLabel = isLastSubject
    ? status === "loading" ? "Generating…" : "Generate My Learning Path →"
    : `Continue to ${nextSubject} Assessment →`;
  const buttonDisabled = weak.length === 0 || (isLastSubject && status === "loading");

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8">
        <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">{subject} Assessment Complete</p>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">Your {subject} Topic Profile</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Nice work, {name}. Based on your answers, here's what we found. You can remove any topic or add extra ones before {isLastSubject ? "we generate your path" : `moving on to ${nextSubject}`}.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 mb-6">
        <TopicGroupEditor
          label="Weak topics"
          emoji="🔴"
          description="Topics you struggled with. We'll focus here."
          slugs={weak}
          onRemove={(slug) => setWeak(weak.filter((s) => s !== slug))}
          subject={subject}
          excluded={[...weak, ...strong]}
          onAdd={(slug) => setWeak([...weak, slug])}
          accentClass="border-destructive/40 bg-destructive/5"
        />
        <TopicGroupEditor
          label="Strong topics"
          emoji="🟢"
          description="Topics you know well. We'll use these as a foundation."
          slugs={strong}
          onRemove={(slug) => setStrong(strong.filter((s) => s !== slug))}
          subject={subject}
          excluded={[...weak, ...strong]}
          onAdd={(slug) => setStrong([...strong, slug])}
          accentClass="border-green-500/40 bg-green-500/5"
        />
      </div>

      {weak.length === 0 && (
        <div className="rounded-2xl bg-highlight p-4 text-sm text-highlight-foreground mb-6">
          <span className="font-semibold">No weak topics selected.</span> Add at least one so we can build a focused learning path for you.
        </div>
      )}

      {isLastSubject && status === "error" && (
        <p className="text-sm text-destructive mb-4">
          Something went wrong generating your path. Please try again.
        </p>
      )}

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <p className="text-xs text-muted-foreground sm:mr-auto sm:self-center">
          {weak.length} weak · {strong.length} strong topic{strong.length !== 1 ? "s" : ""} selected
        </p>
        <button
          id="generate-path"
          onClick={onGenerate}
          disabled={buttonDisabled}
          className="btn-pill btn-pill-accent"
        >
          {buttonLabel}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Topic group editor (used inside AssessmentResultEditor)
// ---------------------------------------------------------------------------

function TopicGroupEditor({
  label, emoji, description, slugs, onRemove,
  subject, excluded, onAdd, accentClass,
}: {
  label: string;
  emoji: string;
  description: string;
  slugs: string[];
  onRemove: (slug: string) => void;
  subject: Subject;
  excluded: string[];
  onAdd: (slug: string) => void;
  accentClass: string;
}) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const allSlugs = TOPIC_SLUGS[subject];
  const remaining = allSlugs.filter(
    (s) => !excluded.includes(s) && s.includes(search.toLowerCase().replace(/\s+/g, "_"))
  );

  const add = (slug: string) => {
    onAdd(slug);
    setSearch("");
    inputRef.current?.focus();
  };

  return (
    <div className={`rounded-3xl border-2 p-5 ${accentClass}`}>
      <div className="flex items-center gap-2 mb-1">
        <span>{emoji}</span>
        <p className="text-sm font-bold text-foreground">{label}</p>
      </div>
      <p className="text-xs text-muted-foreground mb-4">{description}</p>

      {/* Chips */}
      <div className="flex flex-wrap gap-2 mb-3 min-h-[2rem]">
        {slugs.length === 0 && (
          <p className="text-xs text-muted-foreground italic">None yet</p>
        )}
        {slugs.map((slug) => (
          <span
            key={slug}
            className="inline-flex items-center gap-1 rounded-full bg-card border border-border px-3 py-1 text-xs font-medium text-foreground"
          >
            {prettify(slug)}
            <button
              type="button"
              onClick={() => onRemove(slug)}
              className="ml-1 text-muted-foreground hover:text-destructive transition-colors"
              aria-label={`Remove ${prettify(slug)}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>

      {/* Add more */}
      <div className="relative">
        <input
          ref={inputRef}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder="+ Add a topic…"
          className="w-full rounded-xl border border-border bg-card px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-accent"
        />
        {open && remaining.length > 0 && (
          <ul className="absolute z-20 mt-1 max-h-40 w-full overflow-y-auto rounded-xl border border-border bg-card shadow-card">
            {remaining.map((slug) => (
              <li key={slug}>
                <button
                  type="button"
                  onMouseDown={(e) => { e.preventDefault(); add(slug); }}
                  className="w-full px-3 py-2 text-left text-xs text-foreground hover:bg-muted"
                >
                  {prettify(slug)}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Results (enhanced with estimated time indicator)
// ---------------------------------------------------------------------------

function Results({
  name, dataBySubject, onRestart,
}: {
  name: string;
  dataBySubject: Record<Subject, GenerateResponse>;
  onRestart: () => void;
}) {
  const subjects = SUBJECTS.filter((s) => dataBySubject[s]);
  const [activeSubject, setActiveSubject] = useState<Subject>(subjects[0]);
  const data = dataBySubject[activeSubject];
  const orderedContent = [...data.generated_content].sort((a, b) => a.priority - b.priority);
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
      {subjects.length > 1 && (
        <div className="flex gap-2">
          {subjects.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setActiveSubject(s)}
              className={`btn-pill text-sm ${activeSubject === s ? "btn-pill-accent" : "btn-pill-ghost"}`}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="rounded-3xl bg-navy p-7 text-navy-foreground shadow-navy sm:p-10">
        <p className="text-xs font-bold uppercase tracking-widest text-navy-foreground/60">Your personalised {activeSubject} plan, {name}</p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
          Recommended Learning Path
        </h2>

        <ol className="mt-6 space-y-3">
          {data.recommended_order.map((slug, i) => (
            <li key={slug} className="flex items-center gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-sm font-bold text-accent-foreground">
                {i + 1}
              </span>
              <span className="text-base font-medium">{prettify(slug)}</span>
            </li>
          ))}
        </ol>

        <div className="mt-7 border-t border-white/10 pt-5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-navy-foreground/60 mb-2">Strategy</h3>
          <p className="text-base leading-relaxed text-navy-foreground/90">{data.strategy}</p>
        </div>

        {data.focus_areas.length > 0 && (
          <div className="mt-5 border-t border-white/10 pt-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-navy-foreground/60 mb-3">Focus areas</h3>
            <div className="flex flex-wrap gap-2">
              {data.focus_areas.map((area, i) => (
                <span key={i} className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-navy-foreground/80">
                  {area}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {orderedContent.map((topic) => (
        <TopicCard key={topic.topic} topic={topic} />
      ))}

      <div className="flex justify-center pt-4">
        <button id="restart-btn" onClick={onRestart} className="btn-pill btn-pill-ghost text-sm">
          ← Start a new path
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Topic Card (enhanced with estimated time)
// ---------------------------------------------------------------------------

// Rough time estimates per priority band (can be replaced with curriculum data)
function estimatedTime(priority: number): string {
  if (priority <= 2) return "3–5 hrs";
  if (priority <= 4) return "2–3 hrs";
  return "1–2 hrs";
}

function TopicCard({ topic }: { topic: GenerateResponse["generated_content"][number] }) {
  return (
    <article className="rounded-3xl border border-border bg-card p-6 shadow-card sm:p-8">
      <div className="flex items-start justify-between gap-4 mb-1">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest text-accent">
              Priority {topic.priority}
            </span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              ⏱ {estimatedTime(topic.priority)}
            </span>
          </div>
          <h3 className="text-2xl font-bold tracking-tight text-foreground">
            {prettify(topic.topic)}
          </h3>
        </div>
      </div>

      <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
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

// ---------------------------------------------------------------------------
// Utility components
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="rounded-3xl bg-navy p-8 text-navy-foreground shadow-navy sm:p-10 animate-in fade-in duration-300">
      <div className="skeleton-line h-4 w-40 opacity-30" />
      <div className="mt-4 skeleton-line h-8 w-2/3 opacity-30" />
      <div className="mt-6 space-y-2">
        <div className="skeleton-line h-3 w-full opacity-20" />
        <div className="skeleton-line h-3 w-11/12 opacity-20" />
        <div className="skeleton-line h-3 w-4/5 opacity-20" />
      </div>
      <p className="mt-6 text-sm text-navy-foreground/70">Building your personalised plan… this can take a few seconds.</p>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-3xl border border-border bg-card p-8 text-center shadow-card">
      <h3 className="text-lg font-semibold text-foreground">Couldn't generate content right now.</h3>
      <p className="mt-2 text-sm text-muted-foreground">Please try again.</p>
      <button id="error-retry" onClick={onRetry} className="btn-pill btn-pill-accent mt-5">
        Try again
      </button>
    </div>
  );
}
