import { useState, useCallback, useEffect } from "react";
import { apiClient, ChatHistoryEntry } from "../services/api";

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
    async (question: string, topK: number = 5) => {
      if (!question.trim()) {
        setError("Question cannot be empty");
        return null;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await apiClient.chat(question, topK);

        // Create history entry from response
        const entry: ChatHistoryEntry = {
          id: `msg_${Date.now()}`,
          question,
          answer: response.answer,
          timestamp: new Date().toISOString(),
        };

        setMessages([entry, ...messages]);
        return response;
      } catch (err: any) {
        const message =
          err.response?.data?.error?.message || err.message || "Chat failed";
        setError(message);
        console.error("Chat error:", err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [messages]
  );

  const clearHistory = useCallback(async () => {
    try {
      await apiClient.clearHistory();
      setMessages([]);
    } catch (err) {
      console.error("Failed to clear history:", err);
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
    } catch (err: any) {
      const message =
        err.response?.data?.error?.message || err.message || "Ingest failed";
      setError(message);
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
