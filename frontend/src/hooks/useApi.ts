import { useState, useCallback, useEffect } from "react";
import {
  apiClient,
  ChatHistoryEntry,
  normalizeApiError,
  type StreamEvent,
} from "../services/api";

export function useChat() {
  const [messages, setMessages] = useState<ChatHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const history = await apiClient.getHistory();
      setMessages(history || []);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  }, []);

  const sendMessage = useCallback(
    async (
      question: string,
      topK: number = 5,
      onToken?: (token: string) => void,
      onEvent?: (event: StreamEvent) => void
    ) => {
      if (!question.trim()) {
        setError("Question cannot be empty");
        return null;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await apiClient.chatStream(question, topK, true, {
          onToken,
          onEvent,
        });

        const entry: ChatHistoryEntry = {
          id: `msg_${Date.now()}`,
          question,
          answer: response.answer,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [entry, ...prev]);
        return response;
      } catch (err: unknown) {
        const normalized = normalizeApiError(err);
        setError(normalized.message);
        console.error("Chat error:", normalized);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const clearHistory = useCallback(async () => {
    try {
      await apiClient.clearHistory();
      setMessages([]);
      setError(null);
    } catch (err: unknown) {
      const normalized = normalizeApiError(err);
      setError(`Không thể xóa lịch sử: ${normalized.message}`);
      console.error("Failed to clear history:", normalized);
    }
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearHistory,
    loadHistory,
    setError,
  };
}

export function useIngest() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ingestId, setIngestId] = useState<string | null>(null);

  const startIngest = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiClient.startIngest();
      setIngestId(result?.ingest_id || null);
      return result;
    } catch (err: unknown) {
      const normalized = normalizeApiError(err);
      setError(normalized.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const checkStatus = useCallback(async (id: string) => {
    try {
      return await apiClient.getIngestStatus(id);
    } catch (err) {
      console.error("Failed to check status:", err);
      return null;
    }
  }, []);

  return { startIngest, checkStatus, loading, error, ingestId };
}
