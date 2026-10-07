import { useState } from "react";
import { broadcast } from "./adminApi";

export default function AdminBroadcast({ onForbidden }: { onForbidden: () => void }) {
  const [text, setText] = useState("");
  const [onlyInactiveDays, setOnlyInactiveDays] = useState<string>("");
  const [sentCount, setSentCount] = useState<number | null>(null);

  const handleSend = async () => {
    if (!text.trim()) return;
    try {
      const result = await broadcast(
        text,
        onlyInactiveDays ? Number(onlyInactiveDays) : undefined
      );
      setSentCount(result.sent);
      setText("");
    } catch (err: any) {
      if (err.message === "forbidden") onForbidden();
    }
  };

  return (
    <div className="page">
      <h1>Рассылка</h1>
      <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Текст сообщения" />
      <input
        value={onlyInactiveDays}
        onChange={(e) => setOnlyInactiveDays(e.target.value)}
        placeholder="Только неактивным N дней (опционально)"
      />
      <button onClick={handleSend}>Отправить</button>
      {sentCount !== null && <p>Отправлено: {sentCount}</p>}
    </div>
  );
}
