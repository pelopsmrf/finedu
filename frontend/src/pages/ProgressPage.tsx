import { Link } from "react-router-dom";
import { isTelegramEnv } from "../telegram";
import { getProgress } from "../api";
import BadgeGrid from "../components/BadgeGrid";
import LoadStatus from "../components/LoadStatus";
import { ProgressBar } from "../components/QuizRunner";
import { useLoad } from "../useLoad";

export default function ProgressPage() {
  const inTelegram = isTelegramEnv();
  const state = useLoad(() => (inTelegram ? getProgress() : Promise.resolve(null)), [inTelegram]);

  if (!inTelegram) {
    return (
      <div className="page">
        <h1>Прогресс</h1>
        <p>Откройте приложение в Telegram, чтобы сохранять прогресс.</p>
      </div>
    );
  }

  const progress = state.data;
  const earned = progress?.badges.filter((b) => b.earned).length ?? 0;
  return (
    <div className="page">
      <h1>Прогресс</h1>
      <LoadStatus state={state} />
      {progress && (
        <>
          <p>
            Пройдено уроков: {progress.completed_lessons} из {progress.total_lessons}
          </p>
          <ProgressBar value={progress.completed_lessons} max={progress.total_lessons} />

          <h2>По темам</h2>
          <div className="topic-progress-list">
            {progress.topics.map((t) => (
              <Link key={t.topic_id} to={`/topics/${t.topic_id}`} className="topic-progress">
                <div className="topic-progress__head">
                  <span>
                    {t.icon} {t.title}
                  </span>
                  <span className="muted">
                    {t.total > 0 && t.completed === t.total ? "✅" : `${t.completed} из ${t.total}`}
                  </span>
                </div>
                <ProgressBar value={t.completed} max={t.total} />
              </Link>
            ))}
          </div>

          <h2>
            Награды <span className="muted">{earned} из {progress.badges.length}</span>
          </h2>
          <BadgeGrid badges={progress.badges} />
        </>
      )}
    </div>
  );
}
