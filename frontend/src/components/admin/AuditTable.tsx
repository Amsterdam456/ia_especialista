import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";

type Props = {
  token: string;
};

export function AuditTable({ token }: Props) {
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    adminService.getAuditLogs(token).then(setLogs).catch(console.error);
  }, [token]);

  return (
    <div className="card-glass">
      <div className="card-title">Auditoria</div>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Usuário</th>
            <th>Ação</th>
            <th>Meta</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((l) => (
            <tr key={l.id}>
              <td>{l.user_id}</td>
              <td>{l.action}</td>
              <td>{l.meta ? JSON.stringify(l.meta) : "-"}</td>
              <td>{l.created_at ? new Date(l.created_at).toLocaleString() : "-"}</td>
            </tr>
          ))}
          {logs.length === 0 && (
            <tr>
              <td colSpan={4}>Nenhum registro</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
