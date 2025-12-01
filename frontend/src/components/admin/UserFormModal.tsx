import { useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";

type Props = {
  token: string;
  onClose: (refresh?: boolean) => void;
};

export function UserFormModal({ token, onClose }: Props) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("usuario");
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    try {
      await adminService.createUser({ email, full_name: name, password, role }, token);
      onClose(true);
    } catch (e: any) {
      setError(e.message || "Erro ao criar usuário");
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h3>Novo usuário</h3>
        <label>Nome</label>
        <input value={name} onChange={(e) => setName(e.target.value)} className="input-glass" />
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} className="input-glass" />
        <label>Senha</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" className="input-glass" />
        <label>Cargo</label>
        <select value={role} onChange={(e) => setRole(e.target.value)} className="input-glass">
          <option value="admin">Admin</option>
          <option value="moderador">Moderador</option>
          <option value="usuario">Usuário</option>
        </select>
        {error && <p className="muted">{error}</p>}
        <div className="modal-actions">
          <GlassButton onClick={submit}>Criar</GlassButton>
          <GlassButton variant="ghost" onClick={() => onClose()}>Cancelar</GlassButton>
        </div>
      </div>
    </div>
  );
}
