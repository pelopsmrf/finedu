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

/** Friendly comment for the final score. */
export function resultMessage(score: number, total: number): string {
  if (total === 0) return "";
  const share = score / total;
  if (share === 1) return "Отлично! Все ответы верные 🎉";
  if (share >= 0.5) return "Хороший результат! Загляни в пояснения к ошибкам 👍";
  return "Стоит повторить урок — в следующий раз получится лучше 💪";
}

/** Russian plural: pluralRu(5, ["вопрос", "вопроса", "вопросов"]) → "вопросов". */
export function pluralRu(n: number, forms: [string, string, string]): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return forms[0];
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return forms[1];
  return forms[2];
}
