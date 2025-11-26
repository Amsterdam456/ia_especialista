import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import "./App.css";
import bg from "./assets/bg_athena.jpg";

type User = {
  id: number;
  email: string;
  full_name?: string | null;
  is_admin: boolean;
  created_at: string;
};

type Chat = {
  id: number;
  title: string;
  created_at: string;
};

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

const sanitizeUrl = (url: string | undefined | null) =>
  url?.trim().replace(/\/$/, "");

const API_URL =
  sanitizeUrl(import.meta.env.VITE_API_URL) ||
  (typeof window !== "undefined" ? sanitizeUrl(window.location.origin) : undefined) ||
  "http://localhost:8000";

function App() {
  const [email, setEmail] = useState("admin@athena.local");
  const [password, setPassword] = useState("admin123");
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChat, setSelectedChat] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adminUsers, setAdminUsers] = useState<User[]>([]);
  const [policies, setPolicies] = useState<string[]>([]);

  const headers = useMemo(
    () => ({
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
    }),
    [token]
  );

  useEffect(() => {
    const savedToken = localStorage.getItem("athena_token");
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchProfile(token);
  }, [token]);

  const fetchProfile = async (authToken: string) => {
    try {
      const res = await fetch(`${API_URL}/auth/me`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (!res.ok) throw new Error("Falha ao buscar usuário");
      const data = await res.json();
      setUser(data);
      await Promise.all([loadChats(authToken), data.is_admin ? loadAdminData(authToken) : Promise.resolve()]);
    } catch (err: any) {
      setError(err.message);
      setToken(null);
      localStorage.removeItem("athena_token");
    }
  };

  const loadChats = async (authToken: string = token ?? "") => {
    const res = await fetch(`${API_URL}/chats`, { headers: { Authorization: `Bearer ${authToken}` } });
    if (!res.ok) return;
    const data = await res.json();
    setChats(data);
    if (data.length && !selectedChat) {
      setSelectedChat(data[0].id);
      loadMessages(data[0].id, authToken);
    }
  };

  const loadMessages = async (chatId: number, authToken: string = token ?? "") => {
    const res = await fetch(`${API_URL}/chats/${chatId}/messages`, { headers: { Authorization: `Bearer ${authToken}` } });
    if (res.ok) {
      const data = await res.json();
      setMessages(data);
    }
  };

  const loadAdminData = async (authToken: string = token ?? "") => {
    const [usersRes, policiesRes] = await Promise.all([
      fetch(`${API_URL}/admin/users`, { headers: { Authorization: `Bearer ${authToken}` } }),
      fetch(`${API_URL}/admin/policies`, { headers: { Authorization: `Bearer ${authToken}` } }),
    ]);

    if (usersRes.ok) setAdminUsers(await usersRes.json());
    if (policiesRes.ok) setPolicies(await policiesRes.json());
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Login inválido");
      const data = await res.json();
      setToken(data.access_token);
      localStorage.setItem("athena_token", data.access_token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateChat = async () => {
    if (!token) return;
    const res = await fetch(`${API_URL}/chats`, {
      method: "POST",
      headers,
      body: JSON.stringify({ title: "Nova conversa" }),
    });
    if (!res.ok) return;
    const chat = await res.json();
    setChats((prev) => [chat, ...prev]);
    setSelectedChat(chat.id);
    setMessages([]);
  };

  const handleSend = async () => {
    if (!token || !question.trim()) return;

    let chatId = selectedChat;
    if (!chatId) {
      const res = await fetch(`${API_URL}/chats`, {
        method: "POST",
        headers,
        body: JSON.stringify({ title: "Nova conversa" }),
      });
      const chat = await res.json();
      chatId = chat.id;
      setSelectedChat(chatId);
      setChats((prev) => [chat, ...prev]);
    }

    setLoading(true);
    const res = await fetch(`${API_URL}/chats/${chatId}/ask`, {
      method: "POST",
      headers,
      body: JSON.stringify({ question }),
    });

    if (res.ok) {
      const data = await res.json();
      setMessages(data);
      setQuestion("");
    }
    setLoading(false);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setChats([]);
    setMessages([]);
    localStorage.removeItem("athena_token");
  };

  if (!token || !user) {
    return (
      <div className="athena-login" style={{ backgroundImage: `url(${bg})` }}>
        <div className="login-card">
          <h1>ATHENA · Painel Seguro</h1>
          <p>Faça login para acessar os chats e o painel administrativo.</p>
          <form onSubmit={handleLogin}>
            <label>E-mail institucional</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />

            <label>Senha</label>
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />

            <button type="submit" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </button>
          </form>
          {error && <div className="alert">{error}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="athena-shell" style={{ backgroundImage: `url(${bg})` }}>
      <aside className="athena-sidebar">
        <div className="logo-mini">ATHENA</div>
        <div className="user-block">
          <div className="user-name">{user.full_name || user.email}</div>
          <div className="user-role">{user.is_admin ? "Administrador" : "Usuário"}</div>
          <button className="outline" onClick={handleLogout}>
            Sair
          </button>
        </div>

        <div className="sidebar-section">
          <div className="section-title">Conversas</div>
          <button className="primary" onClick={handleCreateChat}>
            + Nova conversa
          </button>
          <ul className="chat-list">
            {chats.map((c) => (
              <li
                key={c.id}
                className={c.id === selectedChat ? "active" : ""}
                onClick={() => {
                  setSelectedChat(c.id);
                  loadMessages(c.id);
                }}
              >
                <span>{c.title}</span>
                <small>{new Date(c.created_at).toLocaleString("pt-BR")}</small>
              </li>
            ))}
            {!chats.length && <li className="empty">Nenhuma conversa criada ainda.</li>}
          </ul>
        </div>

        {user.is_admin && (
          <div className="sidebar-section">
            <div className="section-title">Administração</div>
            <div className="pill">{adminUsers.length} usuários</div>
            <div className="pill">{policies.length} políticas</div>
          </div>
        )}
      </aside>

      <main className="athena-main">
        <header className="athena-header">
          <div>
            <p className="overline">Projeto ATHENA · Inteligência Corporativa Estácio</p>
            <h1>IA Especialista + Painel Operacional</h1>
            <p className="subtitle">
              Chat seguro com base em políticas internas, múltiplas conversas por usuário e visão administrativa para
              governança.
            </p>
          </div>
        </header>

        <section className="chat-window">
          <div className="messages">
            {messages.map((m) => (
              <div key={m.id} className={`msg ${m.role}`}>
                <div className="msg-role">{m.role === "user" ? "Você" : "Athena"}</div>
                <div className="msg-content">{m.content}</div>
                <div className="msg-time">{new Date(m.created_at).toLocaleString("pt-BR")}</div>
              </div>
            ))}
            {!messages.length && <div className="empty">Envie uma pergunta para começar.</div>}
          </div>
          <div className="composer">
            <textarea
              placeholder="Pergunte à Athena sobre políticas internas ou processos da Estácio"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
            />
            <button className="primary" onClick={handleSend} disabled={loading}>
              {loading ? "Gerando resposta..." : "Enviar"}
            </button>
          </div>
        </section>

        {user.is_admin && (
          <section className="admin-panel">
            <div>
              <h2>Usuários</h2>
              <p className="muted">Gerencie quem acessa a IA e as conversas.</p>
              <div className="table">
                <div className="table-row table-head">
                  <div>E-mail</div>
                  <div>Perfil</div>
                  <div>Cadastro</div>
                </div>
                {adminUsers.map((u) => (
                  <div className="table-row" key={u.id}>
                    <div>{u.email}</div>
                    <div>{u.is_admin ? "Administrador" : "Usuário"}</div>
                    <div>{new Date(u.created_at).toLocaleDateString("pt-BR")}</div>
                  </div>
                ))}
                {!adminUsers.length && <div className="empty">Nenhum usuário adicional encontrado.</div>}
              </div>
            </div>

            <div>
              <h2>Políticas ingeridas</h2>
              <p className="muted">Arquivos monitorados para o RAG e watcher em segundo plano.</p>
              <ul className="pill-list">
                {policies.map((p) => (
                  <li key={p}>{p}</li>
                ))}
                {!policies.length && <li className="empty">Nenhum arquivo em policies/</li>}
              </ul>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
