export interface QuizQuestion {
  correct_index: number;
}

export function scoreQuiz(
  questions: QuizQuestion[],
  answers: number[]
): { score: number; total: number } {
  const score = questions.reduce((acc, q, i) => {
    return acc + (answers[i] === q.correct_index ? 1 : 0);
  }, 0);
  return { score, total: questions.length };
}
