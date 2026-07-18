# Mathematics Slug ↔ Curriculum Match Report

**Scoring: token-based Jaccard word-set overlap** (intersection over union of stop-word-filtered words), with `difflib.SequenceMatcher` used only as a tiebreaker for equal Jaccard scores. **Matching now covers the full JSS1-SS3 range** (all six class levels are in one primary pool), not JSS1-JSS3. This **supersedes both prior versions** of this report — the original character-ratio version and the JSS1-JSS3-only token version; this full-scope token-based one is authoritative. Read-only diagnostic: no source files were modified.

**Thresholds used** (re-tuned for the Jaccard scale — see script comments)

- `CONFIDENT_THRESHOLD` = 0.34
- `AMBIGUOUS_GAP` = 0.1
- `MATCH_FLOOR` = 0.15
- `COVERAGE_FLOOR` = 0.15

**Scope of matching:** 30 allowlist slugs vs 82 curriculum topics across the full JSS1-SS3 range (JSS1, JSS2, JSS3, SS1, SS2, SS3 — all in one primary pass).

**Summary:** 9 confident · 17 ambiguous · 4 unmatched · 27 curriculum topics with no slug.

## MATHS_TOPICS Intended Scope (Task 2)

**Finding:** FULL JSS1-SS3 (secondary-wide) list that is NOT scoped by class level anywhere in code - NOT a JSS-only list.

Evidence from `app/core/topics.py` and this run:

- `MATHS_TOPICS` has no docstring or comment stating its scope, and its name carries no `JSS`/`SS` qualifier (it mirrors `ENGLISH_TOPICS`).
- `get_topics()` / `invalid_topics()` return and validate against the whole flat list; there is no class-level filtering anywhere in topics.py.
- The list contains topics that are unambiguously SS-level in the curriculum (e.g. `surds`, `logarithms`, `matrices`, `coordinate_geometry`, `sets`), plus `vectors` and `logic`, which appear in neither JSS nor SS.
- This run (full JSS1-SS3 pool): 12 slug(s) have their best match at an SS1-SS3 level (`indices`, `logarithms`, `simultaneous_equations`, `quadratic_equations`, `sets`, `matrices`, `surds`, `plane_geometry`, `circles`, `coordinate_geometry`, `statistics`, `sequence_and_series`), confirming the allowlist reaches beyond JSS content.
- No docstring explicitly *declares* the intended scope, so this is inferred from composition + absence of scoping code, not a stated contract. It is not, however, genuinely ambiguous: a JSS-only list would not include strictly-SS topics.

## 1. Confident Matches

_Sorted by score ascending, so the weakest 'confident' calls sit at the top._

| Slug | Best curriculum title | Class | Term | Score | Gap to 2nd |
| --- | --- | --- | --- | --- | --- |
| `ratio_and_proportion` | Fractions: Percentages, Ratio, Proportion and Rate | JSS2 | First | 0.400 | 0.200 |
| `indices` | Indices and Logarithms | SS1 | First | 0.500 | 0.167 |
| `logarithms` | Indices and Logarithms | SS1 | First | 0.500 | 0.500 |
| `matrices` | Matrices and Determinants | SS2 | First | 0.500 | 0.500 |
| `linear_equations` | Graphs of Linear Equations | JSS2 | Second | 0.667 | 0.167 |
| `commercial_arithmetic` | Household and Commercial Arithmetic | JSS2 | First | 0.667 | 0.467 |
| `simultaneous_equations` | Simultaneous Equations | SS1 | Second | 1.000 | 0.500 |
| `quadratic_equations` | Quadratic Equations | SS1 | Second | 1.000 | 0.667 |
| `sets` | Sets | SS1 | First | 1.000 | 1.000 |

## 2. Ambiguous

_Sorted by best score descending. Multiple curriculum titles score close together, or the best score sits below the confident threshold._

- `probability` — best 1.000, gap 0.000:
    - Probability (JSS2 Third) — 1.000
    - Probability (SS3 First) — 1.000
    - Word Problems (JSS3 First) — 0.000
- `coordinate_geometry` — best 0.667, gap 0.000:
    - Further Coordinate Geometry (SS2 Second) — 0.667
    - Introduction to Coordinate Geometry (SS1 First) — 0.667
    - Revision: Mensuration and Geometry (JSS3 Third) — 0.250
