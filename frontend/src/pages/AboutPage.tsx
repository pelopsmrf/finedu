import { useEffect, useState } from "react";
import { getNotifications, setNotifications } from "../api";
import { getInitData } from "../telegram";

function NotificationsToggle() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getNotifications()
      .then((r) => setEnabled(r.enabled))
      .catch(() => setError(true));
  }, []);

  const toggle = async () => {
    if (enabled === null) return;
    setError(false);
    try {
      const r = await setNotifications(!enabled);
      setEnabled(r.enabled);
    } catch {
      setError(true);
    }
  };

  return (
    <div className="settings-row">
      <label>
        <input type="checkbox" checked={enabled ?? false} disabled={enabled === null} onChange={toggle} />{" "}
        Напоминания от бота
      </label>
      {error && <p className="muted">Не удалось сохранить настройку, попробуйте позже.</p>}
    </div>
  );
}

export default function AboutPage() {
  return (
    <div className="page">
      <h1>Finedu</h1>
      <p>Финансовая грамотность — понятно и интересно.</p>
      <p>
        Приложение помогает детям и студентам разобраться с бюджетом,
        накоплениями, кредитами и инвестициями через короткие уроки и квизы.
      </p>
      {getInitData() && <NotificationsToggle />}
      <p>
        <a href="/privacy-policy.html">Политика конфиденциальности</a>
      </p>
      <p className="muted">Версия 1.1</p>
    </div>
  );
}
