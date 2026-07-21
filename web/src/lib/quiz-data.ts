/**
 * quiz-data.ts — Static question banks and scoring helpers for the
 * LearNEXO onboarding wizard.
 *
 * Learning-style questions → tallyStyleScores() → {visual, auditory, kinesthetic} (0–100)
 * Academic MCQ questions   → tallyTopicScores() → {weak: string[], strong: string[]}
 */

// ---------------------------------------------------------------------------
// Learning Style Quiz (VAK)
// ---------------------------------------------------------------------------

export type StyleChoice = "visual" | "auditory" | "kinesthetic";

export type StyleQuestion = {
  id: number;
  scenario: string;
  options: Record<StyleChoice, string>;
};

export const STYLE_QUESTIONS: StyleQuestion[] = [
  {
    id: 1,
    scenario: "When learning something new, you prefer to:",
    options: {
      visual: "Watch a video or see a demonstration",
      auditory: "Listen to the teacher explain it",
      kinesthetic: "Try a practice problem straight away",
    },
  },
  {
    id: 2,
    scenario: "When you need to remember directions to a place, you:",
    options: {
      visual: "Picture a map or draw one out",
      auditory: "Repeat the directions out loud to yourself",
      kinesthetic: "Just go and figure it out as you walk",
    },
  },
  {
    id: 3,
    scenario: "Your favourite way to revise for an exam is:",
    options: {
      visual: "Re-read your notes with diagrams and charts",
      auditory: "Record yourself and play it back",
      kinesthetic: "Grind through past exam questions",
    },
  },
  {
    id: 4,
    scenario: "When you are stuck on a difficult problem, you:",
    options: {
      visual: "Search for a diagram or worked example to look at",
      auditory: "Ask someone to talk you through it",
      kinesthetic: "Keep trying different approaches until one works",
    },
  },
  {
    id: 5,
    scenario: "In class, you learn best when:",
    options: {
      visual: "The board is full of clear notes and diagrams",
      auditory: "The teacher explains everything in detail",
      kinesthetic: "You do group work or hands-on activities",
    },
  },
  {
    id: 6,
    scenario: "Your preferred study material is:",
    options: {
      visual: "Textbooks with lots of pictures and charts",
      auditory: "Audio explanations or recorded lessons",
      kinesthetic: "Worksheets, exercises, and practice sets",
    },
  },
  {
    id: 7,
    scenario: "When you forget something you studied, you:",
    options: {
      visual: "Picture the page or place where you saw it",
      auditory: "Hear the words or explanation in your head",
      kinesthetic: "Try to re-do the action or write it out again",
    },
  },
  {
    id: 8,
    scenario: "During a long study session, you get bored fastest when:",
    options: {
      visual: "Reading big blocks of text with no images",
      auditory: "Listening to a lecture with nothing to look at",
      kinesthetic: "Sitting still and not doing anything active",
    },
  },
  {
    id: 9,
    scenario: "Your best note-taking style is:",
    options: {
      visual: "Mind maps, diagrams, and colour-coded notes",
      auditory: "Short key phrases you can read aloud later",
      kinesthetic: "Writing and rewriting to make it stick",
    },
  },
  {
    id: 10,
    scenario: "Your favourite revision method is:",
    options: {
      visual: "Colour-coded flashcards with diagrams",
      auditory: "Discussing topics with a study group",
      kinesthetic: "Timed past-paper practice",
    },
  },
  {
    id: 11,
    scenario: "When someone gives you feedback on your work, you'd rather they:",
    options: {
      visual: "Show you examples of what good work looks like",
      auditory: "Talk you through what to change and why",
      kinesthetic: "Let you redo it yourself and learn from doing it again",
    },
  },
  {
    id: 12,
    scenario: "Before an exam, the thing that calms your nerves most is:",
    options: {
      visual: "Skimming your notes and diagrams one more time",
      auditory: "Talking through the topics with a friend",
      kinesthetic: "Doing a few quick practice questions to warm up",
    },
  },
  {
    id: 13,
    scenario: "When a teacher introduces a new topic, you pay the most attention when they:",
    options: {
      visual: "Write key points and diagrams on the board",
      auditory: "Explain the idea step by step out loud",
      kinesthetic: "Set up an example or activity to work through",
    },
  },
  {
    id: 14,
    scenario: "If you had to explain a topic you just learned to a friend, you would:",
    options: {
      visual: "Draw it out or sketch a diagram",
      auditory: "Just talk them through it",
      kinesthetic: "Walk them through solving an example together",
    },
  },
  {
    id: 15,
    scenario: "When you're given a long reading assignment, you:",
    options: {
      visual: "Skim for headings, bold text, and images first",
      auditory: "Read it slowly, sounding it out in your head",
      kinesthetic: "Take breaks to jot notes or summarise as you go",
    },
  },
  {
    id: 16,
    scenario: "Your ideal group project role is the one where you:",
    options: {
      visual: "Design the slides or visual layout",
      auditory: "Present and explain the ideas to others",
      kinesthetic: "Build, test, or assemble the actual work",
    },
  },
  {
    id: 17,
    scenario: "When a lesson feels confusing, what helps you most is:",
    options: {
      visual: "Seeing it laid out step by step on paper",
      auditory: "Having someone explain it a different way out loud",
      kinesthetic: "Trying it yourself until it clicks",
    },
  },
  {
    id: 18,
    scenario: "The classroom setup you'd choose if you could is one with:",
    options: {
      visual: "Charts, posters, and visual aids everywhere",
      auditory: "Lots of discussion and verbal explanation",
      kinesthetic: "Room to move around and try things hands-on",
    },
  },
];

/**
 * Tally VAK quiz answers into normalised 0–100 scores.
 * answers: array of StyleChoice values (one per question, in order).
 */
export function tallyStyleScores(
  answers: StyleChoice[],
): Record<StyleChoice, number> {
  const counts: Record<StyleChoice, number> = {
    visual: 0,
    auditory: 0,
    kinesthetic: 0,
  };
  for (const a of answers) counts[a]++;
  return {
    visual: Math.round((counts.visual / STYLE_QUESTIONS.length) * 100),
    auditory: Math.round((counts.auditory / STYLE_QUESTIONS.length) * 100),
    kinesthetic: Math.round(
      (counts.kinesthetic / STYLE_QUESTIONS.length) * 100,
    ),
  };
}

/**
 * Deterministic per-question option shuffle so option position doesn't leak
 * which VAK category an answer belongs to. Seeded by a per-quiz-attempt seed
 * (generated once when the quiz mounts) combined with the question id, so
 * order is stable within one attempt but varies across retakes.
 */
