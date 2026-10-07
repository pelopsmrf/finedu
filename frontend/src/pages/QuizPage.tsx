import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getQuiz, Quiz, submitProgress } from "../api";
import { scoreQuiz } from "../quizLogic";

export default function QuizPage() {
  const { quizId } = useParams();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [result, setResult] = useState<{ score: number; total: number } | null>(null);

  useEffect(() => {
    if (!quizId) return;
    getQuiz(Number(quizId)).then(setQuiz).catch(() => setQuiz(null));
  }, [quizId]);

  if (!quiz) {
    return <div className="page">Загрузка...</div>;
  }

  const selectAnswer = (questionIndex: number, optionIndex: number) => {
    const next = [...answers];
    next[questionIndex] = optionIndex;
    setAnswers(next);
  };

  const finish = async () => {
    const scored = scoreQuiz(quiz.questions, answers);
    setResult(scored);
    await submitProgress({ quiz_id: quiz.id, quiz_score: scored.score });
  };

  return (
    <div className="page">
      <h1>{quiz.title}</h1>
      {!result &&
        quiz.questions.map((q, qi) => (
          <div key={qi} className="quiz-question">
            <p>{q.question}</p>
            {q.options.map((option, oi) => (
              <button
                key={oi}
                onClick={() => selectAnswer(qi, oi)}
                className={answers[qi] === oi ? "quiz-option quiz-option--selected" : "quiz-option"}
              >
                {option}
              </button>
            ))}
          </div>
        ))}
      {!result && <button onClick={finish}>Завершить</button>}
      {result && (
        <p>
          Результат: {result.score}/{result.total}
        </p>
      )}
    </div>
  );
}
