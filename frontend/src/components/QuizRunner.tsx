import { ReactNode, useState } from "react";
import { Quiz } from "../api";
import { resultMessage, scoreQuiz } from "../quizLogic";

interface Props {
  quiz: Quiz;
  /** Called once when the last question is answered. */
  onFinish?: (score: number, total: number) => void;
  /** Buttons shown under the result (e.g. "К урокам"). */
  afterResult?: ReactNode;
}

/** One question at a time with instant right/wrong feedback and an explanation. */
export default function QuizRunner({ quiz, onFinish, afterResult }: Props) {
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [finished, setFinished] = useState(false);

  const questions = quiz.questions;
  const total = questions.length;

  if (finished) {
    const { score } = scoreQuiz(questions, answers);
    return (
      <div className="quiz-result">
        <div className="quiz-result__score">
          {score} из {total}
        </div>
        <p>{resultMessage(score, total)}</p>
        {afterResult}
      </div>
    );
  }

  const question = questions[index];
  const chosen = answers[index];
  const answered = chosen !== undefined;
  const isLast = index === total - 1;

  const choose = (optionIndex: number) => {
    if (answered) return;
    const next = [...answers];
    next[index] = optionIndex;
    setAnswers(next);
  };

  const goNext = () => {
    if (!isLast) {
      setIndex(index + 1);
      return;
    }
    setFinished(true);
    const { score } = scoreQuiz(questions, answers);
    onFinish?.(score, total);
  };

  const optionClass = (oi: number) => {
    if (!answered) return "quiz-option";
    if (oi === question.correct_index) return "quiz-option quiz-option--correct";
    if (oi === chosen) return "quiz-option quiz-option--wrong";
    return "quiz-option quiz-option--dim";
  };

  return (
    <div className="quiz-question">
      <div className="muted">
        Вопрос {index + 1} из {total}
      </div>
      <ProgressBar value={index + (answered ? 1 : 0)} max={total} />
      <p className="quiz-question__text">{question.question}</p>
      {question.options.map((option, oi) => (
        <button key={oi} className={optionClass(oi)} onClick={() => choose(oi)} disabled={answered}>
          {option}
        </button>
      ))}
      {answered && (
        <div className={chosen === question.correct_index ? "notice notice--ok" : "notice notice--error"}>
          <strong>{chosen === question.correct_index ? "Верно! ✅" : "Не совсем ❌"}</strong>
          {question.explanation && <p>{question.explanation}</p>}
        </div>
      )}
      {answered && (
        <button className="btn btn--primary" onClick={goNext}>
          {isLast ? "Посмотреть результат" : "Дальше →"}
        </button>
      )}
    </div>
  );
}

export function ProgressBar({ value, max }: { value: number; max: number }) {
  const percent = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="progress-bar" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
      <div className="progress-bar__fill" style={{ width: `${percent}%` }} />
    </div>
  );
}
