import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getLesson, Lesson, submitProgress } from "../api";

export default function LessonContentPage() {
  const { lessonId } = useParams();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!lessonId) return;
    getLesson(Number(lessonId)).then(setLesson).catch(() => setLesson(null));
  }, [lessonId]);

  if (!lesson) {
    return <div className="page">Загрузка...</div>;
  }

  const content = lesson.content ?? [];
  const isLastStep = step >= content.length - 1;

  const handleNext = async () => {
    if (!isLastStep) {
      setStep(step + 1);
      return;
    }
    await submitProgress({ lesson_id: lesson.id });
    setDone(true);
  };

  const currentBlock = content[step];

  return (
    <div className="page">
      <h1>{lesson.title}</h1>
      {currentBlock && <p>{currentBlock.text}</p>}
      {!done && <button onClick={handleNext}>Далее →</button>}
      {done && <p>Урок завершён ✅</p>}
    </div>
  );
}
