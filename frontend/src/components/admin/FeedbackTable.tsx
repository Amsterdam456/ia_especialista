import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";

type Props = {
  token: string;
};

export function FeedbackTable({ token }: Props) {
  const [directives, setDirectives] = useState<any[]>([]);
  const [feedback, setFeedback] = useState<any[]>([]);

  const refresh = async () => {
    const [dirData, fbData] = await Promise.all([
      adminService.getFeedbackDirectives(token),
      adminService.getFeedback(token),
    ]);
    setDirectives(dirData);
    setFeedback(fbData);
  };

  useEffect(() => {
    refresh().catch(console.error);
  }, [token]);

  const handleApprove = async (directive: any) => {
    const text = window.prompt("Texto aprovado para a IA:", directive.text || "");
    if (!text) return;
    try {
      await adminService.approveFeedbackDirective(directive.id, { text }, token);
      await refresh();
    } catch (err) {
      console.error(err);
      alert("Erro ao aprovar diretriz");
    }
  };

  const handleReject = async (directive: any) => {
    const ok = window.confirm("Rejeitar esta diretriz?");
    if (!ok) return;
    try {
      await adminService.rejectFeedbackDirective(directive.id, token);
      await refresh();
    } catch (err) {
      console.error(err);
      alert("Erro ao rejeitar diretriz");
    }
  };

  const pending = directives.filter((d) => d.status === "pending");
  const history = directives.filter((d) => d.status !== "pending");

  return (
    <div className="card-glass">
      <div className="card-title">Feedback IA</div>

      <h3>Diretrizes pendentes</h3>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Mensagem</th>
            <th>Avaliacao</th>
            <th>Texto</th>
            <th>Acoes</th>
          </tr>
        </thead>
        <tbody>
          {pending.map((d) => (
            <tr key={d.id}>
              <td>{d.created_by_email || d.created_by}</td>
              <td>{d.message_id}</td>
              <td>{d.rating ?? "-"}</td>
              <td>{d.text}</td>
              <td className="actions">
                <GlassButton variant="ghost" onClick={() => handleApprove(d)}>
                  Aprovar
                </GlassButton>
                <GlassButton variant="ghost" onClick={() => handleReject(d)}>
                  Rejeitar
                </GlassButton>
              </td>
            </tr>
          ))}
          {pending.length === 0 && (
            <tr>
              <td colSpan={5}>Nenhuma diretriz pendente</td>
            </tr>
          )}
        </tbody>
      </table>

      <h3>Historico de feedback</h3>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Mensagem</th>
            <th>Avaliacao</th>
            <th>Comentario</th>
          </tr>
        </thead>
        <tbody>
          {feedback.map((f) => (
            <tr key={f.id}>
              <td>{f.user_id}</td>
              <td>{f.message_id}</td>
              <td>{f.rating ?? "-"}</td>
              <td>{f.comment || "-"}</td>
            </tr>
          ))}
          {feedback.length === 0 && (
            <tr>
              <td colSpan={4}>Nenhum feedback</td>
            </tr>
          )}
        </tbody>
      </table>

      <h3>Historico de diretrizes</h3>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Status</th>
            <th>Texto</th>
            <th>Aplicado em</th>
          </tr>
        </thead>
        <tbody>
          {history.map((d) => (
            <tr key={d.id}>
              <td>{d.created_by_email || d.created_by}</td>
              <td>{d.status}</td>
              <td>{d.text}</td>
              <td>{d.applied_at ? new Date(d.applied_at).toLocaleString() : "-"}</td>
            </tr>
          ))}
          {history.length === 0 && (
            <tr>
              <td colSpan={4}>Nenhuma diretriz aplicada ou rejeitada</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
