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
  async updateUser(id: number, data: Partial<User> & { role?: string; password?: string }, token?: string) {
    return request<User>(`/admin/users/${id}`, { method: "PUT", body: JSON.stringify(data), headers: authHeaders(token) }, token);
  },
  async resetPassword(id: number, newPassword: string, token?: string) {
    return request<User>(
      `/admin/users/${id}`,
      { method: "PUT", body: JSON.stringify({ password: newPassword }), headers: authHeaders(token) },
      token
    );
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
      throw new Error(payload.error || "Erro ao enviar politica");
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
      throw new Error(payload.error || "Erro ao processar politicas");
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
  async getMetrics(token?: string) {
    return request<any>("/admin/metrics", { headers: authHeaders(token) }, token);
  },
  async exportAuditCsv(token?: string) {
    const res = await fetch(`${API_URL}/admin/audit/export`, { headers: authHeaders(token) });
    if (!res.ok) {
      throw new Error("Erro ao exportar auditoria");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "audit.csv";
    a.click();
    URL.revokeObjectURL(url);
  },
  async getFeedback(token?: string) {
    return request<any[]>("/admin/feedback", { headers: authHeaders(token) }, token);
  },
  async getFeedbackDirectives(token?: string) {
    return request<any[]>("/admin/feedback/directives", { headers: authHeaders(token) }, token);
  },
  async sendFeedbackResponse(data: any, token?: string) {
    return request<ChatCompletionData>("/admin/feedback/respond", { method: "POST", body: JSON.stringify(data), headers: authHeaders(token) }, token);
  },
  async approveFeedbackDirective(id: number, data: { text?: string }, token?: string) {
    return request<boolean>(
      `/admin/feedback/directives/${id}/approve`,
      { method: "POST", body: JSON.stringify(data), headers: authHeaders(token) },
      token
    );
  },
  async rejectFeedbackDirective(id: number, token?: string) {
    return request<boolean>(
      `/admin/feedback/directives/${id}/reject`,
      { method: "POST", headers: authHeaders(token) },
      token
    );
  },
  async uploadUsersBulk(file: File, token?: string) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/admin/users/bulk`, {
      method: "POST",
      headers: authHeaders(token),
      body: form,
    });
    const payload = (await res.json()) as Envelope<{ created: number; errors: string[]; temp_passwords?: { email: string; password: string }[] }>;
    if (!res.ok || !payload.success) {
      throw new Error(payload.error || "Erro ao criar usuarios em lote");
    }
    return payload.data;
  },
  async getPivot(token?: string, params?: { cenario?: string; ano?: string }) {
    const search = new URLSearchParams();
    if (params?.cenario) search.append("cenario", params.cenario);
    if (params?.ano) search.append("ano", params.ano);
    const qs = search.toString() ? `?${search.toString()}` : "";
    return request<any>(`/admin/finance/pivot${qs}`, { headers: authHeaders(token) }, token);
  },
  async uploadFinanceCsv(file: File, token?: string) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/admin/finance/upload`, {
      method: "POST",
      headers: authHeaders(token),
      body: form,
    });
    const payload = (await res.json()) as Envelope<boolean>;
    if (!res.ok || !payload.success) {
      throw new Error(payload.error || "Erro ao enviar CSV financeiro");
    }
    return payload.data;
  },
};
