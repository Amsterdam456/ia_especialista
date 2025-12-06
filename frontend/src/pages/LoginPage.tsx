import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import bg from "../assets/bg_athena.jpg";
import { GlassButton } from "../components/buttons/GlassButton";
import { login } from "../services/api";
import type { User } from "../types";

type Props = {
  onLoginSuccess: (token: string, user: User) => void;
};

export default function LoginPage({ onLoginSuccess }: Props) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@athena.com");
  const [password, setPassword] = useState("123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await login(email, password);
      localStorage.setItem("athena_token", data.access_token);
      onLoginSuccess(data.access_token, data.user as User);
      navigate("/home");
    } catch (err: any) {
      setError(err.message || "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell" style={{ backgroundImage: `url(${bg})` }}>
      <div className="login-card glass-surface">
        <p className="overline">ATHENA • Acesso seguro</p>
        <h1>Entrar no painel</h1>
        <p className="subtitle">
          Use suas credenciais institucionais para acessar os chats e dashboards.
        </p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>E-mail</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />

          <label>Senha</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />

          <GlassButton type="submit" disabled={loading}>
            {loading ? "Entrando..." : "Entrar"}
          </GlassButton>
        </form>

        {error && <div className="alert">{error}</div>}
      </div>
    </div>
  );
}