function mulberry32(seed: number): () => number {
  let s = seed;
  return () => {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function shuffledStyleOrder(
  seed: number,
  questionId: number,
): StyleChoice[] {
  const rng = mulberry32(seed + questionId * 9973);
  const order: StyleChoice[] = ["visual", "auditory", "kinesthetic"];
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return order;
}

// ---------------------------------------------------------------------------
// Academic Assessment MCQs
// ---------------------------------------------------------------------------

export type MCQOption = "A" | "B" | "C" | "D";

export type MCQQuestion = {
  id: number;
  /** Topic slug this question tests — matches app/core/topics.py allowlist */
  topicSlug: string;
  question: string;
  options: Record<MCQOption, string>;
  answer: MCQOption;
};

type Subject = "Mathematics" | "English Language";
type ClassLevel = "JSS1" | "JSS2" | "JSS3" | "SS1" | "SS2" | "SS3";

// ---------------------------------------------------------------------------
// Legacy fallback banks — 10 questions across 10 topic slugs, used only when
// a subject/class-level combination has no class-scoped bank below (currently
// only English SS3, which has zero slugged curriculum topics and will never
// get class-scoped MCQs from the Gemini generation pass).
// ---------------------------------------------------------------------------
const MATHS_QUESTIONS: MCQQuestion[] = [
  {
    id: 1,
    topicSlug: "numbers_and_numeration",
    question: "Convert 110₂ (binary) to its decimal equivalent.",
    options: { A: "4", B: "6", C: "5", D: "8" },
    answer: "B",
  },
  {
    id: 2,
    topicSlug: "fractions",
    question: "Simplify: ¾ + ⅔",
    options: { A: "7/12", B: "5/6", C: "17/12", D: "1/12" },
    answer: "C",
  },
  {
    id: 3,
    topicSlug: "percentages",
    question: "What is 15% of 240?",
    options: { A: "36", B: "24", C: "30", D: "18" },
    answer: "A",
  },
  {
    id: 4,
    topicSlug: "algebraic_expressions",
    question: "Expand: 3(2x − 4)",
    options: { A: "6x − 4", B: "6x − 12", C: "6x + 12", D: "5x − 4" },
    answer: "B",
  },
  {
    id: 5,
    topicSlug: "linear_equations",
    question: "Solve for x: 2x + 7 = 15",
    options: { A: "x = 4", B: "x = 11", C: "x = 3", D: "x = 8" },
    answer: "A",
  },
  {
    id: 6,
    topicSlug: "quadratic_equations",
    question: "Which values of x satisfy x² − 5x + 6 = 0?",
    options: { A: "x = 1, 6", B: "x = 2, 3", C: "x = −2, −3", D: "x = 3, 4" },
    answer: "B",
  },
  {
    id: 7,
    topicSlug: "angles",
    question:
      "Two angles of a triangle are 55° and 70°. What is the third angle?",
    options: { A: "45°", B: "55°", C: "60°", D: "65°" },
    answer: "B",
  },
  {
    id: 8,
    topicSlug: "ratio_and_proportion",
    question:
      "Divide ₦3,600 between Amaka and Tunde in the ratio 5:4. How much does Amaka receive?",
    options: { A: "₦1,600", B: "₦2,000", C: "₦2,200", D: "₦1,800" },
    answer: "B",
  },
  {
    id: 9,
    topicSlug: "statistics",
    question: "Find the mean of: 8, 12, 15, 10, 5",
    options: { A: "9", B: "10", C: "11", D: "12" },
    answer: "B",
  },
  {
    id: 10,
    topicSlug: "mensuration",
    question:
      "What is the area of a rectangle with length 9 cm and width 5 cm?",
    options: { A: "25 cm²", B: "40 cm²", C: "45 cm²", D: "50 cm²" },
    answer: "C",
  },
];

const ENGLISH_QUESTIONS: MCQQuestion[] = [
  {
    id: 1,
    topicSlug: "tenses",
    question:
      "Choose the correct verb form: 'By the time they arrived, she _______ the food.'",
    options: {
      A: "has cooked",
      B: "had already cooked",
      C: "will have cooked",
      D: "was cooking",
    },
    answer: "B",
  },
  {
    id: 2,
    topicSlug: "prepositions",
    question: "Fill in the blank: 'She has been waiting _______ two hours.'",
    options: { A: "since", B: "for", C: "from", D: "at" },
    answer: "B",
  },
  {
    id: 3,
    topicSlug: "articles",
    question:
      "Choose the correct article: '_______ honest man is hard to find.'",
    options: { A: "A", B: "An", C: "The", D: "No article needed" },
    answer: "B",
  },
  {
    id: 4,
    topicSlug: "sentence_structure",
    question:
      "Identify the sentence type: 'Although it was raining heavily, we went to school.'",
    options: {
      A: "Simple sentence",
      B: "Compound sentence",
      C: "Complex sentence",
      D: "Compound-complex sentence",
    },
    answer: "C",
  },
  {
    id: 5,
    topicSlug: "synonyms",
    question: "Which word is closest in meaning to 'benevolent'?",
    options: { A: "Cruel", B: "Kind", C: "Brave", D: "Timid" },
    answer: "B",
  },
  {
    id: 6,
    topicSlug: "antonyms",
    question: "What is the antonym of 'verbose'?",
    options: { A: "Talkative", B: "Wordy", C: "Concise", D: "Fluent" },
    answer: "C",
  },
  {
    id: 7,
    topicSlug: "comprehension",
    question:
      "A passage states: 'The governor's policy was met with widespread criticism.' The word 'widespread' most likely means:",
    options: {
      A: "Limited to one area",
      B: "Affecting only officials",
      C: "Covering a large area or many people",
      D: "Mostly positive",
    },
    answer: "C",
  },
  {
    id: 8,
    topicSlug: "essay_writing",
    question:
      "Which of the following best describes the purpose of a thesis statement in an essay?",
    options: {
      A: "To summarise the conclusion",
      B: "To introduce a new topic in the middle",
      C: "To state the main argument the essay will prove",
      D: "To list all points without explaining them",
    },
    answer: "C",
  },
  {
    id: 9,
    topicSlug: "letter_writing",
    question:
      "In a formal letter, which of the following is the correct closing salutation?",
    options: {
      A: "Yours lovingly,",
      B: "Yours faithfully,",
      C: "With regards,",
      D: "Lots of love,",
    },
    answer: "B",
  },
  {
    id: 10,
    topicSlug: "vocabulary_in_context",
    question:
      "Read: 'The student was reticent during the debate.' What does 'reticent' mean here?",
    options: {
      A: "Very loud and confident",
      B: "Reluctant to speak",
      C: "Well-prepared",
      D: "Eager to participate",
    },
    answer: "B",
  },
];

// ---------------------------------------------------------------------------
// Class-scoped banks — generated via Gemini from the full curriculum, ~3
// questions per active topic slug (app/core/topics.py). Validated against
// the topic allowlist and manual answer-key checks before merging.
// ---------------------------------------------------------------------------

const MATHS_QUESTIONS_BY_CLASS: Record<ClassLevel, MCQQuestion[]> = {
  JSS1: [
    { id: 1, topicSlug: "fractions", question: "Convert 0.45 to a fraction in its simplest form.", options: { A: "4/5", B: "9/20", C: "9/50", D: "45/10" }, answer: "B" },
    { id: 2, topicSlug: "fractions", question: "What is the place value of the digit 7 in the decimal fraction 0.573?", options: { A: "7 tenths", B: "7 units", C: "7 hundredths", D: "7 thousandths" }, answer: "C" },
    { id: 3, topicSlug: "fractions", question: "Write 5/8 as a decimal.", options: { A: "0.58", B: "0.85", C: "5.8", D: "0.625" }, answer: "D" },
    { id: 4, topicSlug: "decimals", question: "Which of the following fractions gives a recurring decimal?", options: { A: "1/4", B: "2/5", C: "1/3", D: "7/10" }, answer: "C" },
    { id: 5, topicSlug: "decimals", question: "Express 8% as a decimal.", options: { A: "0.8", B: "0.08", C: "0.008", D: "8.0" }, answer: "B" },
    { id: 6, topicSlug: "decimals", question: "A piece of yam weighs 2.35 kg. What is the place value of 3 in this mass?", options: { A: "Tenths", B: "Hundredths", C: "Units", D: "Tens" }, answer: "A" },
    { id: 7, topicSlug: "percentages", question: "A trader in Balogun market gives a 10% discount on a pair of shoes marked at ₦5,000. How much is the discount?", options: { A: "₦100", B: "₦4,500", C: "₦500", D: "₦50" }, answer: "C" },
    { id: 8, topicSlug: "percentages", question: "In a JSS1 class of 40 students, 24 are girls. What percentage of the class are girls?", options: { A: "60%", B: "40%", C: "24%", D: "50%" }, answer: "A" },
    { id: 9, topicSlug: "percentages", question: "Convert 35% to a fraction in its lowest terms.", options: { A: "7/20", B: "3/5", C: "7/10", D: "35/100" }, answer: "A" },
    { id: 10, topicSlug: "basic_operations", question: "Simplify: 1/4 + 2/5.", options: { A: "3/9", B: "13/20", C: "3/20", D: "10/20" }, answer: "B" },
    { id: 11, topicSlug: "basic_operations", question: "Chinedu spends 1/3 of his pocket money on books and 1/4 on snacks. What fraction of his money is left?", options: { A: "1/12", B: "7/12", C: "2/7", D: "5/12" }, answer: "D" },
    { id: 12, topicSlug: "basic_operations", question: "Find the product of 2 1/2 and 1 1/5.", options: { A: "3", B: "3 1/10", C: "2 1/10", D: "5/6" }, answer: "A" },
    { id: 13, topicSlug: "algebraic_expressions", question: "Ngozi has x oranges and her brother gives her 5 more. How many oranges does she have altogether?", options: { A: "5x", B: "x - 5", C: "x + 5", D: "5 / x" }, answer: "C" },
    { id: 14, topicSlug: "algebraic_expressions", question: "Simplify the algebraic expression: 4a + 3b - 2a + 5b.", options: { A: "6a + 8b", B: "2a - 2b", C: "10ab", D: "2a + 8b" }, answer: "D" },
    { id: 15, topicSlug: "algebraic_expressions", question: "If a pen costs ₦p and a book costs ₦b, what is the total cost of 3 pens and 2 books?", options: { A: "₦(3p + 2b)", B: "₦(5pb)", C: "₦(p + b)", D: "₦(3b + 2p)" }, answer: "A" },
    { id: 16, topicSlug: "angles", question: "The sum of angles on a straight line is equal to:", options: { A: "90°", B: "180°", C: "270°", D: "360°" }, answer: "B" },
    { id: 17, topicSlug: "angles", question: "Two lines cross each other at a point. The angles directly opposite to each other are called:", options: { A: "Alternate angles", B: "Corresponding angles", C: "Adjacent angles", D: "Vertically opposite angles" }, answer: "D" },
    { id: 18, topicSlug: "angles", question: "Calculate the sum of angles around a single point.", options: { A: "180°", B: "90°", C: "360°", D: "270°" }, answer: "C" },
    { id: 19, topicSlug: "statistics", question: "A yam seller records her daily sales in tubers as: 12, 15, 10, 15, and 8. What is the mode of her sales?", options: { A: "8", B: "10", C: "12", D: "15" }, answer: "D" },
    { id: 20, topicSlug: "statistics", question: "Find the mean (average) of the following numbers: 4, 7, 5, 8, 6.", options: { A: "5", B: "6", C: "7", D: "30" }, answer: "B" },
    { id: 21, topicSlug: "statistics", question: "What is the main purpose of collecting and presenting data in statistics?", options: { A: "To make numbers look difficult", B: "To draw pictures on the board", C: "To organize information for easy understanding", D: "To confuse the teacher" }, answer: "C" },
  ],
  JSS2: [
    { id: 1, topicSlug: "ratio_and_proportion", question: "Share ₦5,000 between Chinedu and Aisha in the ratio 3:2. How much does Aisha get?", options: { A: "₦1,500", B: "₦2,000", C: "₦2,500", D: "₦3,000" }, answer: "B" },
    { id: 2, topicSlug: "ratio_and_proportion", question: "If 5 exercise books cost ₦750 at the market, what is the cost of 8 similar exercise books?", options: { A: "₦1,000", B: "₦1,150", C: "₦1,200", D: "₦1,500" }, answer: "C" },
    { id: 3, topicSlug: "ratio_and_proportion", question: "A commercial bus (danfo) travels a distance of 180 km from Lagos to Ibadan in 2 hours. What is its average speed?", options: { A: "90 km/h", B: "80 km/h", C: "100 km/h", D: "360 km/h" }, answer: "A" },
    { id: 4, topicSlug: "commercial_arithmetic", question: "Mr. Adebayo saves ₦50,000 in a bank at a simple interest rate of 4% per annum. Calculate the interest he will earn after 3 years.", options: { A: "₦2,000", B: "₦6,000", C: "₦12,000", D: "₦56,000" }, answer: "B" },
    { id: 5, topicSlug: "commercial_arithmetic", question: "Madam Nkechi bought a bag of rice for ₦40,000 and sold it for ₦48,000. What is her percentage profit?", options: { A: "8%", B: "15%", C: "16.6%", D: "20%" }, answer: "D" },
    { id: 6, topicSlug: "commercial_arithmetic", question: "A shop in Wuse market offers a 10% discount on a television set marked at ₦80,000. How much will a customer pay for the television?", options: { A: "₦70,000", B: "₦72,000", C: "₦78,000", D: "₦88,000" }, answer: "B" },
    { id: 7, topicSlug: "linear_equations", question: "What is the y-intercept of the straight line represented by the equation y = 3x - 5?", options: { A: "3", B: "-3", C: "5", D: "-5" }, answer: "D" },
    { id: 8, topicSlug: "linear_equations", question: "For the linear equation y = 2x + 1, what is the value of y when x = -2?", options: { A: "-3", B: "-1", C: "3", D: "-5" }, answer: "A" },
    { id: 9, topicSlug: "linear_equations", question: "Which of the following ordered pairs lies on the graph of the line y = x + 4?", options: { A: "(1, 4)", B: "(2, 5)", C: "(1, 5)", D: "(4, 1)" }, answer: "C" },
    { id: 10, topicSlug: "probability_jss2", question: "Emeka rolls a fair standard die once. What is the probability that he gets a number greater than 4?", options: { A: "1/2", B: "1/3", C: "2/3", D: "1/6" }, answer: "B" },
    { id: 11, topicSlug: "probability_jss2", question: "A bag contains 4 red balls, 5 blue balls, and 1 yellow ball. If a ball is picked at random, what is the probability of picking a blue ball?", options: { A: "1/10", B: "1/5", C: "1/2", D: "5/9" }, answer: "C" },
    { id: 12, topicSlug: "probability_jss2", question: "Which of the following numbers represents an event that is impossible to happen on the probability scale?", options: { A: "0", B: "0.5", C: "1", D: "-1" }, answer: "A" },
  ],
  JSS3: [
    { id: 1, topicSlug: "numbers_and_numeration", question: "Chinedu invests ₦50,000 in a bank that pays compound interest at a rate of 10% per annum. Calculate the total amount in his account after 2 years.", options: { A: "₦60,000", B: "₦60,500", C: "₦55,000", D: "₦65,000" }, answer: "B" },
    { id: 2, topicSlug: "numbers_and_numeration", question: "Express the number 0.00456 in standard form.", options: { A: "4.56 × 10⁻³", B: "4.56 × 10³", C: "45.6 × 10⁻⁴", D: "0.456 × 10⁻²" }, answer: "A" },
    { id: 3, topicSlug: "numbers_and_numeration", question: "A trader shares a profit of ₦12,000 between his two apprentices, Tola and Musa, in the ratio 3:5. How much does Musa receive?", options: { A: "₦3,000", B: "₦4,500", C: "₦6,000", D: "₦7,500" }, answer: "D" },
    { id: 4, topicSlug: "mensuration", question: "A rectangular water tank in a school compound has a length of 5 m, width of 4 m, and height of 3 m. What is the volume of the tank?", options: { A: "60 m³", B: "47 m³", C: "12 m³", D: "20 m³" }, answer: "A" },
    { id: 5, topicSlug: "mensuration", question: "Calculate the area of a trapezium with parallel sides 8 cm and 12 cm, and a perpendicular height of 5 cm.", options: { A: "100 cm²", B: "25 cm²", C: "50 cm²", D: "200 cm²" }, answer: "C" },
    { id: 6, topicSlug: "mensuration", question: "A circular garden in Abuja has a radius of 14 m. Find the perimeter (circumference) of the garden. (Take π = 22/7)", options: { A: "44 m", B: "88 m", C: "176 m", D: "616 m" }, answer: "B" },
    { id: 7, topicSlug: "plane_geometry", question: "What is the sum of the interior angles of a regular hexagon (a 6-sided polygon)?", options: { A: "360°", B: "540°", C: "720°", D: "900°" }, answer: "C" },
    { id: 8, topicSlug: "plane_geometry", question: "A rectangular map of Lagos has a scale of 1:1000. If a road on the map is 5 cm long, what is the actual length of the road in metres?", options: { A: "50 m", B: "500 m", C: "5 m", D: "5000 m" }, answer: "A" },
    { id: 9, topicSlug: "plane_geometry", question: "In a right-angled triangle, if the opposite side to angle θ is 3 cm and the adjacent side is 4 cm, what is the value of tan θ?", options: { A: "3/5", B: "4/5", C: "4/3", D: "3/4" }, answer: "D" },
  ],
  SS1: [
    { id: 1, topicSlug: "sets", question: "In a class of 40 students, 25 study Economics and 20 study Government. If 8 students study neither subject, how many study both?", options: { A: "5", B: "13", C: "15", D: "18" }, answer: "B" },
    { id: 2, topicSlug: "sets", question: "Which of the following describes the set of elements in the universal set that are NOT in a given set A?", options: { A: "Union of A", B: "Intersection of A", C: "Complement of A", D: "Subset of A" }, answer: "C" },
    { id: 3, topicSlug: "sets", question: "If A = {2, 4, 6, 8} and B = {1, 2, 3, 4}, find the intersection of sets A and B.", options: { A: "{2, 4}", B: "{1, 2, 3, 4, 6, 8}", C: "{6, 8}", D: "{1, 3}" }, answer: "A" },
    { id: 4, topicSlug: "indices", question: "Simplify 8^(2/3).", options: { A: "2", B: "4", C: "16", D: "32" }, answer: "B" },
    { id: 5, topicSlug: "indices", question: "Simplify the expression: (x^5 * x^3) / x^4", options: { A: "x^2", B: "x^3", C: "x^4", D: "x^8" }, answer: "C" },
    { id: 6, topicSlug: "indices", question: "If 3^(x - 1) = 27, find the value of x.", options: { A: "4", B: "3", C: "2", D: "5" }, answer: "A" },
    { id: 7, topicSlug: "logarithms", question: "Evaluate log10(1000).", options: { A: "1", B: "2", C: "3", D: "10" }, answer: "C" },
    { id: 8, topicSlug: "logarithms", question: "According to the laws of logarithms, express log(a) + log(b) - log(c) as a single logarithm.", options: { A: "log(ab/c)", B: "log(a+b-c)", C: "log(a/bc)", D: "log(c/ab)" }, answer: "A" },
    { id: 9, topicSlug: "logarithms", question: "Given that log10(2) = 0.3010 and log10(3) = 0.4771, find the value of log10(6).", options: { A: "0.1761", B: "1.4313", C: "0.8871", D: "0.7781" }, answer: "D" },
    { id: 10, topicSlug: "inequalities", question: "Solve the linear inequality: 3x - 5 < 5x + 7", options: { A: "x < -6", B: "x > -6", C: "x < 6", D: "x > 6" }, answer: "B" },
    { id: 11, topicSlug: "inequalities", question: "If y varies directly as x, and y = 15 when x = 5, find the value of y when x = 8.", options: { A: "24", B: "18", C: "30", D: "40" }, answer: "A" },
    { id: 12, topicSlug: "inequalities", question: "P varies inversely as Q. When P = 10, Q = 2. Find Q when P = 4.", options: { A: "8", B: "2.5", C: "5", D: "10" }, answer: "C" },
    { id: 13, topicSlug: "coordinate_geometry_ss1", question: "Find the distance between the points P(2, 3) and Q(5, 7) on the Cartesian plane.", options: { A: "3", B: "4", C: "5", D: "25" }, answer: "C" },
    { id: 14, topicSlug: "coordinate_geometry_ss1", question: "What is the gradient (slope) of the straight line passing through the points (1, 2) and (3, 6)?", options: { A: "1/2", B: "2", C: "-2", D: "4" }, answer: "B" },
    { id: 15, topicSlug: "coordinate_geometry_ss1", question: "Find the coordinates of the midpoint of the line segment joining points A(4, -2) and B(8, 6).", options: { A: "(2, 4)", B: "(4, 4)", C: "(12, 4)", D: "(6, 2)" }, answer: "D" },
    { id: 16, topicSlug: "quadratic_equations", question: "Solve for x in the quadratic equation x^2 - 5x + 6 = 0.", options: { A: "x = -2 or -3", B: "x = 2 or 3", C: "x = -2 or 3", D: "x = 2 or -3" }, answer: "B" },
    { id: 17, topicSlug: "quadratic_equations", question: "The product of two consecutive positive integers is 42. If the smaller integer is x, which of the following quadratic equations represents this statement?", options: { A: "x^2 - x + 42 = 0", B: "x^2 + x - 42 = 0", C: "2x + 1 = 42", D: "x^2 + 2x = 42" }, answer: "B" },
    { id: 18, topicSlug: "quadratic_equations", question: "Which of the following is a standard method for solving a quadratic equation?", options: { A: "Completing the square", B: "Elimination method", C: "Direct variation", D: "Matrix inversion" }, answer: "A" },
    { id: 19, topicSlug: "simultaneous_equations", question: "Solve the simultaneous equations: 2x + y = 7 and x - y = 2.", options: { A: "x = 2, y = 3", B: "x = 3, y = 1", C: "x = 1, y = 3", D: "x = 4, y = -1" }, answer: "B" },
    { id: 20, topicSlug: "simultaneous_equations", question: "A pure water seller sold 5 bags of sachet water and 2 bottles of table water for ₦1,200. The next day, she sold 3 bags of sachet water and 4 bottles of table water for ₦1,000. Let s be the price of a bag of sachet water and b be the price of a bottle of table water. Which system of equations models this?", options: { A: "5s + 2b = 1200 and 3s + 4b = 1000", B: "2s + 5b = 1200 and 4s + 3b = 1000", C: "5s + 3s = 1200 and 2b + 4b = 1000", D: "7sb = 1200 and 7sb = 1000" }, answer: "A" },
    { id: 21, topicSlug: "simultaneous_equations", question: "When solving a system of equations containing one linear equation and one quadratic equation, which algebraic method is most commonly applied?", options: { A: "Elimination method", B: "Graphical intersection only", C: "Substitution method", D: "Completing the square" }, answer: "C" },
    { id: 22, topicSlug: "circles", question: "Calculate the area of a sector of a circle with radius 7 cm if the angle subtended at the centre is 90 degrees. (Take π = 22/7)", options: { A: "11.0 cm²", B: "38.5 cm²", C: "77.0 cm²", D: "154.0 cm²" }, answer: "B" },
    { id: 23, topicSlug: "circles", question: "A cylindrical water storage tank in a Nigerian school has a base radius of 2 m and a height of 5 m. Find its volume. (Leave your answer in terms of π)", options: { A: "10π m³", B: "14π m³", C: "20π m³", D: "40π m³" }, answer: "C" },
    { id: 24, topicSlug: "circles", question: "Which of the following formulas correctly represents the surface area of a sphere of radius r?", options: { A: "(4/3)πr³", B: "πr²", C: "2πrh", D: "4πr²" }, answer: "D" },
  ],
  SS2: [
    { id: 1, topicSlug: "surds", question: "Simplify the expression: √72 + √32 - √50", options: { A: "3√2", B: "4√2", C: "5√2", D: "6√2" }, answer: "C" },
    { id: 2, topicSlug: "surds", question: "Rationalise the denominator of 2 / (3 - √5)", options: { A: "(3 + √5) / 2", B: "(3 - √5) / 2", C: "3 + √5", D: "2(3 + √5)" }, answer: "A" },
    { id: 3, topicSlug: "surds", question: "Solve for x in the exponential equation: 2^(3x - 1) = 32", options: { A: "1", B: "2", C: "3", D: "5" }, answer: "B" },
    { id: 4, topicSlug: "sequence_arithmetic", question: "The 4th term of an Arithmetic Progression is 13 and the 10th term is 31. What is the common difference?", options: { A: "2", B: "3", C: "4", D: "5" }, answer: "B" },
    { id: 5, topicSlug: "sequence_arithmetic", question: "Find the sum of the first 10 terms of the Arithmetic Progression: 2, 7, 12, 17, ...", options: { A: "225", B: "235", C: "245", D: "255" }, answer: "C" },
    { id: 6, topicSlug: "sequence_arithmetic", question: "Emeka saves ₦500 in the first week, ₦700 in the second week, and ₦900 in the third week, following an arithmetic progression. How much will he save in the 12th week?", options: { A: "₦2,500", B: "₦2,700", C: "₦2,900", D: "₦3,100" }, answer: "B" },
    { id: 7, topicSlug: "sequence_geometric", question: "Find the 6th term of the geometric progression: 3, -6, 12, -24, ...", options: { A: "96", B: "48", C: "-48", D: "-96" }, answer: "D" },
    { id: 8, topicSlug: "sequence_geometric", question: "Calculate the sum to infinity of the geometric progression: 18, 6, 2, ...", options: { A: "24", B: "27", C: "36", D: "54" }, answer: "B" },
    { id: 9, topicSlug: "sequence_geometric", question: "The population of a village in Kano grows at a rate of 5% every year. If the current population is 20,000, what will be the population after 2 years?", options: { A: "21,000", B: "22,000", C: "22,050", D: "25,000" }, answer: "C" },
    { id: 10, topicSlug: "matrices", question: "If matrix A = [[2, 1], [0, 3]] and matrix B = [[1, -1], [2, 0]], find the product AB.", options: { A: "[[4, -2], [6, 0]]", B: "[[3, 0], [2, 3]]", C: "[[4, 2], [6, 0]]", D: "[[-2, 4], [0, 6]]" }, answer: "A" },
    { id: 11, topicSlug: "matrices", question: "Find the determinant of the matrix P = [[5, 2], [4, 3]].", options: { A: "7", B: "15", C: "8", D: "23" }, answer: "A" },
    { id: 12, topicSlug: "matrices", question: "Which of the following represents the inverse of the matrix [[3, 2], [7, 5]]?", options: { A: "[[5, 2], [7, 3]]", B: "[[3, -2], [-7, 5]]", C: "[[-5, 2], [7, -3]]", D: "[[5, -2], [-7, 3]]" }, answer: "D" },
    { id: 13, topicSlug: "trigonometry", question: "If sin x = 3/5 and x is an acute angle, find the value of cos x + tan x.", options: { A: "11/20", B: "23/20", C: "31/20", D: "37/20" }, answer: "C" },
    { id: 14, topicSlug: "trigonometry", question: "In triangle ABC, side AB = 5 cm, side BC = 7 cm, and angle ABC = 60 degrees. Find the length of side AC.", options: { A: "√39 cm", B: "√74 cm", C: "√109 cm", D: "8 cm" }, answer: "A" },
    { id: 15, topicSlug: "trigonometry", question: "A trader in Lagos travels 10 km due North from her shop, then 10 km due East to buy goods. What is her bearing from the shop?", options: { A: "030 degrees", B: "045 degrees", C: "060 degrees", D: "090 degrees" }, answer: "B" },
    { id: 16, topicSlug: "coordinate_geometry_ss2", question: "Calculate the distance between the points A(-2, 3) and B(4, 11) on a Cartesian plane.", options: { A: "8 units", B: "9 units", C: "10 units", D: "12 units" }, answer: "C" },
    { id: 17, topicSlug: "coordinate_geometry_ss2", question: "Find the gradient of a line that is perpendicular to the line with equation 3y + 2x = 6.", options: { A: "-2/3", B: "-3/2", C: "2/3", D: "3/2" }, answer: "D" },
    { id: 18, topicSlug: "coordinate_geometry_ss2", question: "Find the equation of the straight line passing through the point (2, -1) with a gradient of 3.", options: { A: "y = 3x - 7", B: "y = 3x - 1", C: "y = 3x + 5", D: "y = -3x + 5" }, answer: "A" },
  ],
  SS3: [
    { id: 1, topicSlug: "probability_ss3", question: "A box contains 4 red balls, 5 green balls, and 6 yellow balls. If a ball is picked at random, what is the probability that it is either green or yellow?", options: { A: "1/3", B: "2/5", C: "11/15", D: "2/3" }, answer: "C" },
    { id: 2, topicSlug: "probability_ss3", question: "Two students, Chidi and Ngozi, are taking a mathematics examination. The probability that Chidi passes is 2/3 and the probability that Ngozi passes is 3/4. What is the probability that both of them pass the examination?", options: { A: "1/12", B: "1/4", C: "5/12", D: "1/2" }, answer: "D" },
    { id: 3, topicSlug: "probability_ss3", question: "A bag contains 7 white and 3 black identical balls. If two balls are drawn one after the other without replacement, what is the probability that both balls are white?", options: { A: "7/15", B: "21/50", C: "49/100", D: "1/15" }, answer: "A" },
  ],
};

// English SS3 has zero slugged topics in the curriculum (see app/core/topics.py)
// and is intentionally absent here — getQuestions() falls back to the legacy
// ENGLISH_QUESTIONS bank for that combination.
const ENGLISH_QUESTIONS_BY_CLASS: Partial<Record<ClassLevel, MCQQuestion[]>> = {
  JSS1: [
    { id: 1, topicSlug: "prepositions", question: "Which word in the following sentence is a preposition? 'Chinedu hid the keys under the mat.'", options: { A: "Chinedu", B: "under", C: "keys", D: "hid" }, answer: "B" },
    { id: 2, topicSlug: "prepositions", question: "Choose the correct preposition to complete this sentence: 'The new English teacher from Abuja arrived ___ Monday morning.'", options: { A: "in", B: "at", C: "on", D: "by" }, answer: "C" },
    { id: 3, topicSlug: "prepositions", question: "What is the primary function of a preposition in an English sentence?", options: { A: "To show the relationship between a noun or pronoun and other words in the sentence", B: "To describe an action or state of being", C: "To replace a noun to avoid repetition", D: "To join two independent clauses together" }, answer: "A" },
    { id: 4, topicSlug: "vowel_sounds", question: "Which of the following words contains the short vowel sound /ʌ/?", options: { A: "Book", B: "Cup", C: "Shoe", D: "Car" }, answer: "B" },
    { id: 5, topicSlug: "vowel_sounds", question: "Identify the word that is pronounced with the long vowel sound /u:/.", options: { A: "Look", B: "Put", C: "Food", D: "Cut" }, answer: "C" },
    { id: 6, topicSlug: "vowel_sounds", question: "Which of these word pairs demonstrates the contrasting vowel sounds /a:/ and /æ/?", options: { A: "Part and Pat", B: "Sit and Seat", C: "Cot and Caught", D: "Pull and Pool" }, answer: "A" },
    { id: 7, topicSlug: "letter_writing", question: "Which of the following is a required feature of a formal letter that is NOT included in an informal letter?", options: { A: "The sender's address", B: "A closing remark", C: "The receiver's address", D: "The date of writing" }, answer: "C" },
    { id: 8, topicSlug: "letter_writing", question: "If you are writing a letter to the Chairman of your Local Government Area complaining about bad roads, which of these is the most appropriate closing?", options: { A: "Yours affectionately,", B: "Yours faithfully,", C: "Best wishes,", D: "Your friend," }, answer: "B" },
    { id: 9, topicSlug: "letter_writing", question: "What is the main purpose of using the opening salutation 'Dear Amina,' in a letter?", options: { A: "To show respect to a government official", B: "To greet a friend or relative in an informal letter", C: "To conclude a formal business letter", D: "To introduce the main topic of an argumentative essay" }, answer: "B" },
    { id: 10, topicSlug: "consonant_sounds", question: "Which of the following words begins with a consonant cluster?", options: { A: "Animal", B: "Thrive", C: "Book", D: "Apple" }, answer: "B" },
    { id: 11, topicSlug: "consonant_sounds", question: "How many consonant sounds are grouped together to form the consonant cluster at the end of the word 'asks'?", options: { A: "One", B: "Two", C: "Three", D: "Four" }, answer: "C" },
    { id: 12, topicSlug: "consonant_sounds", question: "Which of these words does NOT contain a consonant cluster?", options: { A: "School", B: "Respect", C: "Pen", D: "Thrive" }, answer: "C" },
    { id: 13, topicSlug: "comprehension", question: "In a reading passage, what is the main function of a topic sentence?", options: { A: "To provide a summary of the entire textbook", B: "To state the central idea of a paragraph", C: "To give minor examples and supporting details", D: "To test the reader's spelling vocabulary" }, answer: "B" },
    { id: 14, topicSlug: "comprehension", question: "When you are asked to write a summary of a passage, which of the following is the best approach?", options: { A: "Copy the exact sentences word-for-word from the original passage", B: "Include all the minor details, jokes, and examples mentioned", C: "State the main points clearly using your own words", D: "Add your own personal opinions and new ideas to the story" }, answer: "C" },
    { id: 15, topicSlug: "comprehension", question: "Which important reading skill involves telling the difference between what is absolutely true and what someone simply believes?", options: { A: "Skimming for character names", B: "Identifying topic sentences", C: "Spelling difficult words correctly", D: "Analysing facts and opinions" }, answer: "D" },
  ],
  JSS2: [
    { id: 1, topicSlug: "tenses", question: "Choose the option that correctly completes the sentence: By the time Chike arrived at the park, the bus _______.", options: { A: "has left", B: "had left", C: "is leaving", D: "leaves" }, answer: "B" },
    { id: 2, topicSlug: "tenses", question: "Identify the tense used in this sentence: Listen! The school choir is singing the national anthem.", options: { A: "Simple Present", B: "Present Continuous", C: "Past Continuous", D: "Present Perfect" }, answer: "B" },
    { id: 3, topicSlug: "tenses", question: "Change the following direct speech into indirect speech: Ade said, 'I am traveling to Kano.'", options: { A: "Ade said that he is traveling to Kano.", B: "Ade said that he will travel to Kano.", C: "Ade said that he was traveling to Kano.", D: "Ade said that he travels to Kano." }, answer: "C" },
    { id: 4, topicSlug: "narrative_writing", question: "Which of the following elements is most important when writing a narrative essay about your last holiday?", options: { A: "Explaining the rules of a game", B: "Telling the events in a clear chronological order", C: "Arguing against traveling during the holidays", D: "Listing population facts about a state" }, answer: "B" },
    { id: 5, topicSlug: "narrative_writing", question: "In a narrative essay titled 'What I Do Every Day', which tense is the most appropriate to use?", options: { A: "Simple present tense", B: "Past perfect tense", C: "Future continuous tense", D: "Simple past tense" }, answer: "A" },
    { id: 6, topicSlug: "narrative_writing", question: "Which of these introductory sentences is most suitable for a narrative essay?", options: { A: "Lagos is the commercial capital of Nigeria.", B: "To bake a cake, you need flour, butter, and sugar.", C: "It was a bright Saturday morning when my uncle arrived unexpectedly from Abuja.", D: "In this essay, I will define what a school is." }, answer: "C" },
    { id: 7, topicSlug: "descriptive_writing", question: "When writing a descriptive essay about your favourite teacher, which of these details should you primarily include?", options: { A: "Details about her physical appearance and unique teaching style", B: "A fictional story about a completely different school", C: "The step-by-step process of solving an algebra equation", D: "A strong argument about why teachers should be paid more" }, answer: "A" },
    { id: 8, topicSlug: "descriptive_writing", question: "To make a descriptive essay about a local festival lively and engaging, the writer should mostly use:", options: { A: "Scientific formulas and equations", B: "Sensory words and vivid adjectives", C: "Statistical data about agriculture", D: "Persuasive arguments against celebrating festivals" }, answer: "B" },
    { id: 9, topicSlug: "descriptive_writing", question: "In the pre-writing stage of a descriptive essay about a place of interest, what is the best action to take?", options: { A: "Submit the final draft immediately", B: "Check for punctuation errors", C: "Brainstorm and outline your ideas about the place", D: "Read the essay aloud to the class" }, answer: "C" },
    { id: 10, topicSlug: "stress_jss2", question: "Identify the correct stress placement for the word 'export' when it is used as a verb.", options: { A: "EX-port", B: "ex-PORT", C: "ex-port-ER", D: "EX-ports" }, answer: "B" },
    { id: 11, topicSlug: "stress_jss2", question: "Which of the following shows the correct stress placement for the word 'present' when it functions as a noun (meaning a gift)?", options: { A: "PRE-sent", B: "pre-SENT", C: "pre-SENT-ing", D: "pre-sent-ED" }, answer: "A" },
    { id: 12, topicSlug: "stress_jss2", question: "Choose the correct stress pattern for the noun 'refuse' (meaning waste or rubbish).", options: { A: "re-FUSE", B: "re-FUS-ing", C: "re-FUSED", D: "RE-fuse" }, answer: "D" },
    { id: 13, topicSlug: "intonation_jss2", question: "Which intonation pattern is normally used when asking a Wh- question like 'Where is my bag?'", options: { A: "Rising intonation", B: "Falling intonation", C: "Fall-rise intonation", D: "Rise-fall intonation" }, answer: "B" },
    { id: 14, topicSlug: "intonation_jss2", question: "Which of the following sentences should be spoken with a rising intonation?", options: { A: "Give me the book immediately.", B: "My name is Ngozi.", C: "Are you going to the market today?", D: "The boy is sleeping in the room." }, answer: "C" },
    { id: 15, topicSlug: "intonation_jss2", question: "A falling intonation is typically used for all the following sentence types EXCEPT:", options: { A: "Commands", B: "Statements", C: "Wh- questions", D: "Yes/No questions" }, answer: "D" },
    { id: 16, topicSlug: "synonyms", question: "Choose the word nearest in meaning to the underlined word: The principal praised the students for their 'brilliant' performance.", options: { A: "dull", B: "excellent", C: "poor", D: "lazy" }, answer: "B" },
    { id: 17, topicSlug: "synonyms", question: "In the sentence 'The wealthy businessman donated a new building to the school', a synonym for 'wealthy' is:", options: { A: "affluent", B: "generous", C: "famous", D: "poor" }, answer: "A" },
    { id: 18, topicSlug: "synonyms", question: "Identify the synonym for the word 'conceal' in this context: Tunde tried to conceal the broken plate from his mother.", options: { A: "reveal", B: "display", C: "hide", D: "repair" }, answer: "C" },
    { id: 19, topicSlug: "antonyms", question: "Choose the word opposite in meaning to the underlined word: Amina is known to be very 'industrious'.", options: { A: "hardworking", B: "lazy", C: "smart", D: "tired" }, answer: "B" },
    { id: 20, topicSlug: "antonyms", question: "What is the antonym of the word 'ancient' as used in the sentence 'We visited an ancient monument in Kano'?", options: { A: "old", B: "historical", C: "modern", D: "big" }, answer: "C" },
    { id: 21, topicSlug: "antonyms", question: "Identify the antonym of the word 'frequently' in the sentence: 'It frequently rains in Port Harcourt during July.'", options: { A: "often", B: "constantly", C: "always", D: "seldom" }, answer: "D" },
  ],
  JSS3: [
    { id: 1, topicSlug: "sentence_structure", question: "Which of the following is an example of a compound sentence?", options: { A: "Chidi and Amaka walked to the market to buy provisions.", B: "Tunde bought a new textbook, but he lost it on his way home.", C: "Although it rained heavily, we still played football.", D: "The principal spoke to the students during the morning assembly." }, answer: "B" },
    { id: 2, topicSlug: "sentence_structure", question: "Choose the correct relative pronoun to complete this sentence: 'The man _____ stole the bicycle has been caught by the police.'", options: { A: "which", B: "whom", C: "who", D: "whose" }, answer: "C" },
    { id: 3, topicSlug: "sentence_structure", question: "Select the correct reflexive pronoun to complete the sentence: 'Ngozi bought _____ a beautiful dress for the school prize-giving day.'", options: { A: "himself", B: "herself", C: "themselves", D: "itself" }, answer: "B" },
    { id: 4, topicSlug: "essay_writing", question: "Which of the following is an essential feature of an informal letter to a friend?", options: { A: "The recipient's address at the top left corner.", B: "A formal title or heading for the letter.", C: "The writer's address and the date at the top right corner.", D: "The complimentary close 'Yours faithfully,'" }, answer: "C" },
    { id: 5, topicSlug: "essay_writing", question: "You are asked to write a composition on the topic 'Teachers are better than farmers in society.' What type of essay is this?", options: { A: "Expository essay", B: "Narrative essay", C: "Descriptive essay", D: "Argumentative essay" }, answer: "D" },
    { id: 6, topicSlug: "essay_writing", question: "An expository essay on 'The Effects of Youth Unemployment' should primarily aim to do what?", options: { A: "Tell an interesting story about a youth who could not find a job.", B: "Explain the causes, consequences, and possible solutions to the issue.", C: "Argue that the government is solely to blame for the lack of jobs.", D: "Describe the physical appearance of an unemployed graduate." }, answer: "B" },
  ],
  SS1: [
    { id: 1, topicSlug: "stress_ss1", question: "Identify the word with the correct stress pattern. The stressed syllable is written in capital letters: 'education'.", options: { A: "E-du-ca-tion", B: "e-DU-ca-tion", C: "e-du-CA-tion", D: "e-du-ca-TION" }, answer: "C" },
    { id: 2, topicSlug: "stress_ss1", question: "Which of the following words changes its meaning depending on whether the first or second syllable is stressed?", options: { A: "Beautiful", B: "Record", C: "Happen", D: "Teacher" }, answer: "B" },
    { id: 3, topicSlug: "stress_ss1", question: "Read the sentence and determine the implication of the stress: 'Bolu bought a RED car.' The emphasis on the word 'RED' implies that:", options: { A: "Bolu did not buy a blue car.", B: "Chuka did not buy the car.", C: "Bolu did not steal the car.", D: "Bolu did not buy a bicycle." }, answer: "A" },
    { id: 4, topicSlug: "intonation_ss1", question: "Which of the following sentence types is typically spoken with a falling intonation?", options: { A: "A polar (Yes/No) question", B: "A Wh- question", C: "A request for repetition", D: "An expression of doubt" }, answer: "B" },
    { id: 5, topicSlug: "intonation_ss1", question: "In which of these sentences would you naturally use a rising intonation at the end?", options: { A: "Olu is going to the market.", B: "Sit down right now!", C: "Are you attending the festival tomorrow?", D: "I bought yam, beans and rice." }, answer: "C" },
    { id: 6, topicSlug: "intonation_ss1", question: "A fall-rise intonation pattern is most appropriately used to express:", options: { A: "Absolute certainty", B: "A direct command", C: "A factual statement", D: "Partial agreement or hesitation" }, answer: "D" },
    { id: 7, topicSlug: "vocabulary_in_context", question: "Choose the word nearest in meaning to the underlined word: The principal's decision to expel the students was 'irrevocable'.", options: { A: "Unfair", B: "Reversible", C: "Temporary", D: "Final" }, answer: "D" },
    { id: 8, topicSlug: "vocabulary_in_context", question: "Choose the word opposite in meaning to the underlined word: While Amina is known for being 'frugal', her brother is quite ________.", options: { A: "Extravagant", B: "Generous", C: "Careful", D: "Miserly" }, answer: "A" },
    { id: 9, topicSlug: "vocabulary_in_context", question: "Which of the following terms belongs to the register of commerce and banking?", options: { A: "Stethoscope", B: "Overdraft", C: "Plaintiff", D: "Syllabus" }, answer: "B" },
    { id: 10, topicSlug: "reading_skills", question: "If a writer describes a character's actions with words like 'foolish', 'hasty', and 'disastrous', what is the writer's tone towards the character?", options: { A: "Admiring", B: "Objective", C: "Critical", D: "Sympathetic" }, answer: "C" },
    { id: 11, topicSlug: "reading_skills", question: "What is the best strategy for identifying the main idea of a paragraph in a comprehension passage?", options: { A: "Looking for the longest word in the paragraph.", B: "Reading the topic sentence, which is usually at the beginning or end.", C: "Counting the number of punctuation marks.", D: "Memorizing every minor detail mentioned in the text." }, answer: "B" },
    { id: 12, topicSlug: "reading_skills", question: "An article detailing the step-by-step process of refining crude oil in Port Harcourt is most likely written to:", options: { A: "Inform the reader about the refining process.", B: "Persuade the reader to buy petrol.", C: "Entertain the reader with a story.", D: "Criticize the oil workers." }, answer: "A" },
    { id: 13, topicSlug: "summary", question: "According to WAEC and NECO guidelines, which of the following is a strict rule when writing a summary?", options: { A: "You must write in your own words as much as possible.", B: "You must copy the exact sentences from the passage.", C: "You should include your personal opinions on the topic.", D: "You must provide a long explanation for each point." }, answer: "A" },
    { id: 14, topicSlug: "summary", question: "How are summary answers expected to be presented in the exam?", options: { A: "As a list of phrases without verbs.", B: "As a single, unbroken paragraph containing all points.", C: "As bulleted single words.", D: "In complete sentences." }, answer: "D" },
    { id: 15, topicSlug: "summary", question: "In summary writing, including irrelevant examples and illustrations from the passage will result in:", options: { A: "Extra marks for thoroughness.", B: "A deduction of marks or loss of the point.", C: "A better understanding by the examiner.", D: "An automatic failure of the entire English paper." }, answer: "B" },
  ],
  SS2: [
    { id: 1, topicSlug: "idioms", question: "When the principal discovered the students were leaving the hostel at night, he hit the roof. The idiom 'hit the roof' means that he...", options: { A: "became extremely angry.", B: "decided to repair the building.", C: "punished them immediately.", D: "climbed up to catch them." }, answer: "A" },
    { id: 2, topicSlug: "idioms", question: "Read the following sentence: 'The doctor's prognosis was that Tunde would fully recover from malaria within a week.' In the medical register, what does 'prognosis' refer to?", options: { A: "A detailed list of the drugs prescribed.", B: "The likely course and outcome of a disease.", C: "The final hospital bill given to a patient.", D: "A surgical tool used in operations." }, answer: "B" },
    { id: 3, topicSlug: "idioms", question: "During the debate competition, the opposing team tried to pull the wool over our eyes regarding the school's budget. This means they tried to...", options: { A: "make us feel comfortable.", B: "present a clear argument.", C: "deceive or mislead us.", D: "surprise us with facts." }, answer: "C" },
    { id: 4, topicSlug: "articles", question: "When writing a formal report on a fire outbreak in the chemistry laboratory for the school principal, which of the following is most essential?", options: { A: "A catchy, exaggerated headline to grab attention.", B: "Emotional language to show sympathy for the students.", C: "Objective language, factual details, and a clear layout.", D: "A long fictional narrative of how the fire might have started." }, answer: "C" },
    { id: 5, topicSlug: "articles", question: "A feature article intended for publication in a popular Nigerian youth magazine is expected to have...", options: { A: "official minutes of a previous meeting.", B: "a highly academic and rigid sentence structure.", C: "inside addresses like a formal business letter.", D: "an engaging headline and a captivating hook." }, answer: "D" },
    { id: 6, topicSlug: "articles", question: "Which of the following is the standard way to record the decisions made during a meeting of the school's press club?", options: { A: "Writing long verbatim speeches of every member.", B: "Listing concise action points and resolutions in the minutes.", C: "Creating a subjective review of the event.", D: "Drafting an argumentative essay defending the decisions." }, answer: "B" },
  ],
  // SS3 intentionally omitted — zero slugged topics, falls back to ENGLISH_QUESTIONS.
};

// ---------------------------------------------------------------------------
// Scoring helpers
// ---------------------------------------------------------------------------

/**
 * Return the question bank for a subject/class-level pair, preferring the
 * class-scoped curriculum bank and falling back to the legacy flat bank when
 * no class-scoped content exists yet (currently only English SS3).
 */
export function getQuestions(
  subject: Subject,
  classLevel: ClassLevel,
): MCQQuestion[] {
  if (subject === "Mathematics") {
    return MATHS_QUESTIONS_BY_CLASS[classLevel] ?? MATHS_QUESTIONS;
  }
  return ENGLISH_QUESTIONS_BY_CLASS[classLevel] ?? ENGLISH_QUESTIONS;
}

/**
 * Score a completed MCQ assessment and return weak / strong topic slug lists.
 *
 * Each topic slug gets ~3 questions in the class-scoped banks (1 in the
 * legacy fallback banks):
 *   rate ≥ 0.8 → strong
 *   rate ≤ 0.5 → weak
 */
export function tallyTopicScores(
  answers: Record<number, MCQOption>,
  subject: Subject,
  classLevel: ClassLevel,
): { weak: string[]; strong: string[] } {
  const questions = getQuestions(subject, classLevel);
  const slugStats: Record<string, { correct: number; total: number }> = {};

  for (const q of questions) {
    if (!slugStats[q.topicSlug])
      slugStats[q.topicSlug] = { correct: 0, total: 0 };
    slugStats[q.topicSlug].total++;
    if (answers[q.id] === q.answer) slugStats[q.topicSlug].correct++;
  }

  const weak: string[] = [];
  const strong: string[] = [];
  for (const [slug, { correct, total }] of Object.entries(slugStats)) {
    const rate = correct / total;
    if (rate <= 0.5) weak.push(slug);
    else if (rate >= 0.8) strong.push(slug);
  }
  return { weak, strong };
}
