import { useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import type { ChatMessage } from "../../types";
import { GlassButton } from "../buttons/GlassButton";
import { sendFeedback } from "../../services/api";

type Props = {
  messages: ChatMessage[];
  question: string;
  setQuestion: Dispatch<SetStateAction<string>>;
  onSend: () => void;
  onRegenerate?: () => void;
  loading?: boolean;
  token: string;
  chatId: number;
};

const MAX_QUESTION_CHARS = 2000;

export function ChatWindow({ messages, question, setQuestion, onSend, onRegenerate, loading, token, chatId }: Props) {
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [ratings, setRatings] = useState<Record<string, number>>({});

  const handleFeedback = async (msg: ChatMessage, rating: number) => {
    const numericId = Number(msg.id);
    if (!msg.id || Number.isNaN(numericId) || !chatId) return;
    const comment = window.prompt("Deixe um comentario para melhorar a IA (opcional):", "") ?? "";
    setSubmitting(msg.id);
    try {
      await sendFeedback(token, chatId, numericId, rating, comment || undefined);
      setRatings((prev) => ({ ...prev, [msg.id]: rating }));
    } catch (err) {
      console.error("Erro ao enviar feedback", err);
    } finally {
      setSubmitting(null);
    }
  };

  const remaining = MAX_QUESTION_CHARS - question.length;
  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error("Erro ao copiar", err);
    }
  };

  const handleRefine = () => {
    const refined = window.prompt("Refine sua pergunta:", question);
    if (refined !== null) {
      setQuestion(refined);
    }
  };

  return (
    <section className="chat-card glass-panel">
      <header className="chat-header">
        <div>
          <p className="overline">ATHENA CHAT</p>
          <h3>Converse com a IA especialista</h3>
        </div>
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
                <span>{msg.role === "user" ? "Voce" : "ATHENA"}</span>
                <span>
                  {new Date(msg.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <div className="chat-content">
                {msg.content.split("\n").map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="chat-sources">
                  <span className="muted">Fontes:</span>
                  {msg.sources.map((s, idx) => (
                    <span key={`${msg.id}-src-${idx}`} className="pill">
                      {s.source} | pag. {s.page}
                    </span>
                  ))}
                </div>
              )}
              {msg.role === "assistant" && msg.id && !msg.id.startsWith("tmp") && !Number.isNaN(Number(msg.id)) && (
                <div className="chat-feedback">
                  <span className="muted">Avalie a resposta:</span>
                  <button
                    className={`glass-button compact ${ratings[msg.id] === 1 ? "active" : ""}`}
                    disabled={submitting === msg.id}
                    onClick={() => handleFeedback(msg, 1)}
                    title="Util"
                  >
                    +1
                  </button>
                  <button
                    className={`glass-button compact ${ratings[msg.id] === -1 ? "active" : ""}`}
                    disabled={submitting === msg.id}
                    onClick={() => handleFeedback(msg, -1)}
                    title="Imprecisa"
                  >
                    -1
                  </button>
                  <button className="glass-button compact" onClick={() => handleCopy(msg.content)}>
                    Copiar
                  </button>
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="typing-indicator">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
            <span>ATHENA esta respondendo...</span>
          </div>
        )}
      </div>

      <div className="chat-input glass-panel">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Digite sua pergunta..."
          maxLength={MAX_QUESTION_CHARS}
          onKeyDown={(e) => {
            const isCtrlEnter = e.key === "Enter" && (e.ctrlKey || e.metaKey);
            if ((e.key === "Enter" && !loading) || isCtrlEnter) onSend();
          }}
        />
        <GlassButton onClick={onSend} disabled={loading || !question.trim() || remaining < 0}>
          {loading ? "Gerando..." : "Enviar"}
        </GlassButton>
        <GlassButton variant="ghost" onClick={handleRefine} disabled={loading}>
          Refinar
        </GlassButton>
        {onRegenerate && (
          <GlassButton variant="ghost" onClick={onRegenerate} disabled={loading}>
            Regenerar
          </GlassButton>
        )}
      </div>
      <p className="muted">Limite: {MAX_QUESTION_CHARS} caracteres. Restantes: {remaining}.</p>
    </section>
  );
}
