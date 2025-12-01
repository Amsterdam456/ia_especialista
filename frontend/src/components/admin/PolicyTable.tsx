import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";

type Props = {
  token: string;
};

export function PolicyTable({ token }: Props) {
  const [policies, setPolicies] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);

  const load = () => adminService.getPolicies(token).then(setPolicies).catch(console.error);

  useEffect(() => {
    load();
  }, [token]);

  const upload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      await adminService.uploadPolicy(file, token);
      setFile(null);
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const process = async () => {
    setLoading(true);
    try {
      await adminService.processPolicies(token, selected || undefined);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-glass">
      <div className="card-title">Políticas</div>
      <div className="upload-area">
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <GlassButton onClick={upload} disabled={!file || loading}>Enviar política</GlassButton>
        <GlassButton variant="ghost" onClick={process} disabled={loading}>Processar políticas</GlassButton>
      </div>
      <table className="admin-table">
        <thead>
          <tr>
            <th></th>
            <th>Nome</th>
            <th>Upload</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {policies.map((p) => (
            <tr key={p.id || p.filename}>
              <td>
                <input type="radio" name="policy" checked={selected === p.id} onChange={() => setSelected(p.id)} />
              </td>
              <td>{p.filename || p}</td>
              <td>{p.uploaded_at ? new Date(p.uploaded_at).toLocaleString() : "-"}</td>
              <td>{p.embedding_status || "pendente"}</td>
              <td>
                <GlassButton variant="ghost" onClick={() => adminService.deletePolicy(p.id, token).then(load)}>
                  Remover
                </GlassButton>
              </td>
            </tr>
          ))}
          {policies.length === 0 && (
            <tr>
              <td colSpan={5}>Nenhuma política</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
