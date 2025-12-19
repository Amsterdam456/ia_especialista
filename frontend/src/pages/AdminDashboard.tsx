import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { HomeActionCard } from "../components/cards/HomeActionCard";
import { UserTable } from "../components/admin/UserTable";
import { UserFormModal } from "../components/admin/UserFormModal";
import { PolicyTable } from "../components/admin/PolicyTable";
import { AdminConfigPanel } from "../components/admin/AdminConfigPanel";
import { AuditTable } from "../components/admin/AuditTable";
import { FeedbackTable } from "../components/admin/FeedbackTable";
import { Shell } from "../components/layout/Shell";
import { GlassButton } from "../components/buttons/GlassButton";
import type { User } from "../types";

type Props = {
  user: User;
  token: string;
  onBack: () => void;
  onLogout: () => void;
};

type Section = "users" | "policies" | "config" | "audit" | "feedback";

export default function AdminDashboard({ user, token, onBack, onLogout }: Props) {
  const [section, setSection] = useState<Section>("users");
  const [showUserModal, setShowUserModal] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const [refreshUsersKey, setRefreshUsersKey] = useState(0);

  useEffect(() => {
    const isAdmin = user.is_admin || user.role === "admin";
    if (!isAdmin) onBack();
  }, [user, onBack]);

  useEffect(() => {
    if (location.pathname.startsWith("/admin/policies")) setSection("policies");
    else if (location.pathname.startsWith("/admin/config")) setSection("config");
    else if (location.pathname.startsWith("/admin/audit")) setSection("audit");
    else if (location.pathname.startsWith("/admin/feedback")) setSection("feedback");
    else setSection("users");
  }, [location.pathname]);

  const go = (path: string, sec: Section) => {
    setSection(sec);
    navigate(path);
  };

  return (
    <Shell
      sidebar={
        <aside className="sidebar">
          <div className="sidebar-brand">
            <div className="logo">ATHENA</div>
            <div className="badge">Admin</div>
          </div>
          <div className="sidebar-list">
            <button className={`chat-pill ${section === "users" ? "active" : ""}`} onClick={() => go("/admin/users", "users")}>
              Usuarios
            </button>
            <button className={`chat-pill ${section === "policies" ? "active" : ""}`} onClick={() => go("/admin/policies", "policies")}>
              Politicas
            </button>
            <button className={`chat-pill ${section === "config" ? "active" : ""}`} onClick={() => go("/admin/config", "config")}>
              Configuracoes
            </button>
            <button className={`chat-pill ${section === "audit" ? "active" : ""}`} onClick={() => go("/admin/audit", "audit")}>
              Auditoria
            </button>
            <button className={`chat-pill ${section === "feedback" ? "active" : ""}`} onClick={() => go("/admin/feedback", "feedback")}>
              Feedback IA
            </button>
          </div>
          <GlassButton variant="ghost" onClick={onBack} className="w-full">Voltar</GlassButton>
          <GlassButton variant="ghost" onClick={onLogout} className="w-full">Sair</GlassButton>
        </aside>
      }
    >
      {section === "users" && (
        <>
          <HomeActionCard
            title="Usuarios"
            subtitle="Gerencie contas e papeis"
            description="Criar, editar e desativar usuarios."
            primary
            onClick={() => setShowUserModal(true)}
          />
          <UserTable token={token} onCreate={() => setShowUserModal(true)} refreshKey={refreshUsersKey} />
          {showUserModal && (
            <UserFormModal
              token={token}
              onClose={(refresh) => {
                setShowUserModal(false);
                if (refresh) setRefreshUsersKey((k) => k + 1);
              }}
            />
          )}
        </>
      )}
      {section === "policies" && <PolicyTable token={token} />}
      {section === "config" && <AdminConfigPanel token={token} />}
      {section === "audit" && <AuditTable token={token} />}
      {section === "feedback" && <FeedbackTable token={token} />}
    </Shell>
  );
}
