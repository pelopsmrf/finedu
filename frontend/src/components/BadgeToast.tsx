import { useEffect, useState } from "react";
import { NEW_BADGES_EVENT, type Badge } from "../api";

const SHOW_MS = 4000;

/** Pops up "New badge!" whenever submitProgress reports freshly earned badges. */
export default function BadgeToast() {
  const [badges, setBadges] = useState<Badge[]>([]);

  useEffect(() => {
    const onBadges = (e: Event) => setBadges((e as CustomEvent<Badge[]>).detail);
    window.addEventListener(NEW_BADGES_EVENT, onBadges);
    return () => window.removeEventListener(NEW_BADGES_EVENT, onBadges);
  }, []);

  useEffect(() => {
    if (badges.length === 0) return;
    const timer = setTimeout(() => setBadges([]), SHOW_MS);
    return () => clearTimeout(timer);
  }, [badges]);

  if (badges.length === 0) return null;
  return (
    <div className="badge-toast" role="status" onClick={() => setBadges([])}>
      {badges.map((b) => (
        <div key={b.id} className="badge-toast__item">
          <span className="badge-toast__icon">{b.icon}</span>
          <span>
            Новая награда: <strong>{b.title}</strong>!
          </span>
        </div>
      ))}
    </div>
  );
}
