import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import bg from "../assets/bg_athena.jpg";
import { GlassButton } from "../components/buttons/GlassButton";
import { HomeActionCard } from "../components/cards/HomeActionCard";
import { InfoCard } from "../components/cards/InfoCard";
import { AdminPanel } from "../components/cards/AdminPanel";
import { Shell } from "../components/layout/Shell";
import { Sidebar } from "../components/sidebar/Sidebar";
import { getAdminUsers, getPolicies, createChat } from "../services/api";
import type { User } from "../types";

type Props = {
  user: User;
  token: string;
  onLogout: () => void;
  onOpenChat: (route?: string) => void;
};

const highlights = [
  { title: "ATHENA IA", description: "Assistente especialista treinada com dados internos para responder e apoiar decisões.", tag: "IA Especialista", icon: "🤖" },
  { title: "Neural Map", description: "Mapa inteligente que cruza mercado, captação e evasão para revelar oportunidades.", tag: "Mapa Estratégico", icon: "🧭" },
  { title: "Athena OPS", description: "Digital twin operacional: simula cenários e impactos em ROL.", tag: "Digital Twin", icon: "🛰️" },
  { title: "Athena DNA", description: "Sistema de riscos com score por núcleo para sinais precoces.", tag: "Gestão de Riscos", icon: "🧬" },
  { title: "Forecast 360", description: "Previsões financeiras, comerciais e acadêmicas em um único painel.", tag: "Previsão", icon: "📈" },
  { title: "Athena Oracle", description: "Gera planos e responde perguntas complexas com contexto interno.", tag: "Planejamento", icon: "🔮" },
];

export default function HomeDashboard({ user, token, onLogout, onOpenChat }: Props) {
  const [adminUsers, setAdminUsers] = useState<User[]>([]);
  const [policies, setPolicies] = useState<string[]>([]);
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
          const [users, pol] = await Promise.all([getAdminUsers(token), getPolicies(token)]);
          setAdminUsers(users);
          setPolicies(pol as any);
        }
      } catch (e) {
        console.error(e);
      }
    };
    init();
  }, [token, user.is_admin, user.role]);

  return (
    <Shell
      background={bg}
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
          <p className="overline">ATHENA • IA Corporativa Estácio</p>
          <h1>Inteligência aplicada a decisões reais</h1>
          <p className="subtitle">
            Plataforma proprietária de IA, simulação e diagnóstico que conecta resultados financeiros,
            captação, evasão e operação acadêmica.
          </p>
          <div className="hero-actions">
            <GlassButton onClick={handleNewChat}>Nova conversa</GlassButton>
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
          description="Converse com a IA oficial e obtenha respostas baseadas nas políticas Estácio."
          primary
          onClick={() => onOpenChat("/chat")}
          icon="🤖"
        />
        {(user.is_admin || user.role === "admin") && (
          <HomeActionCard
            title="Administração do Sistema"
            subtitle="Gerenciar usuários, políticas e configurações"
            description="Acesse o painel administrativo."
            primary
            onClick={() => navigate("/admin")}
            icon="🛠️"
          />
        )}
        {highlights.map((item) => (
          <HomeActionCard
            key={item.title}
            title={item.title}
            subtitle={item.tag}
            description={item.description}
            icon={item.icon}
            disabled
          />
        ))}
      </section>

      <section className="info-panels">
        <InfoCard title="Políticas carregadas" description={`Total: ${policies.length || 0}`} tag="Políticas" />
        <InfoCard title="Status do modelo" description="Modelo atual: LM Studio" tag="Conexão: OK" />
      </section>

      {(user.is_admin || user.role === "admin") && <AdminPanel currentUser={user} users={adminUsers} policies={policies} />}
    </Shell>
  );
}
