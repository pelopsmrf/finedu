import { Link, useParams } from "react-router-dom";
import { getCompletedLessonIds, getTopic, getTopicLessons } from "../api";
import LoadStatus from "../components/LoadStatus";
import { useLoad } from "../useLoad";

export default function LessonsPage() {
  const topicId = Number(useParams().topicId);
  const state = useLoad(
    () => Promise.all([getTopic(topicId), getTopicLessons(topicId), getCompletedLessonIds()]),
    [topicId]
  );

  if (!state.data) {
    return (
      <div className="page">
        <Link to="/" className="back-link">← Все темы</Link>
        <LoadStatus state={state} />
      </div>
    );
  }

  const [topic, lessons, completed] = state.data;
  const doneCount = lessons.filter((l) => completed.has(l.id)).length;

  return (
    <div className="page">
      <Link to="/" className="back-link">← Все темы</Link>
      <h1>
        {topic.icon} {topic.title}
      </h1>
      {topic.description && <p>{topic.description}</p>}
      {completed.size > 0 && (
        <p className="muted">
          Пройдено {doneCount} из {lessons.length}
        </p>
      )}
      {lessons.length === 0 && <p className="muted">Уроки скоро появятся.</p>}
      <div className="lesson-list">
        {lessons.map((lesson, i) => (
          <Link key={lesson.id} to={`/lessons/${lesson.id}`} className="lesson-row">
            <span className="lesson-row__mark">{completed.has(lesson.id) ? "✅" : i + 1}</span>
            {lesson.title}
          </Link>
        ))}
      </div>
    </div>
  );
}
