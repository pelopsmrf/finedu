import { useEffect, useState } from "react";
import { AdminTopic, createTopic, listTopics, updateTopic } from "./adminApi";

export default function AdminTopics({ onForbidden }: { onForbidden: () => void }) {
  const [topics, setTopics] = useState<AdminTopic[]>([]);
  const [title, setTitle] = useState("");

  const reload = () => {
    listTopics()
      .then(setTopics)
      .catch((err) => {
        if (err.message === "forbidden") onForbidden();
      });
  };

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreate = async () => {
    if (!title.trim()) return;
    try {
      await createTopic({ title, order: topics.length, is_published: false });
      setTitle("");
      reload();
    } catch (err: any) {
      if (err.message === "forbidden") onForbidden();
    }
  };

  const togglePublished = async (topic: AdminTopic) => {
    try {
      await updateTopic(topic.id, { ...topic, is_published: !topic.is_published });
      reload();
    } catch (err: any) {
      if (err.message === "forbidden") onForbidden();
    }
  };

  return (
    <div className="page">
      <h1>Темы</h1>
      <div>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Название темы" />
        <button onClick={handleCreate}>+ Тема</button>
      </div>
      <table>
        <thead>
          <tr>
            <th>Тема</th>
            <th>Опубликована</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {topics.map((topic) => (
            <tr key={topic.id}>
              <td>{topic.title}</td>
              <td>{topic.is_published ? "✅" : "черновик"}</td>
              <td>
                <button onClick={() => togglePublished(topic)}>
                  {topic.is_published ? "Снять с публикации" : "Опубликовать"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
