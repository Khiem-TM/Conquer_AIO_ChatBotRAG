import { FC, useRef, useEffect, useState } from "react";
import { ChatResponse } from "../services/api";

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
  citations?: NonNullable<ChatResponse["citations"]>;
}

export const ChatMessage: FC<DisplayMessage> = ({ role, content, isStreaming, citations }) => {
  const isUser = role === "user";

  return (
    <div className={`group w-full py-6 flex justify-center ${isUser ? "" : "bg-white/[0.03] animate-in fade-in duration-500"}`}>
      <div className="max-w-3xl w-full px-4 lg:px-0 flex gap-4 md:gap-6">
        <div className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center shadow-md ${
          isUser
            ? "bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
            : "bg-gradient-to-br from-emerald-500 to-teal-600 text-white"
        }`}>
          {isUser ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12L2.7 16.5"/><path d="M12 12l8-10"/><path d="M12 12l7.7 4.5"/><path d="M12 12V22"/></svg>
          )}
        </div>

        <div className="flex-1 space-y-3 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm tracking-tight text-white">
              {isUser ? "You" : "Assistant"}
            </span>
          </div>

          <div className={`text-[15px] leading-relaxed text-gray-200 prose-chat ${isStreaming ? "streaming-text" : ""}`}>
            {content}
            {isStreaming && (
              <span className="inline-block w-1.5 h-4 ml-1 bg-indigo-500 animate-pulse align-middle" />
            )}
          </div>

          {citations && citations.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/5">
              {citations.map((cite, idx) => (
                <div key={idx} className="group/cite relative">
                  <span className="px-2 py-1 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 rounded text-[11px] text-indigo-300 cursor-help transition-colors">
                    [{idx + 1}] {cite.source_id.split('/').pop()}
                  </span>
                  <div className="invisible group-hover/cite:visible absolute bottom-full left-0 mb-2 w-64 p-3 bg-[#2f2f2f] border border-white/10 rounded-xl shadow-2xl z-50 text-xs text-gray-300 backdrop-blur-xl">
                    <p className="font-semibold mb-1 text-indigo-300">Source: {cite.source_id}</p>
                    <p className="line-clamp-4 italic">"{cite.text}"</p>
                    <div className="mt-1 text-[10px] opacity-50">Score: {cite.score != null ? (cite.score * 100).toFixed(1) : "N/A"}%</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const WelcomeScreen: FC<{ onSubmit: (text: string) => void; loading: boolean }> = ({ onSubmit, loading }) => {
  const suggestions = [
    "Tôi cần hỗ trợ về tài liệu này",
    "Tóm tắt các điểm chính",
    "Làm thế nào để bắt đầu?",
    "Thông tin về chatbot RAG"
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-2xl mb-8 ring-4 ring-white/5">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      </div>
      <h2 className="text-3xl font-bold text-white mb-3 tracking-tight">Chào mừng bạn trở lại</h2>
      <p className="text-[#8e8ea0] max-w-md mb-10 leading-relaxed font-medium">
        Tôi có thể giúp gì cho bạn hôm nay? Hãy chọn một gợi ý bên dưới hoặc nhập câu hỏi mới.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onSubmit(s)}
            disabled={loading}
            className="p-4 bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 rounded-xl text-left text-sm text-[#ececf1] transition-all hover:scale-[1.02] hover:shadow-lg group"
          >
            {s}
            <svg className="inline-block ml-2 opacity-0 group-hover:opacity-100 transition-opacity" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </button>
        ))}
      </div>
    </div>
  );
};

export interface ChatContainerProps {
  messages: DisplayMessage[];
  loading: boolean;
  error: string | null;
}

export const ChatContainer: FC<ChatContainerProps> = ({ messages, loading, error }) => {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex-1 overflow-y-auto pt-4">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} {...msg} />
      ))}
      {error && (
        <div className="max-w-2xl mx-auto my-6 px-4 py-3 bg-red-900/20 border border-red-500/50 rounded-xl text-center">
          <p className="text-sm text-red-400 font-medium">{error}</p>
        </div>
      )}
      <div ref={endRef} className="h-4" />
    </div>
  );
};

export interface InputAreaProps {
  onSubmit: (question: string) => void;
  onAttachFile?: (files: FileList) => void;
  loading: boolean;
  uploadStatus?: "idle" | "uploading" | "done" | "error";
}

export const InputArea: FC<InputAreaProps> = ({ onSubmit, onAttachFile, loading, uploadStatus }) => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (input.trim() && !loading) {
      onSubmit(input);
      setInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onAttachFile?.(e.target.files);
      e.target.value = "";
    }
  };

  return (
    <div className="p-4 border-t border-white/5 bg-[#212121]">
      <div className="max-w-3xl mx-auto">
        {/* Upload status indicator */}
        {uploadStatus && uploadStatus !== "idle" && (
          <div className={`mb-2 px-3 py-1.5 rounded-lg text-xs flex items-center gap-2 ${
            uploadStatus === "uploading" ? "bg-blue-500/10 text-blue-400" :
            uploadStatus === "done" ? "bg-green-500/10 text-green-400" :
            "bg-red-500/10 text-red-400"
          }`}>
            {uploadStatus === "uploading" && (
              <svg className="animate-spin" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" opacity=".3"/><path d="M21 12a9 9 0 0 1-9 9"/></svg>
            )}
            {uploadStatus === "uploading" ? "Đang tải lên tài liệu..." :
             uploadStatus === "done" ? "Tài liệu đã được tải lên thành công!" :
             "Tải lên thất bại. Thử lại."}
          </div>
        )}

        <div className="relative">
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.docx,.doc,.md"
            className="hidden"
            onChange={handleFileChange}
          />

          {/* Attach button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadStatus === "uploading"}
            title="Đính kèm tài liệu"
            className="absolute left-3 top-1/2 -translate-y-1/2 p-1.5 text-[#8e8ea0] hover:text-[#ececf1] hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Hỏi về tài liệu của bạn..."
            disabled={loading}
            rows={1}
            className="w-full bg-[#2f2f2f] border border-white/10 rounded-2xl py-3 pl-11 pr-12 text-white placeholder-[#8e8ea0] focus:outline-none focus:border-white/20 transition-all resize-none max-h-[200px]"
          />

          {/* Send button */}
          <button
            onClick={() => handleSubmit()}
            disabled={loading || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-white text-black hover:bg-[#ececf1] disabled:bg-[#2f2f2f] disabled:text-[#555] rounded-xl transition-all"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7 11L12 6L17 11M12 18V7"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
