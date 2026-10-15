import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getLesson, getLessonQuiz, submitProgress } from "../api";
import LoadStatus from "../components/LoadStatus";
import QuizRunner, { ProgressBar } from "../components/QuizRunner";
import { pluralRu } from "../quizLogic";
import { useLoad } from "../useLoad";

type Stage = "steps" | "done" | "quiz";

export default function LessonContentPage() {
  const lessonId = Number(useParams().lessonId);
  const state = useLoad(
    () => Promise.all([getLesson(lessonId), getLessonQuiz(lessonId)]),
    [lessonId]
  );
  const [step, setStep] = useState(0);
  const [stage, setStage] = useState<Stage>("steps");

  if (!state.data) {
    return (
      <div className="page">
        <LoadStatus state={state} />
      </div>
    );
  }

  const [lesson, quiz] = state.data;
  const steps = lesson.content ?? [];
  const backToTopic = (
    <Link to={`/topics/${lesson.topic_id}`} className="btn">
      К урокам темы
    </Link>
  );

  if (stage === "quiz" && quiz) {
    return (
      <div className="page">
        <h1>{quiz.title}</h1>
        <QuizRunner
          quiz={quiz}
          onFinish={(score) => submitProgress({ quiz_id: quiz.id, quiz_score: score })}
          afterResult={backToTopic}
        />
      </div>
    );
  }

  if (stage === "done" || steps.length === 0) {
    return (
      <div className="page lesson-done">
        <div className="lesson-done__emoji">🎉</div>
        <h1>Урок пройден!</h1>
        <p>{lesson.title}</p>
        {quiz && (
          <button className="btn btn--primary" onClick={() => setStage("quiz")}>
            Проверить себя: {quiz.questions.length}{" "}
            {pluralRu(quiz.questions.length, ["вопрос", "вопроса", "вопросов"])}
          </button>
        )}
        {backToTopic}
      </div>
    );
  }

  const current = steps[step];
  const isLast = step === steps.length - 1;

  const next = () => {
    if (!isLast) {
      setStep(step + 1);
      return;
    }
    setStage("done");
    void submitProgress({ lesson_id: lesson.id });
  };

  return (
    <div className="page">
      <Link to={`/topics/${lesson.topic_id}`} className="back-link">← К урокам</Link>
      <h1>{lesson.title}</h1>
      <ProgressBar value={step + 1} max={steps.length} />
      <div className="lesson-card" key={step}>
        {current.emoji && <div className="lesson-card__emoji">{current.emoji}</div>}
        {current.image_url && <img className="lesson-card__image" src={current.image_url} alt="" />}
        {current.text && <p>{current.text}</p>}
      </div>
      <div className="lesson-nav">
        <button className="btn" onClick={() => setStep(step - 1)} disabled={step === 0}>
          ← Назад
        </button>
        <button className="btn btn--primary" onClick={next}>
          {isLast ? "Завершить урок" : "Далее →"}
        </button>
      </div>
    </div>
  );
}