- `basic_operations` — best 0.500, gap 0.100:
    - Fractions (2): Basic Operations (JSS1 Second) — 0.500
    - Binary Number System: Basic Operations (JSS1 Second) — 0.400
    - Basic Operations on Whole Numbers and Decimals (JSS1 First) — 0.400
- `algebraic_expressions` — best 0.500, gap 0.000:
    - Use of Symbols and Algebraic Expressions (JSS1 Second) — 0.500
    - Directed Numbers and Algebraic Expressions (JSS2 Second) — 0.500
    - Revision: Algebraic Processes (JSS3 Third) — 0.250
- `fractions` — best 0.333, gap 0.083:
    - Decimals, Fractions and Percentages (JSS1 First) — 0.333
    - Fractions (2): Basic Operations (JSS1 Second) — 0.250
    - Fractions (1): Introduction and Equivalence (JSS1 First) — 0.250
- `decimals` — best 0.333, gap 0.133:
    - Decimals, Fractions and Percentages (JSS1 First) — 0.333
    - Basic Operations on Whole Numbers and Decimals (JSS1 First) — 0.200
    - Word Problems (JSS3 First) — 0.000
- `percentages` — best 0.333, gap 0.133:
    - Decimals, Fractions and Percentages (JSS1 First) — 0.333
    - Fractions: Percentages, Ratio, Proportion and Rate (JSS2 First) — 0.200
    - Differentiation (SS3 First) — 0.000
- `surds` — best 0.333, gap 0.333:
    - Surds and Further Indices (SS2 First) — 0.333
    - Sets (SS1 First) — 0.000
    - Squares and Square Roots (JSS2 First) — 0.000
- `angles` — best 0.333, gap 0.083:
    - Geometrical Constructions and Angles (JSS1 Third) — 0.333
    - Angles of Elevation and Depression, and Bearings (JSS2 Second) — 0.250
    - Trigonometry (2): Sine and Cosine of Angles (JSS3 Second) — 0.200
- `mensuration` — best 0.333, gap 0.083:
    - Revision: Mensuration and Geometry (JSS3 Third) — 0.333
    - Revision: Geometry, Mensuration and Statistics (SS1 Third) — 0.250
    - Mensuration: Surface Area and Volume of Solids (SS2 Second) — 0.200
- `numbers_and_numeration` — best 0.250, gap 0.000:
    - Revision: Number and Numeration (JSS3 Third) — 0.250
    - Development of Numbers and Numerals (JSS1 First) — 0.250
    - Directed Numbers and Algebraic Expressions (JSS2 Second) — 0.200
- `inequalities` — best 0.250, gap 0.000:
    - Simple Equations and Linear Inequalities (JSS2 Second) — 0.250
    - Simple Equations, Inequalities and Variation (SS1 First) — 0.250
    - Simple Equations (JSS1 Second) — 0.000
- `plane_geometry` — best 0.250, gap 0.000:
    - Further Coordinate Geometry (SS2 Second) — 0.250
    - Revision: Mensuration and Geometry (JSS3 Third) — 0.250
    - Introduction to Coordinate Geometry (SS1 First) — 0.250
- `statistics` — best 0.250, gap 0.000:
    - Statistics (2): Measures of Dispersion (SS2 Second) — 0.250
    - Statistics: Data Collection and Presentation (JSS1 Third) — 0.250
    - Revision: Geometry, Mensuration and Statistics (SS1 Third) — 0.250
- `trigonometry` — best 0.250, gap 0.000:
    - Trigonometry (1): Tangent of an Angle (JSS3 First) — 0.250
    - Trigonometry: Ratios, Graphs and Applications (SS2 Second) — 0.250
    - Trigonometry (2): Sine and Cosine of Angles (JSS3 Second) — 0.200
- `circles` — best 0.200, gap 0.200:
    - Mensuration: Circles, Cylinders, Cones and Spheres (SS1 Second) — 0.200
    - Compound Interest (JSS3 Second) — 0.000
    - Integers (JSS1 Second) — 0.000
- `sequence_and_series` — best 0.200, gap 0.000:
    - Sequences and Series: Geometric Progression (SS2 First) — 0.200
    - Sequences and Series: Arithmetic Progression (SS2 First) — 0.200
    - Squares and Square Roots (JSS2 First) — 0.000

## 3. Unmatched

