import { useState } from "react";
import { GlassButton } from "../buttons/GlassButton";
import type { Chat, User } from "../../types";

type Props = {
  user: User;
  chats: Chat[];
  selectedChatId: number | null;
  onSelectChat: (id: number) => void;
  onNewChat: () => void;
  onLogout: () => void;
  onRenameChat?: (id: number, title: string) => void;
  onDeleteChat?: (id: number) => void;
  adminUsersCount: number;
  policiesCount: number;
  showChats?: boolean;
  showMetrics?: boolean;
};

export function Sidebar({
  user,
  chats,
  selectedChatId,
  onSelectChat,
  onNewChat,
  onLogout,
  onRenameChat,
  onDeleteChat,
  showChats = true,
  showMetrics = true,
}: Props) {
  const [openMenuId, setOpenMenuId] = useState<number | null>(null);
  const badge = user.role || (user.is_admin ? "Admin" : "User");

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="logo">ATHENA</div>
        <div className="badge">{badge}</div>
      </div>

      <div className="sidebar-user">
        <div className="user-name">{user.full_name || user.email}</div>
        <div className="user-email">{user.email}</div>
      </div>

      {showChats ? (
        <button className="chat-pill w-full" onClick={onNewChat}>
          + Novo chat
        </button>
      ) : null}

      {showChats ? (
        <div className="sidebar-list">
          <p className="overline">Conversas</p>
          <div className="sidebar-chats">
            {chats.map((chat) => (
              <div className="chat-row" key={chat.id}>
                <button
                  className={`chat-pill ${selectedChatId === chat.id ? "active" : ""}`}
                  onClick={() => onSelectChat(chat.id)}
                >
                  <span>{chat.title}</span>
                  <span className="pill-date">{new Date(chat.created_at).toLocaleDateString()}</span>
                </button>
                <div className="chat-actions">
                  <button
                    className="glass-button compact"
                    onClick={() => setOpenMenuId(openMenuId === chat.id ? null : chat.id)}
                    title="Opções"
                  >
                    ⋯
                  </button>
                  {openMenuId === chat.id && (
                    <div className="chat-menu">
                      <button onClick={() => { setOpenMenuId(null); onRenameChat?.(chat.id, chat.title); }}>Renomear</button>
                      <button className="danger" onClick={() => { setOpenMenuId(null); onDeleteChat?.(chat.id); }}>Excluir</button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chats.length === 0 && <div className="muted">Nenhum chat ainda.</div>}
          </div>
        </div>
      ) : null}

      {/* Métricas removidas para um visual mais clean */}

      <GlassButton className="w-full" variant="ghost" onClick={onLogout}>
        Sair
      </GlassButton>
    </aside>
  );
}
