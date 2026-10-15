import { Link, useParams } from "react-router-dom";
import { getQuiz, submitProgress } from "../api";
import LoadStatus from "../components/LoadStatus";
import QuizRunner from "../components/QuizRunner";
import { useLoad } from "../useLoad";

export default function QuizPage() {
  const quizId = Number(useParams().quizId);
  const state = useLoad(() => getQuiz(quizId), [quizId]);
  const quiz = state.data;

  return (
    <div className="page">
      <Link to="/quizzes" className="back-link">← Все квизы</Link>
      <LoadStatus state={state} />
      {quiz && (
        <>
          <h1>{quiz.title}</h1>
          <QuizRunner
            key={quiz.id}
            quiz={quiz}
            onFinish={(score) => submitProgress({ quiz_id: quiz.id, quiz_score: score })}
            afterResult={
              <Link to="/quizzes" className="btn">
                К другим квизам
              </Link>
            }
          />
        </>
      )}
    </div>
  );
}
