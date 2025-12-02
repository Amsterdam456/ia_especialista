import { useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";

type Props = {
  token: string;
  onClose: (refresh?: boolean) => void;
  userToEdit?: { id: number; email: string; full_name?: string | null; role?: string; is_admin?: boolean };
};

export function UserFormModal({ token, onClose, userToEdit }: Props) {
  const isEdit = Boolean(userToEdit);
  const [email, setEmail] = useState(userToEdit?.email ?? "");
  const [name, setName] = useState(userToEdit?.full_name ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(userToEdit?.role || (userToEdit?.is_admin ? "admin" : "usuario") || "usuario");
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    try {
      if (isEdit && userToEdit) {
        await adminService.updateUser(
          userToEdit.id,
          { email, full_name: name, role, ...(password ? { password } : {}) },
          token
        );
      } else {
        await adminService.createUser({ email, full_name: name, password, role }, token);
      }
      onClose(true);
    } catch (e: any) {
      setError(e.message || "Erro ao salvar usuário");
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h3>{isEdit ? "Editar usuário" : "Novo usuário"}</h3>
        <label>Nome</label>
        <input value={name} onChange={(e) => setName(e.target.value)} className="input-glass" />
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} className="input-glass" />
        <label>{isEdit ? "Nova senha (opcional)" : "Senha"}</label>
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
          className="input-glass"
          placeholder={isEdit ? "Deixe vazio para manter" : ""}
        />
        <label>Cargo</label>
        <select value={role} onChange={(e) => setRole(e.target.value)} className="input-glass">
          <option value="admin">Admin</option>
          <option value="moderador">Moderador</option>
          <option value="usuario">Usuário</option>
        </select>
        {error && <p className="muted">{error}</p>}
        <div className="modal-actions">
          <GlassButton onClick={submit}>{isEdit ? "Salvar" : "Criar"}</GlassButton>
          <GlassButton variant="ghost" onClick={() => onClose()}>
            Cancelar
          </GlassButton>
        </div>
      </div>
    </div>
  );
}
