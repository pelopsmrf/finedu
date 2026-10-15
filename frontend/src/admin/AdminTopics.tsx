import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";
import { createTopic, listTopics } from "./adminApi";

export default function AdminTopics() {
  const state = useLoad(listTopics, []);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const topics = state.data ?? [];

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setError("");
    try {
      const maxOrder = topics.reduce((m, t) => Math.max(m, t.order), 0);
      await createTopic({ title: title.trim(), description: null, icon: "📘", order: maxOrder + 1, is_published: false });
      setTitle("");
      state.reload();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="page">
      <h1>Темы</h1>
      <LoadStatus state={state} />
      <table className="admin-table">
        <thead>
          <tr>
            <th>№</th>
            <th>Тема</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          {topics.map((topic) => (
            <tr key={topic.id}>
              <td>{topic.order}</td>
              <td>
                <Link to={`/admin/topics/${topic.id}`}>
                  {topic.icon} {topic.title}
                </Link>
              </td>
              <td>{topic.is_published ? "✅ опубликована" : "черновик"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="admin-row" onSubmit={handleCreate}>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Название новой темы" />
        <button className="btn btn--primary">+ Тема</button>
      </form>
      {error && <p className="notice notice--error">{error}</p>}
    </div>
  );
}
