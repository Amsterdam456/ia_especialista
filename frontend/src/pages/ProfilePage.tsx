import { useState } from "react";
import { Shell } from "../components/layout/Shell";
import { GlassButton } from "../components/buttons/GlassButton";
import type { User } from "../types";
import { changePassword } from "../services/api";

type Props = {
  user: User;
  token: string;
  onBack: () => void;
  onLogout: () => void;
};

const MIN_PASSWORD_LEN = 8;

export default function ProfilePage({ user, token, onBack, onLogout }: Props) {
  const [oldPass, setOldPass] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirm, setConfirm] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (newPass.length < MIN_PASSWORD_LEN) {
      setStatus(`Senha precisa ter no minimo ${MIN_PASSWORD_LEN} caracteres.`);
      return;
    }
    if (newPass !== confirm) {
      setStatus("As senhas nao conferem.");
      return;
    }
    setSaving(true);
    try {
      await changePassword(token, oldPass || null, newPass);
      setStatus("Senha atualizada com sucesso.");
      setOldPass("");
      setNewPass("");
      setConfirm("");
    } catch (err) {
      console.error(err);
      setStatus("Erro ao atualizar senha.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Shell sidebar={null}>
      <div className="card-glass profile-card">
        <h2>Meu perfil</h2>
        <p className="muted">{user.email}</p>
        <div className="grid-2">
          <div>
            <label>Nome</label>
            <input className="input-glass" value={user.full_name || ""} disabled />
          </div>
          <div>
            <label>Funcao</label>
            <input className="input-glass" value={user.role || (user.is_admin ? "admin" : "usuario")} disabled />
          </div>
        </div>
        <div className="divider" />
        <h3>Redefinir senha</h3>
        <label>Senha atual</label>
        <input className="input-glass" type="password" value={oldPass} onChange={(e) => setOldPass(e.target.value)} />
        <label>Nova senha</label>
        <input className="input-glass" type="password" value={newPass} onChange={(e) => setNewPass(e.target.value)} />
        <label>Confirmar nova senha</label>
        <input className="input-glass" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        <p className="muted">Use ao menos {MIN_PASSWORD_LEN} caracteres.</p>
        {status && <p className="muted">{status}</p>}
        <div className="modal-actions">
          <GlassButton onClick={handleSave} disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </GlassButton>
          <GlassButton variant="ghost" onClick={onBack}>
            Voltar
          </GlassButton>
          <GlassButton variant="ghost" onClick={onLogout}>
            Sair
          </GlassButton>
        </div>
      </div>
    </Shell>
  );
}
