import { FormEvent, useState } from "react";
import { broadcast } from "./adminApi";

export default function AdminBroadcast() {
  const [text, setText] = useState("");
  const [onlyInactiveDays, setOnlyInactiveDays] = useState<string>("");
  const [result, setResult] = useState("");

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    const days = Number(onlyInactiveDays);
    const audience = days > 0 ? `тем, кто не заходил ${days} дн.` : "всем пользователям";
    if (!window.confirm(`Отправить сообщение ${audience}?`)) return;
    try {
      const r = await broadcast(text.trim(), days > 0 ? days : undefined);
      setResult(`Отправлено: ${r.sent}`);
      setText("");
    } catch (err) {
      setResult((err as Error).message);
    }
  };

  return (
    <div className="page">
      <h1>Рассылка</h1>
      <p className="muted">Получат только те, кто не отключил уведомления. К сообщению добавится кнопка «Открыть Finedu».</p>
      <form className="admin-form" onSubmit={handleSend}>
        <textarea rows={5} value={text} onChange={(e) => setText(e.target.value)} placeholder="Текст сообщения" />
        <label>
          Только тем, кто не заходил N дней (пусто — всем)
          <input type="number" min={1} value={onlyInactiveDays} onChange={(e) => setOnlyInactiveDays(e.target.value)} />
        </label>
        <button className="btn btn--primary" disabled={!text.trim()}>Отправить</button>
      </form>
      {result && <p>{result}</p>}
    </div>
  );
}
