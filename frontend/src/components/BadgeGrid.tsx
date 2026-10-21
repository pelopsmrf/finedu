import type { Badge } from "../api";

export default function BadgeGrid({ badges }: { badges: Badge[] }) {
  return (
    <div className="badge-grid">
      {badges.map((b) => (
        <div key={b.id} className={b.earned ? "badge" : "badge badge--locked"}>
          <div className="badge__icon">{b.icon}</div>
          <div className="badge__title">{b.title}</div>
          <div className="badge__desc">{b.earned ? "Получено ✓" : b.description}</div>
        </div>
      ))}
    </div>
  );
}
