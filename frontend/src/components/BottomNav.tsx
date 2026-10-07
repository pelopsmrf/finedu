import { NavLink } from "react-router-dom";

const TABS = [
  { to: "/", label: "Темы", icon: "📚" },
  { to: "/quizzes", label: "Квизы", icon: "❓" },
  { to: "/progress", label: "Прогресс", icon: "🏆" },
  { to: "/about", label: "О проекте", icon: "ℹ️" },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav">
      {TABS.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.to === "/"}
          className={({ isActive }) => `bottom-nav__item${isActive ? " bottom-nav__item--active" : ""}`}
        >
          <div className="bottom-nav__icon">{tab.icon}</div>
          <div className="bottom-nav__label">{tab.label}</div>
        </NavLink>
      ))}
    </nav>
  );
}
