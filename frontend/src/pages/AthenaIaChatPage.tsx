import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChatWindow } from "../components/chat/ChatWindow";
import { Sidebar } from "../components/sidebar/Sidebar";
import { Shell } from "../components/layout/Shell";
import { getChats, getMessages, createChat, askStream, renameChat, deleteChat } from "../services/api";
import type { Chat, ChatMessage, User } from "../types";

type Props = {
  user: User;
  token: string;
  chatIdParam?: string;
  onBack: () => void;
  onLogout: () => void;
};

export default function AthenaIaChatPage({ user, token, chatIdParam, onBack, onLogout }: Props) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const init = async () => {
      try {
        const chatList = await getChats(token);
        setChats(chatList);

        if (chatList.length > 0) {
          const chosenId = chatIdParam ? Number(chatIdParam) : chatList[0].id;
          const target = chatList.find((c) => c.id === chosenId) || chatList[0];

          setSelectedChatId(target.id);
          await new Promise((r) => setTimeout(r, 0));

          const msgs = await getMessages(token, target.id);
          setMessages(
            msgs.map((m) => ({
              id: String(m.id),
              role: m.role,
              content: m.content,
              createdAt: m.created_at,
            }))
          );

          navigate(`/chat/${target.id}`, { replace: true });
        } else {
          const newChat = await createChat(token, "Nova conversa");
          setChats([newChat]);
          setSelectedChatId(newChat.id);
          setMessages([]);
          navigate(`/chat/${newChat.id}`, { replace: true });
        }
      } catch (err) {
        console.error("Erro ao inicializar chat:", err);
      } finally {
        setInitializing(false);
      }
    };

    init();
  }, [token, chatIdParam, navigate]);

  const handleNewChat = async () => {
    const chat = await createChat(token, "Nova conversa");
    setChats((prev) => [chat, ...prev]);
    setSelectedChatId(chat.id);
    setMessages([]);
    navigate(`/chat/${chat.id}`);
  };

  const handleSelectChat = async (id: number) => {
    setSelectedChatId(id);
    const msgs = await getMessages(token, id);
    setMessages(
      msgs.map((m) => ({
        id: String(m.id),
        role: m.role,
        content: m.content,
        createdAt: m.created_at,
      }))
    );
    navigate(`/chat/${id}`);
  };

  const handleRenameChat = async (id: number, currentTitle: string) => {
    const title = window.prompt("Novo titulo para a conversa:", currentTitle || "Nova conversa");
    if (!title) return;
    try {
      const updated = await renameChat(token, id, title);
      setChats((prev) => prev.map((c) => (c.id === id ? { ...c, title: updated.title } : c)));
    } catch (err) {
      console.error("Erro ao renomear chat", err);
    }
  };

  const handleDeleteChat = async (id: number) => {
    const confirmDelete = window.confirm("Deseja excluir esta conversa?");
    if (!confirmDelete) return;
    try {
      await deleteChat(token, id);
      setChats((prev) => prev.filter((c) => c.id !== id));
      if (selectedChatId === id) {
        const remaining = chats.filter((c) => c.id !== id);
        if (remaining.length > 0) {
          const next = remaining[0];
          setSelectedChatId(next.id);
          const msgs = await getMessages(token, next.id);
          setMessages(
            msgs.map((m) => ({
              id: String(m.id),
              role: m.role,
              content: m.content,
              createdAt: m.created_at,
            }))
          );
          navigate(`/chat/${next.id}`);
        } else {
          setSelectedChatId(null);
          setMessages([]);
          navigate("/chat");
        }
      }
    } catch (err) {
      console.error("Erro ao excluir chat", err);
    }
  };

  const handleSend = async (forcedQuestion?: string) => {
    if (!selectedChatId) {
      console.error("selectedChatId ainda e null. Cancelando envio.");
      return;
    }

    const effectiveQuestion = forcedQuestion ?? question;
    if (!effectiveQuestion.trim()) return;

    const userMessage: ChatMessage = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: effectiveQuestion,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLastQuestion(userMessage.content);
    setLoading(true);

    const assistantId = `stream-${Date.now()}`;
    try {
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          createdAt: new Date().toISOString(),
        },
      ]);

      const res = await askStream(token, selectedChatId, userMessage.content);
      if (!res.ok) throw new Error(`Stream falhou: ${res.status}`);
      const reader = res.body?.getReader();
      if (!reader) {
        throw new Error("Stream indisponivel");
      }
      const decoder = new TextDecoder();
      let acc = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: acc } : m))
        );
      }

      const msgs = await getMessages(token, selectedChatId);
      setMessages(
        msgs.map((m) => ({
          id: String(m.id),
          role: m.role,
          content: m.content,
          createdAt: m.created_at,
        }))
      );
    } catch (e) {
      console.error(e);
      try {
        const completion = await (await import("../services/api")).ask(token, selectedChatId, userMessage.content);
        const assistantMessage: ChatMessage = completion.message
          ? {
              id: String(completion.message.id),
              role: completion.message.role,
              content: completion.message.content,
              createdAt: completion.message.created_at || new Date().toISOString(),
              sources: completion.sources,
            }
          : {
              id: completion.id,
              role: "assistant",
              content: completion.content,
              createdAt: new Date().toISOString(),
              sources: completion.sources,
            };
        setMessages((prev) => [...prev.filter((m) => m.id !== assistantId), assistantMessage]);
      } catch (fallbackErr) {
        console.error(fallbackErr);
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "assistant",
            content: "Tive um problema tecnico para responder agora. Tente novamente em instantes.",
            createdAt: new Date().toISOString(),
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  if (initializing || selectedChatId === null) {
    return (
      <Shell
        sidebar={
          <Sidebar
            user={user}
            chats={[]}
            selectedChatId={null}
            onSelectChat={() => { }}
            onNewChat={() => { }}
            onLogout={onLogout}
            adminUsersCount={0}
            policiesCount={0}
          />
        }
      >
        <div className="loading-screen">
          <p className="muted">Carregando conversa...</p>
        </div>
      </Shell>
    );
  }

  return (
    <Shell
      sidebar={
        <Sidebar
          user={user}
          chats={chats}
          selectedChatId={selectedChatId}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          onLogout={onLogout}
          onRenameChat={handleRenameChat}
          onDeleteChat={handleDeleteChat}
          adminUsersCount={0}
          policiesCount={0}
        />
      }
    >
      <ChatWindow
        messages={messages}
        question={question}
        setQuestion={setQuestion}
        onSend={() => handleSend()}
        onRegenerate={lastQuestion ? () => handleSend(lastQuestion) : undefined}
        loading={loading}
        token={token}
        chatId={selectedChatId!}
      />

      <div className="hero-actions">
        <button className="chat-pill" onClick={onBack}>
          Voltar ao dashboard
        </button>
      </div>
    </Shell>
  );
}
