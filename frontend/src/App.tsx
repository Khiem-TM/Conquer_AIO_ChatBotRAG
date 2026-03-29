import { useState, useEffect, useCallback, useRef } from 'react';
import './index.css';
import { useChat } from './hooks/useApi';
import {
  apiClient,
  normalizeApiError,
  type StreamEvent,
  type IngestStatusData,
} from './services/api';
import { Sidebar } from './components/Sidebar';
import type { ConversationItem } from './components/Sidebar';
import {
  ChatContainer,
  InputArea,
  WelcomeScreen,
} from './components/ChatComponents';
import type { DisplayMessage } from './components/ChatComponents';

const CHAT_UI_STORAGE_KEY = 'rag_chat_ui_state_v4';


export default function App() {
  const { messages, loading, error, sendMessage, clearHistory, setError } = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [localMsgs, setLocalMsgs] = useState<DisplayMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [conversations, setConversations] = useState<(ConversationItem & { messages: DisplayMessage[] })[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'done' | 'error'>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [backendReady, setBackendReady] = useState(false);
  const [backendStatusMsg, setBackendStatusMsg] = useState<string | null>(null);
  const [ingestHistory, setIngestHistory] = useState<IngestStatusData[]>([]);
  const [documents, setDocuments] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const [chatStarted, setChatStarted] = useState(false);
  const [docBusy, setDocBusy] = useState(false);
  const docInputRef = useRef<HTMLInputElement | null>(null);
  const inFlightRef = useRef(false);
  const hasUserInteractedRef = useRef(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(CHAT_UI_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as {
        conversations?: (ConversationItem & { messages: DisplayMessage[] })[];
        activeConvId?: string | null;
        hasUserInteracted?: boolean;
        sidebarOpen?: boolean;
        currentMessages?: DisplayMessage[];
        activeTab?: 'chat' | 'documents';
        chatStarted?: boolean;
      };
      if (parsed.conversations) setConversations(parsed.conversations);
      if (typeof parsed.activeConvId !== 'undefined') setActiveConvId(parsed.activeConvId);
      if (parsed.currentMessages) setLocalMsgs(parsed.currentMessages);
      if (parsed.activeTab) setActiveTab(parsed.activeTab);
      if (typeof parsed.chatStarted === 'boolean') setChatStarted(parsed.chatStarted);
      if (typeof parsed.hasUserInteracted === 'boolean') hasUserInteractedRef.current = parsed.hasUserInteracted;
      if ((parsed.currentMessages && parsed.currentMessages.length > 0) || parsed.activeConvId || parsed.chatStarted) {
        hasUserInteractedRef.current = true;
      }
      if (typeof parsed.sidebarOpen === 'boolean') setSidebarOpen(parsed.sidebarOpen);
    } catch {
      // ignore invalid local cache
    }
  }, []);

  useEffect(() => {
    const payload = {
      conversations,
      activeConvId,
      hasUserInteracted: hasUserInteractedRef.current,
      sidebarOpen,
      currentMessages: localMsgs,
      activeTab,
      chatStarted,
    };
    localStorage.setItem(CHAT_UI_STORAGE_KEY, JSON.stringify(payload));
  }, [conversations, activeConvId, sidebarOpen, localMsgs, activeTab, chatStarted]);


  const loadIngestHistory = useCallback(async () => {
    try {
      const items = await apiClient.getIngestHistory(20);
      setIngestHistory(items);
    } catch (err) {
      console.warn('Không tải được ingest history:', err);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const files = await apiClient.listDocuments();
      setDocuments(files);
    } catch (err) {
      console.warn('Không tải được danh sách tài liệu:', err);
    }
  }, []);

  const refreshStatus = useCallback(async () => {
    await Promise.all([loadIngestHistory(), loadDocuments()]);
  }, [loadDocuments, loadIngestHistory]);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await apiClient.healthCheck();
        setBackendReady(true);
        setBackendStatusMsg(null);
        await refreshStatus();
      } catch (err: unknown) {
        const normalized = normalizeApiError(err);
        setBackendReady(false);
        setBackendStatusMsg(normalized.message);
      }
    };
    void checkBackend();
  }, [refreshStatus]);

  useEffect(() => {
    if (streaming || hasUserInteractedRef.current) return;
    const synced: DisplayMessage[] = [...messages]
      .reverse()
      .flatMap((m: { id: string; question: string; answer: string; timestamp: string }) => [
        {
          id: `${m.id}_q`,
          role: 'user' as const,
          content: m.question,
          timestamp: String(m.timestamp),
        },
        {
          id: m.id,
          role: 'assistant' as const,
          content: m.answer,
          timestamp: String(m.timestamp),
        },
      ]);
    setLocalMsgs(synced);
  }, [messages, streaming]);

  const handleSend = useCallback(
    async (question: string) => {
      if (!backendReady) {
        setError(backendStatusMsg ?? 'Backend chưa sẵn sàng.');
        return;
      }
      if (!question.trim() || loading || inFlightRef.current) return;

      inFlightRef.current = true;
      hasUserInteractedRef.current = true;
      setChatStarted(true);
      setError(null);

      const uid = `u_${Date.now()}`;
      const aid = `a_${Date.now()}`;
      setLocalMsgs((prev) => [
        ...prev,
        { id: uid, role: 'user', content: question, timestamp: new Date().toISOString() },
        {
          id: aid,
          role: 'assistant',
          content: 'Đang truy xuất tài liệu...',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ]);
      setStreaming(true);

      try {
        const resp = await sendMessage(
          question,
          5,
          (token: string) => {
            setLocalMsgs((prev) =>
              prev.map((m) =>
                m.id === aid
                  ? {
                      ...m,
                      content:
                        m.content === 'Đang truy xuất tài liệu...' ||
                        m.content === 'Model đang xử lý, vui lòng chờ...'
                          ? token
                          : `${m.content}${token}`,
                      isStreaming: true,
                    }
                  : m
              )
            );
          },
          (event: StreamEvent) => {
            if (event.meta || event.ping || event.token) {
              }
            if (event.meta?.status === 'started') {
              setLocalMsgs((prev) =>
                prev.map((m) =>
                  m.id === aid ? { ...m, content: 'Đang truy xuất tài liệu...' } : m
                )
              );
            }
            if (event.ping) {
              setLocalMsgs((prev) =>
                prev.map((m) =>
                  m.id === aid && m.content === 'Đang truy xuất tài liệu...'
                    ? { ...m, content: 'Model đang xử lý, vui lòng chờ...' }
                    : m
                )
              );
            }
          }
        );

        if (resp) {
          setLocalMsgs((prev) =>
            prev.map((m) =>
              m.id === aid
                ? {
                    ...m,
                    content: resp.answer?.trim() ? resp.answer : m.content,
                    citations: resp.citations || [],
                    isStreaming: false,
                  }
                : m
            )
          );
        } else {
          setLocalMsgs((prev) => prev.filter((m) => m.id !== aid));
        }
        await refreshStatus();
      } finally {
        setStreaming(false);
        inFlightRef.current = false;
      }
    },
    [backendReady, backendStatusMsg, loading, sendMessage, setError, refreshStatus]
  );

  const handleStartChat = useCallback(() => {
    hasUserInteractedRef.current = true;
    setChatStarted(true);
    setActiveTab('chat');
    setError(null);
  }, [setError]);

  const persistCurrentConversation = useCallback(() => {
    if (localMsgs.length === 0) return;
    const firstUser = localMsgs.find((m) => m.role === 'user');
    const title = firstUser
      ? firstUser.content.slice(0, 45) + (firstUser.content.length > 45 ? '...' : '')
      : 'New conversation';
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
  }, [activeConvId, localMsgs]);

  const handleNewConversation = useCallback(() => {
    if (streaming) {
      setError('Đang stream phản hồi. Vui lòng chờ hoàn tất trước khi tạo hội thoại mới.');
      return;
    }
    persistCurrentConversation();
    setLocalMsgs([]);
    setActiveConvId(null);
    setChatStarted(true);
  }, [persistCurrentConversation, streaming, setError]);

  const handleSelectConversation = useCallback((id: string) => {
    if (streaming) {
      setError('Đang stream phản hồi. Không thể chuyển hội thoại lúc này.');
      return;
    }
    if (localMsgs.length > 0 && activeConvId === null) {
      persistCurrentConversation();
    }
    const target = conversations.find((c) => c.id === id);
    if (target) {
      setLocalMsgs(target.messages);
      setActiveConvId(id);
      setChatStarted(true);
      setActiveTab('chat');
    }
  }, [streaming, localMsgs.length, activeConvId, persistCurrentConversation, conversations, setError]);

  const handleClear = async () => {
    if (!window.confirm('Xóa toàn bộ lịch sử trò chuyện?')) return;
    await clearHistory();
    hasUserInteractedRef.current = false;
    setLocalMsgs([]);
    setConversations([]);
    setActiveConvId(null);
    setChatStarted(false);
    localStorage.removeItem(CHAT_UI_STORAGE_KEY);
    await refreshStatus();
  };

  const handleAttachFile = useCallback(async (files: FileList) => {
    setUploadStatus('uploading');
    setUploadError(null);
    try {
      const uploaded = await apiClient.uploadFiles(files);
      const ingest = await apiClient.startIngest();
      await refreshStatus();
      const names = (ingest?.document_names && ingest.document_names.length > 0 ? ingest.document_names : uploaded?.files || []).slice(0, 3);
      const summary = names.length > 0 ? names.join(', ') : 'tài liệu vừa tải lên';
      setUploadStatus('done');
      setUploadError(`Đã ingest: ${summary}${(ingest?.document_names && ingest.document_names.length > 3) ? '…' : ''}`);
      window.setTimeout(() => {
        setUploadStatus('idle');
        setUploadError(null);
      }, 3500);
    } catch (err: unknown) {
      const normalized = normalizeApiError(err);
      setUploadStatus('error');
      setUploadError(normalized.message);
      window.setTimeout(() => setUploadStatus('idle'), 3500);
    }
  }, [refreshStatus]);

  const handleDeleteDocument = useCallback(async (filename: string) => {
    if (!window.confirm(`Xóa tài liệu ${filename}?`)) return;
    setDocBusy(true);
    try {
      await apiClient.deleteDocument(filename);
      await refreshStatus();
    } catch (err: unknown) {
      const normalized = normalizeApiError(err);
      setUploadError(normalized.message);
    } finally {
      setDocBusy(false);
    }
  }, [refreshStatus]);

  const handleAddDocumentsFromTab = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    await handleAttachFile(files);
  }, [handleAttachFile]);

  const hasMessages = localMsgs.length > 0;

  return (
    <div className="flex h-screen bg-[#212121] text-[#ececf1] overflow-hidden">
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

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex items-center h-12 px-3 shrink-0 border-b border-white/5">
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              title="Open sidebar"
              className="p-2 mr-2 rounded-lg text-[#8e8ea0] hover:text-[#ececf1] hover:bg-white/8 transition-colors"
            >
              ☰
            </button>
          )}
          <span className="text-sm font-medium text-[#8e8ea0]">RAG Assistant</span>
        </div>

        {!backendReady && (
          <div className="mx-4 mt-4 rounded-xl border border-yellow-500/40 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-200">
            Backend chưa sẵn sàng. {backendStatusMsg ?? 'Vui lòng kiểm tra API/Ollama.'}
          </div>
        )}

        <div className="px-4 pt-3 space-y-3">
          <div className="inline-flex rounded-lg border border-white/10 bg-white/[0.03] p-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-3 py-1.5 text-xs rounded-md ${activeTab === 'chat' ? 'bg-white/15 text-white' : 'text-[#9b9baa]'}`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-3 py-1.5 text-xs rounded-md ${activeTab === 'documents' ? 'bg-white/15 text-white' : 'text-[#9b9baa]'}`}
            >
              Tài liệu
            </button>
          </div>
        </div>

        {activeTab === 'documents' ? (
          <div className="mx-4 mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-4 overflow-y-auto space-y-4">
            <input
              ref={docInputRef}
              type="file"
              multiple
              accept=".pdf,.txt,.docx,.doc,.md"
              className="hidden"
              onChange={(e) => void handleAddDocumentsFromTab(e.target.files)}
            />

            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">Quản lý tài liệu</p>
                <p className="text-xs text-[#9b9baa]">Tải tài liệu lên, ingest, rồi quay lại tab chat để hỏi đáp.</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => void refreshStatus()}
                  className="px-3 py-1.5 text-xs rounded-lg border border-white/15 hover:bg-white/10"
                >
                  Làm mới
                </button>
                <button
                  onClick={() => docInputRef.current?.click()}
                  disabled={docBusy}
                  className="px-3 py-1.5 text-xs rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 disabled:opacity-50"
                >
                  + Thêm tài liệu
                </button>
                <button
                  onClick={() => void apiClient.startIngest().then(refreshStatus).catch((err) => setUploadError(normalizeApiError(err).message))}
                  className="px-3 py-1.5 text-xs rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30"
                >
                  Ingest lại
                </button>
              </div>
            </div>

            {(uploadStatus !== 'idle' || uploadError) && (
              <div className={`px-3 py-2 rounded-lg text-xs ${uploadStatus === 'error' ? 'bg-red-500/10 text-red-300 border border-red-500/30' : uploadStatus === 'done' ? 'bg-green-500/10 text-green-300 border border-green-500/30' : 'bg-blue-500/10 text-blue-300 border border-blue-500/30'}`}>
                {uploadError || (uploadStatus === 'uploading' ? 'Đang tải lên và ingest tài liệu...' : 'Tải lên/ingest đã được kích hoạt thành công.')}
              </div>
            )}

            <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-1">
              {documents.length === 0 ? (
                <p className="text-xs text-[#9b9baa]">Chưa có tài liệu nào trong kho.</p>
              ) : (
                documents.map((name) => (
                  <div key={name} className="flex items-center justify-between text-xs border border-white/10 rounded-lg px-3 py-2">
                    <span className="truncate pr-3">{name}</span>
                    <button
                      onClick={() => void handleDeleteDocument(name)}
                      disabled={docBusy}
                      className="text-red-300 hover:text-red-200 disabled:opacity-50"
                    >
                      Xóa
                    </button>
                  </div>
                ))
              )}
            </div>


            <div className="pt-2">
              <p className="text-xs font-semibold text-[#b4b4c2] mb-2">Lịch sử ingest gần đây</p>
              <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                {ingestHistory.length === 0 ? (
                  <p className="text-xs text-[#9b9baa]">Chưa có phiên ingest nào.</p>
                ) : (
                  ingestHistory.slice(0, 6).map((item) => (
                    <div key={item.ingest_id} className="text-xs text-[#d1d1db] border border-white/5 rounded-lg px-3 py-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium uppercase">{item.status}</span>
                        <span className="text-[#8e8ea0]">{new Date(item.created_at).toLocaleString('vi-VN')}</span>
                      </div>
                      <p className="mt-1 text-[#a8a8b7]">{item.document_names?.length ? item.document_names.join(', ') : item.message || 'Không có mô tả'}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : (
          <>
            {!hasMessages && !chatStarted ? (
              <WelcomeScreen onStartChat={handleStartChat} loading={loading || streaming} />
            ) : (
              <ChatContainer messages={localMsgs} loading={loading || streaming} error={error} />
            )}
            <InputArea
              onSubmit={handleSend}
              onAttachFile={handleAttachFile}
              loading={loading || streaming}
              uploadStatus={uploadStatus}
              uploadError={uploadError}
            />
          </>
        )}
      </div>
    </div>
  );
}
