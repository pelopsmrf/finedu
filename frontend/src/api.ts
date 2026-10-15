import { getInitData, isTelegramEnv } from "./telegram";

export interface Topic {
  id: number;
  title: string;
  description: string | null;
  icon: string | null;
  order: number;
  is_published: boolean;
}

export interface LessonStep {
  type?: "text" | "image";
  text?: string;
  emoji?: string | null;
  image_url?: string | null;
}

export interface Lesson {
  id: number;
  topic_id: number;
  title: string;
  order: number;
  content: LessonStep[];
  is_published: boolean;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation?: string | null;
}

export interface Quiz {
  id: number;
  lesson_id: number | null;
  title: string;
  questions: QuizQuestion[];
  is_published: boolean;
}

export interface ProgressSummary {
  progress: Array<{
    lesson_id: number | null;
    completed_at: string | null;
    quiz_id: number | null;
    quiz_score: number | null;
    last_activity_at: string;
  }>;
  completed_lessons: number;
  total_lessons: number;
}

export class ApiError extends Error {
  constructor(public status: number, path: string) {
    super(`Request to ${path} failed with ${status}`);
  }
}

function telegramHeaders(): Record<string, string> {
  return { "X-Telegram-Init-Data": getInitData() ?? "" };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, init);
  if (!resp.ok) {
    throw new ApiError(resp.status, path);
  }
  return resp.json() as Promise<T>;
}

export function getTopics(): Promise<Topic[]> {
  return request<Topic[]>("/api/topics");
}

export function getTopic(id: number): Promise<Topic> {
  return request<Topic>(`/api/topics/${id}`);
}

export function getTopicLessons(topicId: number): Promise<Lesson[]> {
  return request<Lesson[]>(`/api/topics/${topicId}/lessons`);
}

export function getLesson(id: number): Promise<Lesson> {
  return request<Lesson>(`/api/lessons/${id}`);
}

/** The quiz attached to a lesson, or null if the lesson has none. */
export async function getLessonQuiz(lessonId: number): Promise<Quiz | null> {
  try {
    return await request<Quiz>(`/api/lessons/${lessonId}/quiz`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export function getQuizzes(): Promise<Quiz[]> {
  return request<Quiz[]>("/api/quizzes");
}

export function getQuiz(id: number): Promise<Quiz> {
  return request<Quiz>(`/api/quizzes/${id}`);
}

export async function submitProgress(payload: {
  lesson_id?: number | null;
  quiz_id?: number | null;
  quiz_score?: number | null;
}): Promise<void> {
  if (!isTelegramEnv()) {
    return;
  }
  try {
    await fetch("/api/progress", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...telegramHeaders() },
      body: JSON.stringify(payload),
    });
  } catch {
    // Progress is a bonus: a network hiccup must not break the lesson.
  }
}

export function getProgress(): Promise<ProgressSummary> {
  return request<ProgressSummary>("/api/progress/me", { headers: telegramHeaders() });
}

/** IDs of lessons the current Telegram user has completed (empty outside Telegram). */
export async function getCompletedLessonIds(): Promise<Set<number>> {
  if (!getInitData()) return new Set();
  try {
    const summary = await getProgress();
    return new Set(
      summary.progress
        .filter((p) => p.lesson_id !== null && p.completed_at)
        .map((p) => p.lesson_id as number)
    );
  } catch {
    return new Set();
  }
}

export function getNotifications(): Promise<{ enabled: boolean }> {
  return request("/api/users/me/notifications", { headers: telegramHeaders() });
}

export function setNotifications(enabled: boolean): Promise<{ enabled: boolean }> {
  return request("/api/users/me/notifications", {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...telegramHeaders() },
    body: JSON.stringify({ enabled }),
  });
}
