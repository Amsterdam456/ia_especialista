import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";
import type { User } from "../../types";

type Props = {
  token: string;
  onCreate: () => void;
  refreshKey?: number;
};

export function UserTable({ token, onCreate, refreshKey = 0 }: Props) {
  const [users, setUsers] = useState<User[]>([]);

  const load = () => adminService.getUsers(token).then(setUsers).catch(console.error);

  useEffect(() => {
    load();
  }, [token, refreshKey]);

  return (
    <div className="card-glass">
      <div className="card-title">Usuários</div>
      <GlassButton className="mb-2" onClick={onCreate}>+ Novo usuário</GlassButton>
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
                <GlassButton variant="ghost" onClick={() => {}}>Editar</GlassButton>
                <GlassButton variant="ghost" onClick={() => {}}>Resetar senha</GlassButton>
                <GlassButton variant="ghost" onClick={() => adminService.deleteUser(u.id, token).then(load)}>Desativar</GlassButton>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
