import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getTopicLessons, Lesson } from "../api";

export default function LessonsPage() {
  const { topicId } = useParams();
  const [lessons, setLessons] = useState<Lesson[]>([]);

  useEffect(() => {
    if (!topicId) return;
    getTopicLessons(Number(topicId)).then(setLessons).catch(() => setLessons([]));
  }, [topicId]);

  return (
    <div className="page">
      <h1>Уроки темы</h1>
      <div className="lesson-list">
        {lessons.map((lesson) => (
          <Link key={lesson.id} to={`/lessons/${lesson.id}`} className="lesson-row">
            {lesson.title}
          </Link>
        ))}
      </div>
    </div>
  );
}
