import { GlassButton } from "../buttons/GlassButton";
import type { Chat, User } from "../../types";

type Props = {
  user: User;
  chats: Chat[];
  selectedChatId: number | null;
  onSelectChat: (id: number) => void;
  onNewChat: () => void;
  onLogout: () => void;
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
  adminUsersCount,
  policiesCount,
  showChats = true,
  showMetrics = true,
}: Props) {
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
        <GlassButton onClick={onNewChat} className="w-full">
          + Novo chat
        </GlassButton>
      ) : null}

      {showChats ? (
        <div className="sidebar-list">
          <p className="overline">Conversas</p>
          <div className="sidebar-chats">
            {chats.map((chat) => (
              <button
                key={chat.id}
                className={`chat-pill ${selectedChatId === chat.id ? "active" : ""}`}
                onClick={() => onSelectChat(chat.id)}
              >
                <span>{chat.title}</span>
                <span className="pill-date">{new Date(chat.created_at).toLocaleDateString()}</span>
              </button>
            ))}
            {chats.length === 0 && <div className="muted">Nenhum chat ainda.</div>}
          </div>
        </div>
      ) : null}

      {showMetrics && (user.is_admin || user.role === "admin") ? (
        <div className="sidebar-metrics">
          <div className="metric">
            <div className="metric-label">Usuários</div>
            <div className="metric-value">{adminUsersCount}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Políticas</div>
            <div className="metric-value">{policiesCount}</div>
          </div>
        </div>
      ) : null}

      <GlassButton variant="ghost" onClick={onLogout} className="w-full">
        Sair
      </GlassButton>
    </aside>
  );
}
