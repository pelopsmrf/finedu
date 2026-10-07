import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTopics, Topic } from "../api";

export default function TopicsPage() {
  const [topics, setTopics] = useState<Topic[]>([]);

  useEffect(() => {
    getTopics().then(setTopics).catch(() => setTopics([]));
  }, []);

  return (
    <div className="page">
      <h1>Привет! 👋</h1>
      <p>Выбери тему и начни учиться</p>
      <div className="topic-list">
        {topics.map((topic) => (
          <Link key={topic.id} to={`/topics/${topic.id}`} className="topic-card">
            <div className="topic-card__icon">{topic.icon}</div>
            <div className="topic-card__body">
              <div className="topic-card__title">{topic.title}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
