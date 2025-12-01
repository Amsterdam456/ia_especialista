import type { Dispatch, SetStateAction } from "react";
import type { ChatMessage } from "../../types";
import { GlassButton } from "../buttons/GlassButton";

type Props = {
  messages: ChatMessage[];
  question: string;
  setQuestion: Dispatch<SetStateAction<string>>;
  onSend: () => void;
  loading?: boolean;
};

export function ChatWindow({ messages, question, setQuestion, onSend, loading }: Props) {
  return (
    <section className="chat-card glass-panel">
      <header className="chat-header">
        <div>
          <p className="overline">ATHENA CHAT</p>
          <h3>Converse com a IA especialista</h3>
        </div>
        <GlassButton variant="ghost" onClick={onSend} disabled={loading || !question.trim()}>
          {loading ? "Gerando..." : "Enviar"}
        </GlassButton>
      </header>

      <div className="chat-body">
        {messages.length === 0 ? (
          <div className="chat-empty">Comece perguntando qualquer coisa sobre as politicas internas.</div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-bubble ${msg.role === "user" ? "bubble-user" : "bubble-ai"}`}
            >
              <div className="chat-bubble-meta">
                <span>{msg.role === "user" ? "Você" : "ATHENA"}</span>
                <span>
                  {new Date(msg.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <p>{msg.content}</p>
            </div>
          ))
        )}
        {loading && (
          <div className="typing-indicator">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
            <span>ATHENA está respondendo...</span>
          </div>
        )}
      </div>

      <div className="chat-input glass-panel">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Digite sua pergunta..."
          onKeyDown={(e) => {
            if (e.key === "Enter" && !loading) onSend();
          }}
        />
        <GlassButton onClick={onSend} disabled={loading || !question.trim()}>
          {loading ? "Gerando..." : "Enviar"}
        </GlassButton>
      </div>
    </section>
  );
}
