import { FC } from "react";

export interface ConversationItem {
  id: string;
  title: string;
  timestamp: string;
}

interface SidebarProps {
  onClearHistory: () => void;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  conversations: ConversationItem[];
  activeConvId: string | null;
  hasCurrentMessages: boolean;
  isOpen: boolean;
  onToggle: () => void;
}

export const Sidebar: FC<SidebarProps> = ({
  onClearHistory,
  onNewConversation,
  onSelectConversation,
  conversations,
  activeConvId,
  hasCurrentMessages,
  isOpen,
  onToggle,
}) => {
  return (
    <>
      {/* Toggle button for mobile */}
      <button
        onClick={onToggle}
        className="lg:hidden fixed top-4 left-4 z-50 bg-[#2a2a2a] hover:bg-[#333] text-white w-10 h-10 rounded flex items-center justify-center"
      >
        ☰
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          w-64 bg-[#171717] border-r border-white/5 flex flex-col
          fixed lg:relative inset-y-0 left-0 z-40
          transform transition-transform duration-300 lg:transform-none
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
          <span className="text-sm font-semibold text-[#ececf1]">Cuộc hội thoại</span>
          <button
            onClick={onNewConversation}
            title="Cuộc hội thoại mới"
            className="w-7 h-7 flex items-center justify-center rounded-md text-[#8e8ea0] hover:text-[#ececf1] hover:bg-white/10 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto py-2">
          {/* Current conversation (unsaved) */}
          {hasCurrentMessages && activeConvId === null && (
            <div className="mx-2 mb-1 px-3 py-2 rounded-lg bg-white/10 border border-white/10">
              <p className="text-xs text-[#ececf1] font-medium truncate">Cuộc hội thoại hiện tại</p>
            </div>
          )}

          {conversations.length === 0 && !hasCurrentMessages && (
            <div className="px-4 py-8 text-center">
              <p className="text-xs text-[#555] leading-relaxed">
                Chưa có cuộc hội thoại nào.<br />Nhấn <span className="text-[#8e8ea0]">+</span> để bắt đầu.
              </p>
            </div>
          )}

          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelectConversation(conv.id)}
              className={`w-full text-left mx-2 px-3 py-2 rounded-lg transition-colors mb-0.5 group ${
                activeConvId === conv.id
                  ? "bg-white/10 text-[#ececf1]"
                  : "text-[#8e8ea0] hover:bg-white/5 hover:text-[#ececf1]"
              }`}
              style={{ width: "calc(100% - 16px)" }}
            >
              <p className="text-xs font-medium truncate">{conv.title}</p>
              <p className="text-[10px] text-[#555] mt-0.5 group-hover:text-[#666]">
                {new Date(conv.timestamp).toLocaleDateString("vi-VN", {
                  day: "2-digit",
                  month: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-white/5">
          <button
            onClick={onClearHistory}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[#8e8ea0] hover:text-red-400 hover:bg-red-500/10 text-xs transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14H6L5 6" />
              <path d="M10 11v6M14 11v6" />
              <path d="M9 6V4h6v2" />
            </svg>
            Xóa lịch sử
          </button>
        </div>
      </aside>
    </>
  );
};
