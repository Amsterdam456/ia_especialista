export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
};

export type ChatCompletionData = {
  id: string;
  content: string;
  raw: unknown;
  message?: {
    id: number;
    chat_id: number;
    role: ChatRole;
    content: string;
    created_at: string;
  };
};
