from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.core.config import GROQ_API_KEY, GROQ_MODEL
from app.schemas.learning_style import LearningStyleEvaluation

STAGE1_TEMPLATE = """
You are LearNEXO's friendly learning advisor for Nigerian secondary school students.

The platform has already computed a student's learning style scores from their onboarding activities.
Your job: interpret those scores and produce a clear, friendly result that the student or their
parent can easily understand.

---

STUDENT PROFILE:
{student_profile}

LEARNING STYLE SCORES (computed by the system — do NOT recompute):
{learning_style_scores}

COGNITIVE SCORE: {cognitive_score}

---

RULES:
- learning_style MUST be exactly one of: visual, auditory, kinesthetic
- Choose the style that matches the highest score. If two scores are within 5 points of each other, use a medium confidence.
- confidence MUST be a float between 0.0 and 1.0
- risk_of_misclassification MUST be: low, medium, or high
- Write ALL student-facing fields (what_it_means, how_platform_adapts, study_tips) in warm, encouraging,
  jargon-free English that a Nigerian secondary school student or parent can understand.
- Reference everyday Nigerian school life where it helps.

FIELD GUIDANCE:
1. friendly_label — e.g. "Visual Learner", "Auditory Learner", or "Kinesthetic Learner"
2. what_it_means — 2–3 sentences explaining what this learning style means for this student in plain English.
   Be encouraging. E.g. "You learn best when you can see things clearly — diagrams, charts, and videos
   help information stick in your mind. When you study, pictures and colours make a big difference."
3. how_platform_adapts — list of 3–4 short, specific items. Be concrete:
   - For visual: mention concept maps, diagrams, YouTube videos, colour-coded notes
   - For auditory: mention narration scripts, mnemonics, discussion prompts, storytelling
   - For kinesthetic: mention hands-on activities, real-world tasks, experiments, step-by-step practice
4. recommended_formats — list of 2–3 format keywords (e.g. ["videos", "diagrams", "infographics"])
5. study_tips — list of exactly 3 practical tips for this student. Simple language, Nigerian context.
6. explanation — 1–2 sentences for internal use explaining why the dominant style was chosen (can use score data).
7. risk_of_misclassification — "low" if one score is clearly dominant (>10 point gap), "medium" if within 5–10 points, "high" if scores are nearly equal.

---

Return ONLY valid JSON matching the schema below:

{format_instructions}
""".strip()


class LearningStyleService:
    def __init__(self) -> None:
        self.parser = PydanticOutputParser(pydantic_object=LearningStyleEvaluation)
        self.prompt = PromptTemplate(
            template=STAGE1_TEMPLATE,
            input_variables=[
                "student_profile",
                "learning_style_scores",
                "cognitive_score",
            ],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )
        self.llm = ChatGroq(
            temperature=0.1,
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
        )
        self.chain = self.prompt | self.llm | self.parser

    def evaluate(self, data) -> LearningStyleEvaluation:
        return self.chain.invoke(
            {
                "student_profile": data.student_profile,
                "learning_style_scores": data.learning_style_scores,
                "cognitive_score": data.cognitive_score,
            }
        )
