import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChatWindow } from "../components/chat/ChatWindow";
import { Sidebar } from "../components/sidebar/Sidebar";
import { Shell } from "../components/layout/Shell";
import { getChats, getMessages, createChat, ask } from "../services/api";
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
  const navigate = useNavigate();

  useEffect(() => {
    const init = async () => {
      const chatList = await getChats(token);
      setChats(chatList);
      if (chatList.length) {
        const initialId = chatIdParam ? Number(chatIdParam) : chatList[0].id;
        const target = chatList.find((c) => c.id === initialId) || chatList[0];
        setSelectedChatId(target.id);
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
      }
    };
    init().catch(console.error);
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

  const handleSend = async () => {
    if (!question.trim() || !selectedChatId) return;
    const userMessage: ChatMessage = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: question,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const completion = await ask(token, selectedChatId, question);
      const assistantMessage: ChatMessage = completion.message
        ? {
            id: String(completion.message.id),
            role: completion.message.role,
            content: completion.message.content,
            createdAt: completion.message.created_at || new Date().toISOString(),
          }
        : {
            id: completion.id,
            role: "assistant",
            content: completion.content,
            createdAt: new Date().toISOString(),
          };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (e) {
      console.error(e);
      const fallback: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: "Tive um problema técnico para responder agora. Tente novamente em instantes.",
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallback]);
    } finally {
      setLoading(false);
    }
  };

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
          adminUsersCount={0}
          policiesCount={0}
        />
      }
    >
      <ChatWindow
        messages={messages}
        question={question}
        setQuestion={setQuestion}
        onSend={handleSend}
        loading={loading}
      />
      <div className="hero-actions">
        <button className="chat-pill" onClick={onBack}>Voltar ao dashboard</button>
      </div>
    </Shell>
  );
}
