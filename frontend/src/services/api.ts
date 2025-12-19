import type {
  Chat,
  ChatCompletionData,
  Envelope,
  Message,
  User,
} from "../types";

const sanitizeUrl = (url: string | undefined | null) =>
  url?.trim().replace(/\/$/, "");

export const API_ROOT =
  sanitizeUrl(import.meta.env.VITE_API_URL) ||
  (typeof window !== "undefined"
    ? sanitizeUrl(window.location.origin)
    : undefined) ||
  "http://localhost:8000";

export const API_URL = `${API_ROOT}/api/v1`;

const jsonHeaders = (token?: string) => ({
  "Content-Type": "application/json",
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});

// Funcao generica para endpoints que seguem o Envelope
export async function request<T>(
  path: string,
  options?: RequestInit,
  token?: string
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...jsonHeaders(token),
      ...(options?.headers || {}),
    },
  });

  const payload = (await res.json()) as Envelope<T>;

  if (!res.ok || !payload.success) {
    throw new Error(payload.error || "Erro de requisicao");
  }

  return payload.data;
}

// =====================
// AUTH
// =====================

// LOGIN NAO USA Envelope! Backend retorna { access_token, user }
export async function login(email: string, password: string) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ email, password }),
  });

  const payload = (await res.json()) as {
    success: boolean;
    data: {
      user: User;
      token: { access_token: string; token_type: string };
    } | null;
    error: string | null;
  };

  if (!res.ok || !payload.success || !payload.data) {
    throw new Error(payload?.error || "Login falhou");
  }

  const { user, token } = payload.data;

  return {
    access_token: token.access_token,
    token_type: token.token_type,
    user,
  };
}

export async function register(email: string, password: string, full_name?: string) {
  return request<User>(
    "/auth/register",
    {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    },
    undefined
  );
}

export async function getMe(token: string) {
  return request<User>("/auth/me", undefined, token);
}

export async function changePassword(token: string, old_password: string | null, new_password: string) {
  return request<boolean>(
    "/auth/change-password",
    {
      method: "POST",
      body: JSON.stringify({ old_password, new_password }),
    },
    token
  );
}

// =====================
// CHATS
// =====================

export async function getChats(token: string) {
  return request<Chat[]>("/chats", undefined, token);
}

export async function createChat(token: string, title: string) {
  return request<Chat>(
    "/chats",
    {
      method: "POST",
      body: JSON.stringify({ title }),
    },
    token
  );
}

export async function getMessages(token: string, chatId: number) {
  return request<Message[]>(`/chats/${chatId}/messages`, undefined, token);
}

export async function ask(token: string, chatId: number, question: string) {
  return request<ChatCompletionData>(
    `/chats/${chatId}/ask`,
    {
      method: "POST",
      body: JSON.stringify({ question }),
    },
    token
  );
}

export async function askStream(token: string, chatId: number, question: string) {
  return fetch(`${API_URL}/chats/${chatId}/ask/stream`, {
    method: "POST",
    headers: jsonHeaders(token),
    body: JSON.stringify({ question }),
  });
}

export async function sendFeedback(token: string, chatId: number, messageId: number, rating: number, comment?: string) {
  return request<boolean>(
    `/chats/${chatId}/feedback`,
    {
      method: "POST",
      body: JSON.stringify({ message_id: messageId, rating, comment }),
    },
    token
  );
}

export async function renameChat(token: string, chatId: number, title: string) {
  return request<Chat>(`/chats/${chatId}`, { method: "PUT", body: JSON.stringify({ title }) }, token);
}

export async function deleteChat(token: string, chatId: number) {
  return request<boolean>(`/chats/${chatId}`, { method: "DELETE" }, token);
}

// =====================
// ADMIN
// =====================

export async function getAdminUsers(token: string) {
  return request<User[]>("/admin/users", undefined, token);
}

export async function getPolicies(token: string) {
  return request<any[]>("/admin/policies", undefined, token);
}

// =====================
// ATHENA
// =====================
