import { Link } from "react-router-dom";
import { getQuizzes } from "../api";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";

export default function QuizzesPage() {
  const state = useLoad(getQuizzes, []);
  const quizzes = state.data ?? [];

  return (
    <div className="page">
      <h1>Быстрые квизы</h1>
      <p>Проверь себя — 2-3 минуты</p>
      <LoadStatus state={state} />
      {state.data && quizzes.length === 0 && <p className="muted">Квизы скоро появятся.</p>}
      <div className="lesson-list">
        {quizzes.map((quiz) => (
          <Link key={quiz.id} to={`/quizzes/${quiz.id}`} className="lesson-row">
            <span className="lesson-row__mark">❓</span>
            {quiz.title}
          </Link>
        ))}
      </div>
    </div>
  );
}
