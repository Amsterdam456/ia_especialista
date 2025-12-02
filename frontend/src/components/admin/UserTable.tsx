import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";
import { UserFormModal } from "./UserFormModal";
import type { User } from "../../types";

type Props = {
  token: string;
  onCreate: () => void;
  refreshKey?: number;
};

export function UserTable({ token, onCreate, refreshKey = 0 }: Props) {
  const [users, setUsers] = useState<User[]>([]);
  const [bulkResult, setBulkResult] = useState<{ created: number; errors: string[] } | null>(null);
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState(false);

  const load = () => adminService.getUsers(token).then(setUsers).catch(console.error);

  useEffect(() => {
    load();
  }, [token, refreshKey]);

  const uploadBulk = async () => {
    if (!bulkFile) return;
    try {
      const result = await adminService.uploadUsersBulk(bulkFile, token);
      setBulkResult(result);
      setBulkFile(null);
      load();
    } catch (e) {
      console.error(e);
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setShowModal(true);
  };

  const handleResetPassword = async (user: User) => {
    const newPass = window.prompt(`Nova senha para ${user.email}:`, "");
    if (!newPass) return;
    try {
      setLoadingAction(true);
      await adminService.resetPassword(user.id, newPass, token);
      setToast("Senha redefinida com sucesso.");
    } catch (err) {
      console.error(err);
      setToast("Erro ao redefinir senha.");
    } finally {
      setLoadingAction(false);
      setTimeout(() => setToast(null), 3500);
    }
  };

  return (
    <div className="card-glass">
      <div className="card-title">Usuários</div>
      <GlassButton
        className="mb-2"
        onClick={() => {
          setEditingUser(null);
          setShowModal(true);
          onCreate();
        }}
      >
        + Novo usuário
      </GlassButton>
      <div className="upload-area">
        <input type="file" accept=".csv,.xlsx" onChange={(e) => setBulkFile(e.target.files?.[0] || null)} />
        <GlassButton variant="ghost" onClick={uploadBulk} disabled={!bulkFile}>
          Criar usuários em lote
        </GlassButton>
        <a
          href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/admin/users/template`}
          className="muted"
          target="_blank"
          rel="noreferrer"
        >
          Baixar template
        </a>
      </div>
      {bulkResult && (
        <div className="muted">
          Criados: {bulkResult.created} {bulkResult.errors.length ? ` | Erros: ${bulkResult.errors.join(", ")}` : ""}
        </div>
      )}
      <table className="admin-table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Email</th>
            <th>Cargo</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.full_name || "-"}</td>
              <td>{u.email}</td>
              <td>{u.role || (u.is_admin ? "admin" : "usuario")}</td>
              <td>Ativo</td>
              <td className="actions">
                <GlassButton variant="ghost" onClick={() => handleEdit(u)}>
                  Editar
                </GlassButton>
                <GlassButton variant="ghost" onClick={() => handleResetPassword(u)}>
                  Resetar senha
                </GlassButton>
                <GlassButton
                  variant="ghost"
                  onClick={async () => {
                    setLoadingAction(true);
                    await adminService.deleteUser(u.id, token);
                    setLoadingAction(false);
                    load();
                  }}
                >
                  Desativar
                </GlassButton>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {toast && <div className="toast">{toast}</div>}
      {loadingAction && <div className="muted">Processando...</div>}
      {showModal && (
        <UserFormModal
          token={token}
          userToEdit={editingUser || undefined}
          onClose={(refresh) => {
            setShowModal(false);
            setEditingUser(null);
            if (refresh) load();
          }}
        />
      )}
    </div>
  );
}
