import { useEffect, useState } from "react";
import { isTelegramEnv } from "../telegram";
import { getProgress, ProgressSummary } from "../api";

export default function ProgressPage() {
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const inTelegram = isTelegramEnv();

  useEffect(() => {
    if (!inTelegram) return;
    getProgress().then(setProgress).catch(() => setProgress(null));
  }, [inTelegram]);

  if (!inTelegram) {
    return (
      <div className="page">
        <p>Откройте приложение в Telegram, чтобы сохранять прогресс.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Прогресс</h1>
      {progress && (
        <p>
          Пройдено уроков: {progress.completed_lessons} из {progress.total_lessons}
        </p>
      )}
    </div>
  );
}
