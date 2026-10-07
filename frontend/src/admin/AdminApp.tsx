import { useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import AdminTopics from "./AdminTopics";
import AdminBroadcast from "./AdminBroadcast";

export default function AdminApp() {
  const [forbidden, setForbidden] = useState(false);

  if (forbidden) {
    return (
      <div className="page">
        <p>Доступ запрещён.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <nav>
        <Link to="/admin">Темы</Link> | <Link to="/admin/broadcast">Рассылка</Link>
      </nav>
      <Routes>
        <Route path="/" element={<AdminTopics onForbidden={() => setForbidden(true)} />} />
        <Route
          path="/broadcast"
          element={<AdminBroadcast onForbidden={() => setForbidden(true)} />}
        />
      </Routes>
    </div>
  );
}
