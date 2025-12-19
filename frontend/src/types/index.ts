export type Envelope<T> = {
  success: boolean;
  data: T;
  error: string | null;
};

export type Token = {
  access_token: string;
  token_type: string;
};

export type User = {
  id: number;
  email: string;
  full_name?: string | null;
  is_admin: boolean;
  is_active?: boolean;
  created_at: string;
  role?: "admin" | "moderador" | "usuario";
};

export type AuthResponse = {
  user: User;
  token: Token;
};

export type Chat = {
  id: number;
  title: string;
  created_at: string;
};

export type Message = {
  id: number;
  chat_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type AskResponse = {
  answer: string;
  meta?: Record<string, unknown>;
};

export * from "./chat";
