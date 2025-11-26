import "./App.css";
import bg from "./assets/bg_athena.jpg";

function App() {
  const cardsRow1 = [
    {
      icon: "🧠",
      title: "ATHENA IA",
      text: "Assistente especialista treinado com dados internos da Estácio para responder perguntas, gerar análises e apoiar decisões.",
      tag: "IA Especialista",
    },
    {
      icon: "📍",
      title: "NEURAL MAP",
      text: "Mapa inteligente que cruza CEP, mercado, captação e evasão, revelando oportunidades e riscos por região.",
      tag: "Mapa Estratégico",
    },
    {
      icon: "📊",
      title: "ATHENA OPS",
      text: "Digital Twin da operação: simula cenários de mídia, ticket, base, evasão e prevê impacto em ROL.",
      tag: "Digital Twin",
    },
  ];

  const cardsRow2 = [
    {
      icon: "⚠️",
      title: "ATHENA DNA",
      text: "Sistema de riscos com score por núcleo: identifica sinais precoces de queda de captação, evasão ou perda de share.",
      tag: "Gestão de Riscos",
    },
    {
      icon: "📈",
      title: "FORECAST 360",
      text: "Visão completa do futuro: previsões financeiras, comerciais, acadêmicas e de mercado em um único painel.",
      tag: "Previsão 360º",
    },
    {
      icon: "🧾",
      title: "ATHENA GEN & ORACLE",
      text: "Gera planos comerciais/ acadêmicos e responde perguntas complexas sobre impacto financeiro e operacional.",
      tag: "Planos & Perguntas",
    },
  ];

  const handleCardClick = (module: string) => {
    // Aqui depois vamos navegar para páginas reais (React Router) ou abrir modais.
    alert(`(MVP) Você clicou no módulo: ${module}`);
  };

  return (
    <div
      className="athena-root"
      style={{ backgroundImage: `url(${bg})` }}
    >
      <aside className="athena-sidebar">
        <div className="logo-mini">ATHENA</div>
        <nav>
          <ul>
            <li className="active">Dashboard</li>
            <li>ATHENA IA</li>
            <li>Neural Map</li>
            <li>Athena OPS</li>
            <li>Athena DNA</li>
            <li>Forecast 360</li>
            <li>Athena GEN & Oracle</li>
          </ul>
        </nav>
      </aside>

      <main className="athena-main">
        <header className="athena-header-tag">
          PROJETO ATHENA · INTELIGÊNCIA CORPORATIVA ESTÁCIO
        </header>

        <h1 className="athena-title">
          O CÉREBRO DIGITAL DA
          <br />
          REGIONAL SUDESTE
        </h1>

        <p className="athena-subtitle">
          Plataforma proprietária de IA, <strong>simulação</strong> e{" "}
          <strong>diagnóstico</strong> que conecta resultados financeiros,
          captação, evasão e operação acadêmica, transformando a Regional
          Sudeste em um <strong>Digital Twin</strong> vivo da Estácio.
        </p>

        <section className="athena-grid">
          {cardsRow1.map((c) => (
            <div
              key={c.title}
              className="athena-card"
              onClick={() => handleCardClick(c.title)}
            >
              <div className="athena-card-icon">{c.icon}</div>
              <div className="athena-card-title">{c.title}</div>
              <div className="athena-card-text">{c.text}</div>
              <div className="athena-card-tag">• {c.tag}</div>
            </div>
          ))}
        </section>

        <section className="athena-grid">
          {cardsRow2.map((c) => (
            <div
              key={c.title}
              className="athena-card"
              onClick={() => handleCardClick(c.title)}
            >
              <div className="athena-card-icon">{c.icon}</div>
              <div className="athena-card-title">{c.title}</div>
              <div className="athena-card-text">{c.text}</div>
              <div className="athena-card-tag">• {c.tag}</div>
            </div>
          ))}
        </section>

        <footer className="athena-footer">
          Projeto ATHENA · Desenvolvido por Gustavo Moreira · Regional Sudeste
          Estácio
        </footer>
      </main>
    </div>
  );
}

export default App;
