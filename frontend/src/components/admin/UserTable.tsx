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

type BulkResult = {
  created: number;
  errors: string[];
  temp_passwords?: { email: string; password: string }[];
};

export function UserTable({ token, onCreate, refreshKey = 0 }: Props) {
  const [users, setUsers] = useState<User[]>([]);
  const [bulkResult, setBulkResult] = useState<BulkResult | null>(null);
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

  const toggleActive = async (user: User) => {
    try {
      setLoadingAction(true);
      await adminService.updateUser(user.id, { is_active: !user.is_active }, token);
      load();
    } catch (err) {
      console.error(err);
      setToast("Erro ao atualizar status.");
    } finally {
      setLoadingAction(false);
      setTimeout(() => setToast(null), 3500);
    }
  };

  return (
    <div className="card-glass">
      <div className="card-title">Usuarios</div>
      <GlassButton
        onClick={() => {
          setEditingUser(null);
          setShowModal(true);
          onCreate();
        }}
      >
        + Novo usuario
      </GlassButton>
      <div className="upload-area">
        <input type="file" accept=".csv" onChange={(e) => setBulkFile(e.target.files?.[0] || null)} />
        <GlassButton variant="ghost" onClick={uploadBulk} disabled={!bulkFile}>
          Criar usuarios em lote
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
          Criados: {bulkResult.created}
          {bulkResult.errors.length ? ` | Erros: ${bulkResult.errors.join(", ")}` : ""}
          {bulkResult.temp_passwords?.length ? " | Senhas temporarias geradas." : ""}
        </div>
      )}
      {bulkResult?.temp_passwords?.length ? (
        <div className="muted">
          {bulkResult.temp_passwords.map((item) => (
            <div key={item.email}>
              {item.email}: {item.password}
            </div>
          ))}
        </div>
      ) : null}
      <table className="admin-table">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Email</th>
            <th>Cargo</th>
            <th>Status</th>
            <th>Acoes</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.full_name || "-"}</td>
              <td>{u.email}</td>
              <td>{u.role || (u.is_admin ? "admin" : "usuario")}</td>
              <td>{u.is_active ? "Ativo" : "Inativo"}</td>
              <td className="actions">
                <GlassButton variant="ghost" onClick={() => handleEdit(u)}>
                  Editar
                </GlassButton>
                <GlassButton variant="ghost" onClick={() => handleResetPassword(u)}>
                  Resetar senha
                </GlassButton>
                <GlassButton
                  variant="ghost"
                  onClick={() => toggleActive(u)}
                >
                  {u.is_active ? "Desativar" : "Ativar"}
                </GlassButton>
                <GlassButton
                  variant="ghost"
                  onClick={async () => {
                    const ok = window.confirm("Excluir usuario definitivamente?");
                    if (!ok) return;
                    setLoadingAction(true);
                    await adminService.deleteUser(u.id, token);
                    setLoadingAction(false);
                    load();
                  }}
                >
                  Excluir
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
