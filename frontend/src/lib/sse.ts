import { useEffect } from "react";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export function useSSE<T>(path: string, onMessage: (data: T) => void, enabled = true) {
  useEffect(() => {
    if (!enabled) return;
    const es = new EventSource(`${BASE}${path}`);
    es.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data) as T);
      } catch {
        // ignore malformed frames
      }
    };
    return () => es.close();
  }, [path, enabled, onMessage]);
}
