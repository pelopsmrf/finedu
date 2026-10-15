import { Link } from "react-router-dom";
import { getTopics } from "../api";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";

export default function TopicsPage() {
  const state = useLoad(getTopics, []);
  const topics = state.data ?? [];

  return (
    <div className="page">
      <h1>Привет! 👋</h1>
      <p>Выбери тему и начни учиться</p>
      <LoadStatus state={state} />
      {state.data && topics.length === 0 && <p className="muted">Скоро здесь появятся темы.</p>}
      <div className="topic-list">
        {topics.map((topic) => (
          <Link key={topic.id} to={`/topics/${topic.id}`} className="topic-card">
            <div className="topic-card__icon">{topic.icon}</div>
            <div className="topic-card__body">
              <div className="topic-card__title">{topic.title}</div>
              {topic.description && <div className="topic-card__desc">{topic.description}</div>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
