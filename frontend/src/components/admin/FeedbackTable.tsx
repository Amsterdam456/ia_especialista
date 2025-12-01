import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";

type Props = {
  token: string;
};

export function FeedbackTable({ token }: Props) {
  const [feedback, setFeedback] = useState<any[]>([]);

  useEffect(() => {
    adminService.getFeedback(token).then(setFeedback).catch(console.error);
  }, [token]);

  return (
    <div className="card-glass">
      <div className="card-title">Feedback IA</div>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Usuário</th>
            <th>Mensagem</th>
            <th>Avaliação</th>
            <th>Comentário</th>
          </tr>
        </thead>
        <tbody>
          {feedback.map((f) => (
            <tr key={f.id}>
              <td>{f.user_id}</td>
              <td>{f.message_id}</td>
              <td>{f.rating ?? f.rating_up_down ?? "-"}</td>
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
    </div>
  );
}
