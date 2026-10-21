import { Link } from "react-router-dom";
import { getTopicProgress, getTopics, type TopicProgress } from "../api";
import LoadStatus from "../components/LoadStatus";
import { ProgressBar } from "../components/QuizRunner";
import { useLoad } from "../useLoad";

export default function TopicsPage() {
  const state = useLoad(() => Promise.all([getTopics(), getTopicProgress()]), []);
  const [topics, progress] = state.data ?? [[], new Map()];

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
              {renderProgress(progress.get(topic.id))}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function renderProgress(p: TopicProgress | undefined) {
  if (!p || p.total === 0 || p.completed === 0) return null;
  return (
    <div className="topic-card__progress">
      <ProgressBar value={p.completed} max={p.total} />
      <span className="muted">
        {p.completed === p.total ? "Пройдено ✅" : `${p.completed} из ${p.total}`}
      </span>
    </div>
  );
}
