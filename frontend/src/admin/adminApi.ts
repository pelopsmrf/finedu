import { getInitData } from "../telegram";

async function adminRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const initData = getInitData();
  const resp = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData ?? "",
      ...(init?.headers ?? {}),
    },
  });
  if (resp.status === 403 || resp.status === 401) {
    throw new Error("forbidden");
  }
  if (!resp.ok) {
    throw new Error(`Request to ${path} failed with ${resp.status}`);
  }
  return resp.json() as Promise<T>;
}

export interface AdminTopic {
  id: number;
  title: string;
  description: string | null;
  icon: string | null;
  order: number;
  is_published: boolean;
}

export function listTopics(): Promise<AdminTopic[]> {
  return adminRequest<AdminTopic[]>("/api/topics");
}

export function createTopic(payload: Partial<AdminTopic>): Promise<AdminTopic> {
  return adminRequest<AdminTopic>("/api/admin/topics", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTopic(id: number, payload: Partial<AdminTopic>): Promise<AdminTopic> {
  return adminRequest<AdminTopic>(`/api/admin/topics/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function broadcast(text: string, onlyInactiveDays?: number): Promise<{ sent: number }> {
  return adminRequest<{ sent: number }>("/api/admin/broadcast", {
    method: "POST",
    body: JSON.stringify({ text, only_inactive_days: onlyInactiveDays ?? null }),
  });
}
