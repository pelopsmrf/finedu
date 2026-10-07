import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getQuizzes, Quiz } from "../api";

export default function QuizzesPage() {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);

  useEffect(() => {
    getQuizzes().then(setQuizzes).catch(() => setQuizzes([]));
  }, []);

  return (
    <div className="page">
      <h1>Быстрые квизы</h1>
      <p>Проверь себя — 2-3 минуты</p>
      <div className="lesson-list">
        {quizzes.map((quiz) => (
          <Link key={quiz.id} to={`/quizzes/${quiz.id}`} className="lesson-row">
            {quiz.title}
          </Link>
        ))}
      </div>
    </div>
  );
}
