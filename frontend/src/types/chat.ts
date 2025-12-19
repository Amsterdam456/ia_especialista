export type ChatRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  sources?: { source: string; page: number; score?: number }[];
};

export type ChatCompletionData = {
  id: string;
  content: string;
  raw: unknown;
  sources?: { source: string; page: number; score?: number }[];
  message?: {
    id: number;
    chat_id: number;
    role: ChatRole;
    content: string;
    created_at: string;
    sources?: { source: string; page: number; score?: number }[];
  };
};
