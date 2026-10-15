import { FormEvent, useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import AdminBroadcast from "./AdminBroadcast";
import AdminLessonEdit from "./AdminLessonEdit";
import AdminQuizEdit from "./AdminQuizEdit";
import AdminQuizzes from "./AdminQuizzes";
import AdminTopicEdit from "./AdminTopicEdit";
import AdminTopics from "./AdminTopics";
import { checkAdmin, FORBIDDEN_EVENT, getAdminToken, setAdminToken } from "./adminApi";

type Access = "checking" | "denied" | "ok";

export default function AdminApp() {
  const [access, setAccess] = useState<Access>("checking");

  useEffect(() => {
    checkAdmin().then((ok) => setAccess(ok ? "ok" : "denied"));
    const onForbidden = () => setAccess("denied");
    window.addEventListener(FORBIDDEN_EVENT, onForbidden);
    return () => window.removeEventListener(FORBIDDEN_EVENT, onForbidden);
  }, []);

  if (access === "checking") return <div className="page">Проверка доступа…</div>;
  if (access === "denied") return <AdminLogin onSuccess={() => setAccess("ok")} />;

  const logout = () => {
    setAdminToken("");
    setAccess("denied");
  };

  return (
    <div className="admin">
      <nav className="admin-nav">
        <NavLink to="/admin" end>Темы и уроки</NavLink>
        <NavLink to="/admin/quizzes">Отдельные квизы</NavLink>
        <NavLink to="/admin/broadcast">Рассылка</NavLink>
        <a href="/" target="_blank" rel="noreferrer">Открыть приложение ↗</a>
        {getAdminToken() && <button className="btn btn--small" onClick={logout}>Выйти</button>}
      </nav>
      <Routes>
        <Route path="/" element={<AdminTopics />} />
        <Route path="/topics/:topicId" element={<AdminTopicEdit />} />
        <Route path="/lessons/:lessonId" element={<AdminLessonEdit />} />
        <Route path="/quizzes" element={<AdminQuizzes />} />
        <Route path="/quizzes/:quizId" element={<AdminQuizEdit />} />
        <Route path="/broadcast" element={<AdminBroadcast />} />
      </Routes>
    </div>
  );
}

function AdminLogin({ onSuccess }: { onSuccess: () => void }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setAdminToken(token.trim());
    const ok = await checkAdmin();
    setBusy(false);
    if (ok) {
      onSuccess();
    } else {
      setAdminToken("");
      setError(true);
    }
  };

  return (
    <div className="page admin-login">
      <h1>Вход в админку</h1>
      <form onSubmit={submit}>
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Секретный ключ (FINEDU_ADMIN_TOKEN)"
          autoFocus
        />
        <button className="btn btn--primary" disabled={busy || !token.trim()}>
          Войти
        </button>
      </form>
      {error && <p className="notice notice--error">Ключ не подошёл.</p>}
    </div>
  );
}
