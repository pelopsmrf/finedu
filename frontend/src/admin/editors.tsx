import type { LessonStep, QuizQuestion } from "./adminApi";

/** Returns a copy of `list` with item `i` moved by `delta` (−1 up, +1 down). */
export function move<T>(list: T[], i: number, delta: number): T[] {
  const j = i + delta;
  if (j < 0 || j >= list.length) return list;
  const copy = [...list];
  [copy[i], copy[j]] = [copy[j], copy[i]];
  return copy;
}

function ItemButtons({ onUp, onDown, onRemove }: { onUp: () => void; onDown: () => void; onRemove: () => void }) {
  return (
    <span className="item-buttons">
      <button type="button" className="btn btn--small" onClick={onUp} title="Выше">↑</button>
      <button type="button" className="btn btn--small" onClick={onDown} title="Ниже">↓</button>
      <button type="button" className="btn btn--small btn--danger" onClick={onRemove} title="Удалить">✕</button>
    </span>
  );
}

export function StepsEditor({ steps, onChange }: { steps: LessonStep[]; onChange: (s: LessonStep[]) => void }) {
  const update = (i: number, patch: Partial<LessonStep>) =>
    onChange(steps.map((s, k) => (k === i ? { ...s, ...patch } : s)));

  return (
    <div className="editor-list">
      {steps.map((step, i) => (
        <div className="editor-card" key={i}>
          <div className="editor-card__head">
            <strong>Карточка {i + 1}</strong>
            <ItemButtons
              onUp={() => onChange(move(steps, i, -1))}
              onDown={() => onChange(move(steps, i, 1))}
              onRemove={() => onChange(steps.filter((_, k) => k !== i))}
            />
          </div>
          <div className="admin-row">
            <input
              className="input--emoji"
              value={step.emoji ?? ""}
              onChange={(e) => update(i, { emoji: e.target.value || null })}
              placeholder="эмодзи"
              title="Эмодзи (необязательно)"
            />
            <input
              value={step.image_url ?? ""}
              onChange={(e) => update(i, { image_url: e.target.value || null })}
              placeholder="Ссылка на картинку (необязательно)"
            />
          </div>
          <textarea rows={4} value={step.text ?? ""} onChange={(e) => update(i, { text: e.target.value })} placeholder="Текст карточки" />
        </div>
      ))}
      <button type="button" className="btn" onClick={() => onChange([...steps, { type: "text", text: "", emoji: null }])}>
        + Карточка
      </button>
    </div>
  );
}

export function QuestionsEditor({
  questions,
  onChange,
}: {
  questions: QuizQuestion[];
  onChange: (q: QuizQuestion[]) => void;
}) {
  const update = (i: number, patch: Partial<QuizQuestion>) =>
    onChange(questions.map((q, k) => (k === i ? { ...q, ...patch } : q)));

  const updateOption = (qi: number, oi: number, value: string) =>
    update(qi, { options: questions[qi].options.map((o, k) => (k === oi ? value : o)) });

  const removeOption = (qi: number, oi: number) => {
    const q = questions[qi];
    if (q.options.length <= 2) return;
    const correct = oi === q.correct_index ? 0 : q.correct_index > oi ? q.correct_index - 1 : q.correct_index;
    update(qi, { options: q.options.filter((_, k) => k !== oi), correct_index: correct });
  };

  return (
    <div className="editor-list">
      {questions.map((q, qi) => (
        <div className="editor-card" key={qi}>
          <div className="editor-card__head">
            <strong>Вопрос {qi + 1}</strong>
            <ItemButtons
              onUp={() => onChange(move(questions, qi, -1))}
              onDown={() => onChange(move(questions, qi, 1))}
              onRemove={() => onChange(questions.filter((_, k) => k !== qi))}
            />
          </div>
          <textarea rows={2} value={q.question} onChange={(e) => update(qi, { question: e.target.value })} placeholder="Текст вопроса" />
          <div className="muted">Отметьте правильный ответ кружком:</div>
          {q.options.map((option, oi) => (
            <div className="admin-row" key={oi}>
              <input
                type="radio"
                name={`correct-${qi}`}
                checked={q.correct_index === oi}
                onChange={() => update(qi, { correct_index: oi })}
                title="Правильный ответ"
              />
              <input value={option} onChange={(e) => updateOption(qi, oi, e.target.value)} placeholder={`Вариант ${oi + 1}`} />
              <button type="button" className="btn btn--small btn--danger" onClick={() => removeOption(qi, oi)} disabled={q.options.length <= 2}>
                ✕
              </button>
            </div>
          ))}
          <button type="button" className="btn btn--small" onClick={() => update(qi, { options: [...q.options, ""] })}>
            + Вариант
          </button>
          <textarea
            rows={2}
            value={q.explanation ?? ""}
            onChange={(e) => update(qi, { explanation: e.target.value || null })}
            placeholder="Пояснение после ответа (необязательно)"
          />
        </div>
      ))}
      <button
        type="button"
        className="btn"
        onClick={() => onChange([...questions, { question: "", options: ["", ""], correct_index: 0, explanation: null }])}
      >
        + Вопрос
      </button>
    </div>
  );
}

/** Problems that would make the server reject a quiz, in plain words. Empty list = OK. */
export function quizProblems(questions: QuizQuestion[]): string[] {
  const problems: string[] = [];
  questions.forEach((q, i) => {
    if (!q.question.trim()) problems.push(`Вопрос ${i + 1}: нет текста вопроса`);
    if (q.options.some((o) => !o.trim())) problems.push(`Вопрос ${i + 1}: есть пустой вариант ответа`);
  });
  return problems;
}

export function SaveStatus({ status }: { status: "" | "saving" | "saved" | string }) {
  if (!status) return null;
  if (status === "saving") return <span className="muted">Сохраняю…</span>;
  if (status === "saved") return <span className="save-ok">Сохранено ✓</span>;
  return <span className="save-error">{status}</span>;
}
