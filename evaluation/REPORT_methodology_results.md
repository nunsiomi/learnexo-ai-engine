# Evaluating Curriculum-Grounding in the Learning-Path Generator

*Draft Methodology and Results sections for the project report. Numbers are from the
evaluation harness in `evaluation/`; CSV outputs are in `evaluation/results/`.*

---

## 3. Methodology

### 3.1 Aim of the experiment

The learning-path stage of the system asks a Large Language Model (LLM) to order a
student's study topics. A known risk of LLMs is *hallucination* — generating
plausible-sounding content that is not actually valid. In this context, a hallucination
is a recommended topic that does **not** exist in the official Nigerian curriculum for the
student's subject, class, and term. To mitigate this, the system uses **curriculum
grounding**: the authoritative list of topics is injected into the prompt and the model is
explicitly instructed not to invent new topic names.

This experiment tests one hypothesis:

> **H1:** Curriculum grounding reduces the proportion of out-of-curriculum / hallucinated
> topics produced by the learning-path generator, compared with an ungrounded baseline.

### 3.2 Experimental conditions

To isolate the effect of grounding, the same learning-path generator was run under three
conditions that differ *only* in how the prompt is grounded. The model, temperature
(0.2), output parser, student inputs, and ordering instructions were held identical across
all three.

| Condition | Topic list injected? | "Do not invent" rule? | Input topic format |
|-----------|----------------------|------------------------|--------------------|
| **Grounded** (production system) | Yes | Yes | Slugs |
| **Ungrounded** | No | No | Slugs |
| **Ungrounded + readable** | No | No | Human-readable names |

The third condition is a control. Because the ungrounded condition still receives the
student's weak/strong topics as system slugs (e.g. `quadratic_equations`), those inputs
could *themselves* prime the model toward valid topics, masking the true effect of removing
grounding. The third condition replaces those slugs with human-readable names (e.g.
`Quadratic Equations`) so that any reduction in hallucination can be attributed to
grounding rather than to slug-formatted inputs.

### 3.3 Test sample

Eight synthetic student profiles were defined for Mathematics (the pilot subject), varied
across class level (JSS1–SS3), academic term, learning style (visual, auditory,
kinesthetic), and the size and difficulty of their weak/strong topic sets. Each profile was
run **3 times** per condition to account for the model's stochasticity, giving
8 × 3 × 3 = **72 LLM calls** per experiment.

### 3.4 Measuring hallucination

Every topic returned by the model was validated against **two** official reference
vocabularies, because the system distinguishes them:

1. **Slug vocabulary** — the 30 canonical Mathematics topic identifiers the system
   recognises (subject-wide).
2. **Curriculum names** — the official NERDC/WAEC topic names for that specific class and
   term, taken from the curriculum data files.

Each returned topic was classified against each reference as:

- **Exact** — normalised string equality (lower-cased, separators unified);
- **Borderline** — a fuzzy match (Python `difflib` similarity > 0.85, or substring
  containment) — flagged for manual review rather than silently accepted;
- **None** — no match.

A topic was counted as a **hallucination** only if it matched *neither* reference (i.e.
`none` against both the slug vocabulary and the curriculum names). The primary metric is the
**hallucination rate**: the percentage of all returned topics that were hallucinations.

### 3.5 Model note

The experiment was run on two models: the production model `llama-3.3-70b-versatile`, and
a smaller model `llama-3.1-8b-instant` as a robustness check. Both arms within each run use
the same model, so each run is an internally valid comparison.

---

## 4. Results

### 4.1 Primary result (production model, llama-3.3-70b-versatile)

72 calls completed with no failures (362 topics returned in total).

| Metric | Grounded | Ungrounded | Ungrounded + readable |
|---|---|---|---|
| **Hallucination rate** | **0.0%** | **3.8%** | **2.9%** |
| Topics matching slug vocabulary (exact) | 100.0% | 89.4% | 91.4% |
| Topics matching no slug (slug `none`) | 0.0% | 3.8% | 2.9% |
| Avg. topics returned per call | 6.38 | 4.33 | 4.38 |

Under grounding, **every one of the 153 returned topics was a valid system topic, and none
were hallucinated.** Removing grounding introduced hallucinated topics in both baselines.
**H1 is supported.**

### 4.2 The grounding effect is not an artefact of input format

The "ungrounded + readable" control hallucinated at **2.9%** — *not lower* than the plain
ungrounded condition (3.8%). If slug-formatted inputs had been the real cause of low
hallucination, the readable condition would have hallucinated substantially more. It did
not. This rules out input formatting as a confound and attributes the effect to the
grounding mechanism itself (the injected topic list and anti-invention instruction).

### 4.3 Examples of hallucinated topics (ungrounded conditions only)

The grounded condition produced no hallucinations. The ungrounded conditions invented
plausible-but-invalid topics, including:

- `differentiation` and `integration` — calculus topics that are **not part of the Nigerian
  secondary Mathematics curriculum** modelled by the system;
- `introduction_to_algebra`, `simple_equations`, `integers`, `graphs` — invented names that
  do not exist in the system's topic vocabulary.

These are exactly the kind of confident, reasonable-looking errors that grounding is
designed to prevent.

### 4.4 Robustness check (llama-3.1-8b-instant)

The same experiment on a smaller model showed the **same direction, with a larger effect**:

| Metric | Grounded | Ungrounded | Ungrounded + readable |
|---|---|---|---|
| **Hallucination rate** | **0.0%** | **20.4%** | **21.9%** |
| Topics matching slug vocabulary (exact) | 99.7% | 67.5% | 64.9% |

The weaker model hallucinated far more when ungrounded (≈1 in 5 topics), yet grounding
still drove hallucination to 0%. This indicates that grounding's benefit is **greater for
less capable models**, while the more capable 70B model has stronger built-in knowledge of
the curriculum and therefore hallucinates less even without grounding.

### 4.5 Summary of findings

1. Curriculum grounding eliminated hallucinated topics (0.0%) on both models.
2. Both ungrounded baselines hallucinated (3.8% on 70B, 20.4% on 8B); the effect is larger
   on the weaker model.
3. A control condition confirmed the effect is due to grounding, not input formatting.
4. The result is robust across two models of differing capability.

### 4.6 Threats to validity

- **Synthetic profiles.** The eight student profiles are constructed, not drawn from real
  students; results may differ on naturalistic inputs.
- **Single subject.** Only Mathematics was evaluated (the pilot subject); English Language
  was not tested.
- **Scale.** 72 calls per model is a small sample sufficient to demonstrate the effect but
  not to estimate it precisely; confidence intervals were not computed.
- **Borderline matches.** Topics that matched only fuzzily were flagged as "borderline" and
  excluded from the hallucination count; these were reviewed manually and are available in
  the per-topic results for transparency.
