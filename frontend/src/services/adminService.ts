import { API_URL, request } from "./api";
import type { User, ChatCompletionData, Envelope } from "../types";

const authHeaders = (token?: string) => ({
  Authorization: `Bearer ${token || localStorage.getItem("athena_token") || ""}`,
});

export const adminService = {
  async getUsers(token?: string) {
    return request<User[]>("/admin/users", { headers: authHeaders(token) }, token);
  },
  async createUser(data: { email: string; full_name?: string; password: string; role: string }, token?: string) {
    return request<User>("/admin/users", { method: "POST", body: JSON.stringify(data), headers: authHeaders(token) }, token);
  },
  async updateUser(id: number, data: Partial<User> & { role?: string }, token?: string) {
    return request<User>(`/admin/users/${id}`, { method: "PUT", body: JSON.stringify(data), headers: authHeaders(token) }, token);
  },
  async deleteUser(id: number, token?: string) {
    return request<boolean>(`/admin/users/${id}`, { method: "DELETE", headers: authHeaders(token) }, token);
  },
  async getPolicies(token?: string) {
    return request<any[]>("/admin/policies", { headers: authHeaders(token) }, token);
  },
  async uploadPolicy(file: File, token?: string) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/admin/policies/upload`, {
      method: "POST",
      headers: authHeaders(token),
      body: form,
    });
    const payload = await res.json();
    if (!res.ok || !payload.success) {
      throw new Error(payload.error || "Erro ao enviar política");
    }
    return payload.data;
  },
  async deletePolicy(id: number, token?: string) {
    return request<boolean>(`/admin/policies/${id}`, { method: "DELETE", headers: authHeaders(token) }, token);
  },
  async processPolicies(token?: string, policyId?: number) {
    const form = new FormData();
    if (policyId) form.append("policy_id", String(policyId));
    const res = await fetch(`${API_URL}/admin/policies/process`, {
      method: "POST",
      headers: authHeaders(token),
      body: form,
    });
    const payload = (await res.json()) as Envelope<boolean>;
    if (!res.ok || !payload.success) {
      throw new Error(payload.error || "Erro ao processar políticas");
    }
    return payload.data;
  },
  async getConfig(token?: string) {
    return request<any>("/admin/config", { headers: authHeaders(token) }, token);
  },
  async updateConfig(data: any, token?: string) {
    return request<any>("/admin/config", { method: "PUT", body: JSON.stringify(data), headers: authHeaders(token) }, token);
  },
  async getAuditLogs(token?: string) {
    return request<any[]>("/admin/audit", { headers: authHeaders(token) }, token);
  },
  async getFeedback(token?: string) {
    return request<any[]>("/admin/feedback", { headers: authHeaders(token) }, token);
  },
  async sendFeedbackResponse(data: any, token?: string) {
    return request<ChatCompletionData>("/admin/feedback/respond", { method: "POST", body: JSON.stringify(data), headers: authHeaders(token) }, token);
  },
};
