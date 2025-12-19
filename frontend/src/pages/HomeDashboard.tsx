import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { GlassButton } from "../components/buttons/GlassButton";
import { HomeActionCard } from "../components/cards/HomeActionCard";
import { InfoCard } from "../components/cards/InfoCard";
import { AdminPanel } from "../components/cards/AdminPanel";
import { Shell } from "../components/layout/Shell";
import { Sidebar } from "../components/sidebar/Sidebar";
import { getAdminUsers, getPolicies, createChat } from "../services/api";
import { adminService } from "../services/adminService";
import type { User } from "../types";

type Props = {
  user: User;
  token: string;
  onLogout: () => void;
  onOpenChat: (route?: string) => void;
};

const highlights = [
  { title: "ATHENA IA", description: "Assistente especialista treinada com dados internos para responder e apoiar decisoes.", tag: "IA Especialista", icon: "AI" },
  { title: "Neural Map", description: "Mapa inteligente que cruza mercado, captacao e evasao para revelar oportunidades.", tag: "Mapa Estrategico", icon: "MAP" },
  { title: "Athena OPS", description: "Digital twin operacional: simula cenarios e impactos em ROL.", tag: "Digital Twin", icon: "OPS" },
  { title: "Athena DNA", description: "Sistema de riscos com score por nucleo para sinais precoces.", tag: "Gestao de Riscos", icon: "DNA" },
  { title: "Pivot", description: "Visoes financeiras consolidadas para IA e painel pivot.", tag: "Financeiro", icon: "PVT" },
];

export default function HomeDashboard({ user, token, onLogout, onOpenChat }: Props) {
  const [adminUsers, setAdminUsers] = useState<User[]>([]);
  const [policies, setPolicies] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any | null>(null);
  const navigate = useNavigate();

  const handleNewChat = async () => {
    try {
      const chat = await createChat(token, "Nova conversa");
      onOpenChat(`/chat/${chat.id}`);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        if (user.is_admin || user.role === "admin") {
          const [users, pol, mtx] = await Promise.all([
            getAdminUsers(token),
            getPolicies(token),
            adminService.getMetrics(token),
          ]);
          setAdminUsers(users);
          setPolicies(pol as any);
          setMetrics(mtx);
        }
      } catch (e) {
        console.error(e);
      }
    };
    init();
  }, [token, user.is_admin, user.role]);

  return (
    <Shell
      sidebar={
        <Sidebar
          user={user}
          chats={[]}
          selectedChatId={null}
          onSelectChat={() => undefined}
          onNewChat={handleNewChat}
          onLogout={onLogout}
          adminUsersCount={adminUsers.length}
          policiesCount={policies.length}
          showChats={false}
          showMetrics={false}
        />
      }
    >
      <header className="hero">
        <div>
          <p className="overline">ATHENA - IA Corporativa Estacio</p>
          <h1>Inteligencia aplicada a decisoes reais</h1>
          <p className="subtitle">
            Plataforma proprietaria de IA, simulacao e diagnostico que conecta resultados financeiros,
            captacao, evasao e operacao academica.
          </p>
          <div className="hero-actions">
            <GlassButton onClick={handleNewChat}>Nova conversa</GlassButton>
            <GlassButton variant="ghost" onClick={() => navigate("/profile")}>
              Meu perfil
            </GlassButton>
            <GlassButton variant="ghost" onClick={onLogout}>
              Sair
            </GlassButton>
          </div>
        </div>
      </header>

      <section className="card-grid">
        <HomeActionCard
          title="IA Especialista"
          subtitle="ATHENA IA"
          description="Converse com a IA oficial e obtenha respostas baseadas nas politicas Estacio."
          primary
          onClick={() => onOpenChat("/chat")}
          icon="AI"
        />
        {(user.is_admin || user.role === "admin") && (
          <HomeActionCard
            title="Administracao do Sistema"
            subtitle="Gerenciar usuarios, politicas e configuracoes"
            description="Acesse o painel administrativo."
            primary
            onClick={() => navigate("/admin")}
            icon="ADM"
          />
        )}
        {highlights.map((item) => (
          <HomeActionCard
            key={item.title}
            title={item.title}
            subtitle={item.tag}
            description={item.description}
            icon={item.icon}
            disabled={item.title !== "Pivot"}
            onClick={item.title === "Pivot" ? () => navigate("/pivot") : undefined}
          />
        ))}
      </section>

      <section className="info-panels">
        <InfoCard title="Politicas carregadas" description={`Total: ${policies.length || 0}`} tag="Politicas" />
        <InfoCard title="Status do modelo" description="Modelo atual: LM Studio" tag="Conexao: OK" />
        {metrics && (
          <InfoCard
            title="Indicadores"
            description={`Usuarios: ${metrics.users} | Chats: ${metrics.chats} | Mensagens: ${metrics.messages}`}
            tag={`Pendencias: ${metrics.directives_pending || 0}`}
          />
        )}
      </section>

      {(user.is_admin || user.role === "admin") && <AdminPanel currentUser={user} users={adminUsers} policies={policies} />}
    </Shell>
  );
}
