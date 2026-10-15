import { isTelegramEnv } from "../telegram";
import { getProgress } from "../api";
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
        </>
      )}
    </div>
  );
}
