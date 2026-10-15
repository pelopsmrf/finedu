import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";
import { deleteQuiz, getQuiz, QuizInput, updateQuiz } from "./adminApi";
import { QuestionsEditor, quizProblems, SaveStatus } from "./editors";

export default function AdminQuizEdit() {
  const quizId = Number(useParams().quizId);
  const navigate = useNavigate();
  const state = useLoad(() => getQuiz(quizId), [quizId]);
  const [form, setForm] = useState<QuizInput | null>(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (state.data) {
      const { id: _id, ...rest } = state.data;
      setForm(rest);
    }
  }, [state.data]);

  if (!state.data || !form) return <div className="page"><LoadStatus state={state} /></div>;

  const backTo = form.lesson_id !== null ? `/admin/lessons/${form.lesson_id}` : "/admin/quizzes";
  const problems = quizProblems(form.questions);

  const save = async (e?: FormEvent) => {
    e?.preventDefault();
    if (problems.length) return;
    setStatus("saving");
    try {
      await updateQuiz(quizId, form);
      setStatus("saved");
    } catch (err) {
      setStatus((err as Error).message);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Удалить квиз «${form.title}»? Это нельзя отменить.`)) return;
    await deleteQuiz(quizId);
    navigate(backTo);
  };

  return (
    <div className="page">
      <Link to={backTo} className="back-link">{form.lesson_id !== null ? "← К уроку" : "← Все квизы"}</Link>
      <h1>Квиз</h1>
      <form className="admin-form" onSubmit={save}>
        <label>
          Название
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </label>
        <label className="checkbox">
          <input type="checkbox" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} />
          Опубликован
        </label>

        <h2>Вопросы</h2>
        <QuestionsEditor questions={form.questions} onChange={(questions) => setForm({ ...form, questions })} />

        {problems.length > 0 && (
          <ul className="notice notice--error">
            {problems.map((p) => <li key={p}>{p}</li>)}
          </ul>
        )}
        <div className="admin-row sticky-save">
          <button className="btn btn--primary" disabled={!form.title.trim() || problems.length > 0}>Сохранить квиз</button>
          <SaveStatus status={status} />
          <button type="button" className="btn btn--danger push-right" onClick={remove}>Удалить квиз</button>
        </div>
      </form>
    </div>
  );
}