_Sorted by best score descending, so near-misses (just under `MATCH_FLOOR`) are easiest to scan first. With SS1-SS3 now in the main pool, a slug here is genuinely absent from the curriculum titles, not merely out of scope._

| Slug | Closest curriculum title | Class | Term | Score |
| --- | --- | --- | --- | --- |
| `polynomials` | Word Problems | JSS3 | First | 0.000 |
| `logic` | Indices and Logarithms | SS1 | First | 0.000 |
| `triangles` | Factors and Multiples | JSS1 | First | 0.000 |
| `vectors` | Sets | SS1 | First | 0.000 |

## 4. Curriculum Topics With No Allowlist Slug

_JSS1-SS3 curriculum titles whose best-matching slug scores below `COVERAGE_FLOOR`. Sorted by score descending — the allowlist may be missing these topics. Closest near-misses appear first._

| Curriculum title | Class | Term | Closest slug | Score |
| --- | --- | --- | --- | --- |
| Whole Numbers: HCF, LCM and Number Patterns | JSS2 | First | `numbers_and_numeration` | 0.143 |
| WAEC/JAMB Comprehensive Revision: Geometry, Trig and Statistics | SS3 | Second | `statistics` | 0.143 |
| Factors and Multiples | JSS1 | First | `triangles` | 0.000 |
| Number Base System | JSS1 | First | `numbers_and_numeration` | 0.000 |
| Integers | JSS1 | Second | `angles` | 0.000 |
| Estimation and Approximation | JSS1 | Second | `ratio_and_proportion` | 0.000 |
| Three-Dimensional Shapes and Volume | JSS1 | Third | `numbers_and_numeration` | 0.000 |
| Squares and Square Roots | JSS2 | First | `sequence_and_series` | 0.000 |
| Approximation and Estimation | JSS2 | First | `ratio_and_proportion` | 0.000 |
| Pythagoras' Rule | JSS2 | Third | `triangles` | 0.000 |
| Geometrical Constructions | JSS2 | Third | `mensuration` | 0.000 |
| Data Presentation and Interpretation | JSS2 | Third | `ratio_and_proportion` | 0.000 |
| Word Problems | JSS3 | First | `polynomials` | 0.000 |
| Factorisation (1): Common Factors | JSS3 | First | `trigonometry` | 0.000 |
| Geometrical Constructions (Revision and Extension) | JSS3 | First | `ratio_and_proportion` | 0.000 |
| Formulae: Substitution and Change of Subject | JSS3 | First | `ratio_and_proportion` | 0.000 |
| Similarity (1): Similar Shapes and Scale Factors | JSS3 | First | `sequence_and_series` | 0.000 |
| Compound Interest | JSS3 | Second | `coordinate_geometry` | 0.000 |
| Similarity (2): Areas and Volumes of Similar Shapes | JSS3 | Second | `numbers_and_numeration` | 0.000 |
| Revision: Number and Algebra | SS1 | Third | `numbers_and_numeration` | 0.000 |
| WAEC/NECO Revision: Algebra and Number | SS2 | Third | `numbers_and_numeration` | 0.000 |
| Differentiation | SS3 | First | `fractions` | 0.000 |
| Integration | SS3 | First | `linear_equations` | 0.000 |
| Permutation and Combination | SS3 | First | `ratio_and_proportion` | 0.000 |
| WAEC/JAMB Comprehensive Revision: Number and Algebra | SS3 | Second | `numbers_and_numeration` | 0.000 |
| Calculus Revision and Applications | SS3 | Second | `ratio_and_proportion` | 0.000 |
| Mock Examinations and JAMB Preparation | SS3 | Third | `numbers_and_numeration` | 0.000 |

## 5. Class-Level Breakdown of Matches

_Where the confident and ambiguous matches land across the full JSS1-SS3 range. (Replaces the old 'Unmatched vs JSS, Checked Against SS' diagnostic, which is redundant now that SS is in the main pool.) Level = the class level of each slug's single best-matching title._

| Class level | Confident | Ambiguous | Total matched |
| --- | --- | --- | --- |
| JSS1 | 0 | 6 | 6 |
| JSS2 | 3 | 2 | 5 |
| JSS3 | 0 | 3 | 3 |
| SS1 | 5 | 1 | 6 |
| SS2 | 1 | 5 | 6 |
| SS3 | 0 | 0 | 0 |
| **All levels** | **9** | **17** | **26** |
