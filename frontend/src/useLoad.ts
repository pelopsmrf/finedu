import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

export interface LoadState<T> {
  data: T | null;
  error: boolean;
  /** The server answered 404: the item does not exist or is not published. */
  notFound: boolean;
  loading: boolean;
  reload: () => void;
}

/** Runs `load` on mount and whenever `deps` change; keeps loading/error state for the page. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]): LoadState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    setNotFound(false);
    load()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(true);
        setNotFound(err instanceof ApiError && err.status === 404);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, attempt]);

  const reload = useCallback(() => setAttempt((n) => n + 1), []);
  return { data, error, notFound, loading, reload };
}
