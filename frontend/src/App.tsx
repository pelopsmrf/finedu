import { Route, Routes } from "react-router-dom";
import BottomNav from "./components/BottomNav";
import TopicsPage from "./pages/TopicsPage";
import LessonsPage from "./pages/LessonsPage";
import LessonContentPage from "./pages/LessonContentPage";
import QuizzesPage from "./pages/QuizzesPage";
import QuizPage from "./pages/QuizPage";
import ProgressPage from "./pages/ProgressPage";
import AboutPage from "./pages/AboutPage";

export default function App() {
  return (
    <div className="app">
      <main className="app__content">
        <Routes>
          <Route path="/" element={<TopicsPage />} />
          <Route path="/topics/:topicId" element={<LessonsPage />} />
          <Route path="/lessons/:lessonId" element={<LessonContentPage />} />
          <Route path="/quizzes" element={<QuizzesPage />} />
          <Route path="/quizzes/:quizId" element={<QuizPage />} />
          <Route path="/progress" element={<ProgressPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>
      <BottomNav />
    </div>
  );
}
