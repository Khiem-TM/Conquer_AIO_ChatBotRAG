import { useState, useEffect, useCallback } from "react";
import "./index.css";
import { useChat } from "./hooks/useApi";
import { apiClient } from "./services/api";
import { Sidebar } from "./components/Sidebar";
import type { ConversationItem } from "./components/Sidebar";
import {
  ChatContainer,
  InputArea,
  WelcomeScreen,
} from "./components/ChatComponents";
import type { DisplayMessage } from "./components/ChatComponents";

export default function App() {
  const { messages, loading, error, sendMessage, clearHistory, setError } =
    useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [localMsgs, setLocalMsgs] = useState<DisplayMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [conversations, setConversations] = useState<
    (ConversationItem & { messages: DisplayMessage[] })[]
  >([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<
    "idle" | "uploading" | "done" | "error"
  >("idle");

  // ── Sync backend history → local display (skip during streaming) ────────────
  useEffect(() => {
    if (streaming) return;
    const synced: DisplayMessage[] = [...messages].reverse().flatMap((m) => [
      {
        id: `${m.id}_q`,
        role: "user" as const,
        content: m.question,
        timestamp: String(m.timestamp),
      },
      {
        id: m.id,
        role: "assistant" as const,
        content: m.answer,
        timestamp: String(m.timestamp),
      },
    ]);
    setLocalMsgs(synced);
  }, [messages, streaming]);

  // ── Send message with optimistic UI + streaming animation ──────────────────
  const handleSend = useCallback(
    async (question: string) => {
      if (!question.trim() || loading) return;
      setError(null);

      const uid = `u_${Date.now()}`;
      const aid = `a_${Date.now()}`;

      setLocalMsgs((prev) => [
        ...prev,
        {
          id: uid,
          role: "user",
          content: question,
          timestamp: new Date().toISOString(),
        },
        {
          id: aid,
          role: "assistant",
          content: "",
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ]);
      setStreaming(true);

      const resp = await sendMessage(question, 5);

      if (resp) {
        const text = resp.answer;
        const citations = resp.citations ?? [];
        const chunkSize = Math.max(4, Math.ceil(text.length / 60));
        let pos = 0;

        const tick = () => {
          pos = Math.min(pos + chunkSize, text.length);
          const done = pos >= text.length;
          setLocalMsgs((prev) =>
            prev.map((m) =>
              m.id === aid
                ? {
                    ...m,
                    content: text.slice(0, pos),
                    isStreaming: !done,
                    citations: done ? citations : undefined,
                  }
                : m
            )
          );
          if (!done) setTimeout(tick, 12);
          else setStreaming(false);
        };
        tick();
      } else {
        setLocalMsgs((prev) => prev.filter((m) => m.id !== aid));
        setStreaming(false);
      }
    },
    [loading, sendMessage, setError]
  );

  // ── New conversation ────────────────────────────────────────────────────────
  const handleNewConversation = useCallback(() => {
    if (localMsgs.length > 0) {
      const firstUser = localMsgs.find((m) => m.role === "user");
      const title = firstUser
        ? firstUser.content.slice(0, 45) +
          (firstUser.content.length > 45 ? "..." : "")
        : "New conversation";
      const saved = {
        id: activeConvId ?? `conv_${Date.now()}`,
        title,
        timestamp: localMsgs[0]?.timestamp ?? new Date().toISOString(),
        messages: localMsgs,
      };
      setConversations((prev) => {
        const exists = prev.find((c) => c.id === saved.id);
        if (exists) return prev.map((c) => (c.id === saved.id ? saved : c));
        return [saved, ...prev];
      });
    }
    setLocalMsgs([]);
    setActiveConvId(null);
  }, [localMsgs, activeConvId]);

  // ── Select past conversation ────────────────────────────────────────────────
  const handleSelectConversation = useCallback(
    (id: string) => {
      // Save current unsaved conversation first
      if (localMsgs.length > 0 && activeConvId === null) {
        const firstUser = localMsgs.find((m) => m.role === "user");
        const title = firstUser
          ? firstUser.content.slice(0, 45) +
            (firstUser.content.length > 45 ? "..." : "")
          : "New conversation";
        const saved = {
          id: `conv_${Date.now()}`,
          title,
          timestamp: localMsgs[0]?.timestamp ?? new Date().toISOString(),
          messages: localMsgs,
        };
        setConversations((prev) => [saved, ...prev]);
      }

      const target = conversations.find((c) => c.id === id);
      if (target) {
        setLocalMsgs(target.messages);
        setActiveConvId(id);
      }
    },
    [localMsgs, activeConvId, conversations]
  );

  // ── Clear history ───────────────────────────────────────────────────────────
  const handleClear = async () => {
    if (!window.confirm("Xóa toàn bộ lịch sử trò chuyện?")) return;
    await clearHistory();
    setLocalMsgs([]);
    setConversations([]);
    setActiveConvId(null);
  };

  // ── File attach ─────────────────────────────────────────────────────────────
  const handleAttachFile = useCallback(async (files: FileList) => {
    setUploadStatus("uploading");
    try {
      await apiClient.uploadFiles(files);
      setUploadStatus("done");
      setTimeout(() => setUploadStatus("idle"), 3000);
    } catch {
      setUploadStatus("error");
      setTimeout(() => setUploadStatus("idle"), 3000);
    }
  }, []);

  const hasMessages = localMsgs.length > 0;

  return (
    <div className="flex h-screen bg-[#212121] text-[#ececf1] overflow-hidden">
      {/* ── Sidebar ── */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((p) => !p)}
        onClearHistory={handleClear}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        conversations={conversations}
        activeConvId={activeConvId}
        hasCurrentMessages={hasMessages}
      />

      {/* ── Main panel ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center h-12 px-3 shrink-0 border-b border-white/5">
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              title="Open sidebar"
              className="p-2 mr-2 rounded-lg text-[#8e8ea0] hover:text-[#ececf1] hover:bg-white/8 transition-colors"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M9 3v18" />
              </svg>
            </button>
          )}
          <span className="text-sm font-medium text-[#8e8ea0]">
            RAG Assistant
          </span>
        </div>

        {/* Content */}
        {hasMessages ? (
          <>
            <ChatContainer
              messages={localMsgs}
              loading={loading && !streaming}
              error={error}
            />
            <InputArea
              onSubmit={handleSend}
              onAttachFile={handleAttachFile}
              loading={loading}
              uploadStatus={uploadStatus}
            />
          </>
        ) : (
          <WelcomeScreen onSubmit={handleSend} loading={loading} />
        )}
      </div>
    </div>
  );
}
