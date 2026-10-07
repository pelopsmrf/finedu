import { getInitData, isTelegramEnv } from "./telegram";

export interface Topic {
  id: number;
  title: string;
  description: string | null;
  icon: string | null;
  order: number;
  is_published: boolean;
}

export interface Lesson {
  id: number;
  topic_id: number;
  title: string;
  order: number;
  content: Array<{ type: string; text?: string }>;
  is_published: boolean;
}

export interface Quiz {
  id: number;
  lesson_id: number | null;
  title: string;
  questions: Array<{ question: string; options: string[]; correct_index: number }>;
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, init);
  if (!resp.ok) {
    throw new Error(`Request to ${path} failed with ${resp.status}`);
  }
  return resp.json() as Promise<T>;
}

export function getTopics(): Promise<Topic[]> {
  return request<Topic[]>("/api/topics");
}

export function getTopicLessons(topicId: number): Promise<Lesson[]> {
  return request<Lesson[]>(`/api/topics/${topicId}/lessons`);
}

export function getLesson(id: number): Promise<Lesson> {
  return request<Lesson>(`/api/lessons/${id}`);
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
  const initData = getInitData();
  await fetch("/api/progress", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData ?? "",
    },
    body: JSON.stringify(payload),
  });
}

export function getProgress(): Promise<ProgressSummary> {
  const initData = getInitData();
  return request<ProgressSummary>("/api/progress/me", {
    headers: { "X-Telegram-Init-Data": initData ?? "" },
  });
}
