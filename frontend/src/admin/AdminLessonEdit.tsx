import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";
import { createQuiz, deleteLesson, getLesson, LessonInput, listQuizzes, updateLesson } from "./adminApi";
import { SaveStatus, StepsEditor } from "./editors";

export default function AdminLessonEdit() {
  const lessonId = Number(useParams().lessonId);
  const navigate = useNavigate();
  const state = useLoad(() => Promise.all([getLesson(lessonId), listQuizzes(lessonId)]), [lessonId]);
  const [form, setForm] = useState<LessonInput | null>(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (state.data) {
      const { id: _id, ...rest } = state.data[0];
      setForm(rest);
    }
  }, [state.data]);

  if (!state.data || !form) return <div className="page"><LoadStatus state={state} /></div>;
  const quizzes = state.data[1];

  const save = async (e?: FormEvent) => {
    e?.preventDefault();
    setStatus("saving");
    try {
      // Empty cards would show as blank screens to users — drop them on save.
      const content = form.content.filter((s) => s.text?.trim() || s.image_url?.trim());
      await updateLesson(lessonId, { ...form, content });
      setForm({ ...form, content });
      setStatus("saved");
    } catch (err) {
      setStatus((err as Error).message);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Удалить урок «${form.title}» вместе с его квизом? Это нельзя отменить.`)) return;
    await deleteLesson(lessonId);
    navigate(`/admin/topics/${form.topic_id}`);
  };

  const addQuiz = async () => {
    const quiz = await createQuiz({
      lesson_id: lessonId,
      title: `Проверь себя: ${form.title}`,
      questions: [],
      is_published: true,
    });
    navigate(`/admin/quizzes/${quiz.id}`);
  };

  return (
    <div className="page">
      <Link to={`/admin/topics/${form.topic_id}`} className="back-link">← К теме</Link>
      <h1>Урок</h1>
      <form className="admin-form" onSubmit={save}>
        <label>
          Название
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </label>
        <div className="admin-row">
          <label>
            Порядок в теме
            <input type="number" value={form.order} onChange={(e) => setForm({ ...form, order: Number(e.target.value) })} />
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} />
            Опубликован
          </label>
        </div>

        <h2>Карточки урока</h2>
        <p className="muted">Каждая карточка — один экран. Пустые карточки при сохранении убираются.</p>
        <StepsEditor steps={form.content} onChange={(content) => setForm({ ...form, content })} />

        <div className="admin-row sticky-save">
          <button className="btn btn--primary" disabled={!form.title.trim()}>Сохранить урок</button>
          <SaveStatus status={status} />
          <button type="button" className="btn btn--danger push-right" onClick={remove}>Удалить урок</button>
        </div>
      </form>

      <h2>Квиз после урока</h2>
      {quizzes.length === 0 && (
        <>
          <p className="muted">У урока пока нет квиза.</p>
          <button className="btn" onClick={addQuiz}>+ Квиз к уроку</button>
        </>
      )}
      <ul>
        {quizzes.map((q) => (
          <li key={q.id}>
            <Link to={`/admin/quizzes/${q.id}`}>{q.title}</Link> — {q.questions.length} вопр.
            {!q.is_published && " (черновик)"}
          </li>
        ))}
      </ul>
    </div>
  );
}
