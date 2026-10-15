import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";
import { createQuiz, listQuizzes } from "./adminApi";

/** Standalone quizzes shown in the "Квизы" tab (lesson quizzes live on the lesson page). */
export default function AdminQuizzes() {
  const state = useLoad(() => listQuizzes(), []);
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const quizzes = (state.data ?? []).filter((q) => q.lesson_id === null);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    const quiz = await createQuiz({ lesson_id: null, title: title.trim(), questions: [], is_published: false });
    navigate(`/admin/quizzes/${quiz.id}`);
  };

  return (
    <div className="page">
      <h1>Отдельные квизы</h1>
      <p className="muted">Эти квизы видны во вкладке «Квизы». Квизы уроков редактируются на странице урока.</p>
      <LoadStatus state={state} />
      <table className="admin-table">
        <thead>
          <tr><th>Квиз</th><th>Вопросов</th><th>Статус</th></tr>
        </thead>
        <tbody>
          {quizzes.map((q) => (
            <tr key={q.id}>
              <td><Link to={`/admin/quizzes/${q.id}`}>{q.title}</Link></td>
              <td>{q.questions.length}</td>
              <td>{q.is_published ? "✅ опубликован" : "черновик"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="admin-row" onSubmit={create}>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Название нового квиза" />
        <button className="btn btn--primary">+ Квиз</button>
      </form>
    </div>
  );
}
