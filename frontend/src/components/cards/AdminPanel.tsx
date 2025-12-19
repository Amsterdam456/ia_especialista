import type { User } from "../../types";

type Policy = {
  id: number;
  filename: string;
  stored_path: string;
  uploaded_by: string;
  uploaded_at: string;
  active: boolean;
  embedding_status: string;
  embedding_last_error: string | null;
};

type Props = {
  currentUser: User;
  users: User[];
  policies: Policy[];
};

export function AdminPanel({ currentUser, users, policies }: Props) {
  if (!currentUser.is_admin) return null;

  return (
    <section className="card-glass admin-card">
      <div className="card-title">Painel administrativo</div>

      <div className="grid grid-2">
        <div>
          <p className="overline">Usuarios</p>
          <ul className="list">
            {users.map((u) => (
              <li key={u.id}>
                <span>{u.full_name || u.email}</span>
                <span className="pill">{u.is_admin ? "Admin" : "User"}</span>
              </li>
            ))}
            {users.length === 0 && <li className="muted">Nenhum usuario</li>}
          </ul>
        </div>

        <div>
          <p className="overline">Politicas</p>
          <ul className="list">
            {policies.map((p) => (
              <li key={p.id}>
                <span>{p.filename}</span>
                <span
                  className="pill"
                  style={{
                    background:
                      p.embedding_status === "completed"
                        ? "rgba(34, 211, 238, 0.15)"
                        : "rgba(255, 193, 7, 0.15)",
                    color:
                      p.embedding_status === "completed"
                        ? "#22d3ee"
                        : "#facc15",
                  }}
                >
                  {p.embedding_status}
                </span>
              </li>
            ))}
            {policies.length === 0 && <li className="muted">Nenhum arquivo</li>}
          </ul>
        </div>
      </div>
    </section>
  );
}
