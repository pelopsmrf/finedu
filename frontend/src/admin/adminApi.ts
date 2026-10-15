import type { Lesson, LessonStep, Quiz, QuizQuestion, Topic } from "../api";
import { getInitData } from "../telegram";

const TOKEN_KEY = "finedu_admin_token";
/** Fired when the server rejects admin credentials, so AdminApp can show the login form. */
export const FORBIDDEN_EVENT = "finedu-admin-forbidden";

export function getAdminToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setAdminToken(token: string): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function adminRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": getAdminToken(),
      "X-Telegram-Init-Data": getInitData() ?? "",
      ...(init?.headers ?? {}),
    },
  });
  if (resp.status === 403 || resp.status === 401) {
    window.dispatchEvent(new Event(FORBIDDEN_EVENT));
    throw new Error("forbidden");
  }
  if (!resp.ok) {
    throw new Error(`Ошибка сервера (${resp.status})`);
  }
  return resp.json() as Promise<T>;
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });

export type AdminTopic = Topic;
export type TopicInput = Omit<Topic, "id">;
export type LessonInput = Omit<Lesson, "id">;
export type QuizInput = Omit<Quiz, "id">;
export type { Lesson, LessonStep, Quiz, QuizQuestion };

/** true if the current token / Telegram account has admin rights. */
export async function checkAdmin(): Promise<boolean> {
  try {
    await adminRequest("/api/admin/_probe");
    return true;
  } catch {
    return false;
  }
}

export const listTopics = () => adminRequest<Topic[]>("/api/admin/topics");
export const getTopic = (id: number) => adminRequest<Topic>(`/api/admin/topics/${id}`);
export const createTopic = (t: TopicInput) => adminRequest<Topic>("/api/admin/topics", json("POST", t));
export const updateTopic = (id: number, t: TopicInput) =>
  adminRequest<Topic>(`/api/admin/topics/${id}`, json("PUT", t));
export const deleteTopic = (id: number) => adminRequest(`/api/admin/topics/${id}`, { method: "DELETE" });

export const listLessons = (topicId: number) => adminRequest<Lesson[]>(`/api/admin/topics/${topicId}/lessons`);
export const getLesson = (id: number) => adminRequest<Lesson>(`/api/admin/lessons/${id}`);
export const createLesson = (l: LessonInput) => adminRequest<Lesson>("/api/admin/lessons", json("POST", l));
export const updateLesson = (id: number, l: LessonInput) =>
  adminRequest<Lesson>(`/api/admin/lessons/${id}`, json("PUT", l));
export const deleteLesson = (id: number) => adminRequest(`/api/admin/lessons/${id}`, { method: "DELETE" });

export const listQuizzes = (lessonId?: number) =>
  adminRequest<Quiz[]>(lessonId === undefined ? "/api/admin/quizzes" : `/api/admin/quizzes?lesson_id=${lessonId}`);
export const getQuiz = (id: number) => adminRequest<Quiz>(`/api/admin/quizzes/${id}`);
export const createQuiz = (q: QuizInput) => adminRequest<Quiz>("/api/admin/quizzes", json("POST", q));
export const updateQuiz = (id: number, q: QuizInput) => adminRequest<Quiz>(`/api/admin/quizzes/${id}`, json("PUT", q));
export const deleteQuiz = (id: number) => adminRequest(`/api/admin/quizzes/${id}`, { method: "DELETE" });

export function broadcast(text: string, onlyInactiveDays?: number): Promise<{ sent: number }> {
  return adminRequest<{ sent: number }>(
    "/api/admin/broadcast",
    json("POST", { text, only_inactive_days: onlyInactiveDays ?? null })
  );
}
