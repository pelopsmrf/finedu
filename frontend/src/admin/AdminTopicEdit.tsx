import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";
import { createLesson, deleteTopic, getTopic, listLessons, TopicInput, updateTopic } from "./adminApi";
import { SaveStatus } from "./editors";

export default function AdminTopicEdit() {
  const topicId = Number(useParams().topicId);
  const navigate = useNavigate();
  const state = useLoad(() => Promise.all([getTopic(topicId), listLessons(topicId)]), [topicId]);
  const [form, setForm] = useState<TopicInput | null>(null);
  const [status, setStatus] = useState("");
  const [newLesson, setNewLesson] = useState("");

  useEffect(() => {
    if (state.data) {
      const { id: _id, ...rest } = state.data[0];
      setForm(rest);
    }
  }, [state.data]);

  if (!state.data || !form) return <div className="page"><LoadStatus state={state} /></div>;
  const lessons = state.data[1];

  const save = async (e?: FormEvent) => {
    e?.preventDefault();
    setStatus("saving");
    try {
      await updateTopic(topicId, form);
      setStatus("saved");
    } catch (err) {
      setStatus((err as Error).message);
    }
  };

  const remove = async () => {
    const warning = lessons.length
      ? `Удалить тему «${form.title}» вместе с ${lessons.length} урок(ами) и их квизами? Это нельзя отменить.`
      : `Удалить тему «${form.title}»?`;
    if (!window.confirm(warning)) return;
    await deleteTopic(topicId);
    navigate("/admin");
  };

  const addLesson = async (e: FormEvent) => {
    e.preventDefault();
    if (!newLesson.trim()) return;
    const maxOrder = lessons.reduce((m, l) => Math.max(m, l.order), 0);
    const lesson = await createLesson({
      topic_id: topicId,
      title: newLesson.trim(),
      order: maxOrder + 1,
      content: [{ type: "text", text: "", emoji: null }],
      is_published: false,
    });
    navigate(`/admin/lessons/${lesson.id}`);
  };

  return (
    <div className="page">
      <Link to="/admin" className="back-link">← Все темы</Link>
      <h1>Тема</h1>
      <form className="admin-form" onSubmit={save}>
        <label>
          Название
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </label>
        <div className="admin-row">
          <label>
            Значок
            <input className="input--emoji" value={form.icon ?? ""} onChange={(e) => setForm({ ...form, icon: e.target.value || null })} />
          </label>
          <label>
            Порядок
            <input type="number" value={form.order} onChange={(e) => setForm({ ...form, order: Number(e.target.value) })} />
          </label>
        </div>
        <label>
          Короткое описание
          <textarea rows={2} value={form.description ?? ""} onChange={(e) => setForm({ ...form, description: e.target.value || null })} />
        </label>
        <label className="checkbox">
          <input type="checkbox" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} />
          Опубликована (видна пользователям)
        </label>
        <div className="admin-row">
          <button className="btn btn--primary" disabled={!form.title.trim()}>Сохранить</button>
          <SaveStatus status={status} />
          <button type="button" className="btn btn--danger push-right" onClick={remove}>Удалить тему</button>
        </div>
      </form>

      <h2>Уроки темы</h2>
      <table className="admin-table">
        <thead>
          <tr><th>№</th><th>Урок</th><th>Карточек</th><th>Статус</th></tr>
        </thead>
        <tbody>
          {lessons.map((l) => (
            <tr key={l.id}>
              <td>{l.order}</td>
              <td><Link to={`/admin/lessons/${l.id}`}>{l.title}</Link></td>
              <td>{l.content.length}</td>
              <td>{l.is_published ? "✅ опубликован" : "черновик"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="admin-row" onSubmit={addLesson}>
        <input value={newLesson} onChange={(e) => setNewLesson(e.target.value)} placeholder="Название нового урока" />
        <button className="btn btn--primary">+ Урок</button>
      </form>
    </div>
  );
}
