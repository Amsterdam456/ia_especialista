import { useEffect, useMemo, useState } from "react";
import { API_URL } from "../services/api";
import { GlassButton } from "../components/buttons/GlassButton";

type RawRow = {
  ano: string;
  cenario: string;
  natureza: string;
  agregador_conta: string;
  pacote: string;
  nome_conta: string;
  conta_descricao: string;
  meses: Record<string, number>;
  ytd: number;
};

type ViewMode = "YTD" | "Mensal" | "Anual";

const MONTHS = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];

const ALL_LINES = [
  "ROL","BM_DIGITAL","BM_PRESENCIAL","BM_VIDATODA",
  "Docentes","Apoio","Educacionais",
  "Lucro Bruto",
  "PDD","Pessoal","Adm.","Benefícios",
  "G&A","Assessorias e Consultorias","Despesas administrativas",
  "Imóveis","Informática e telecom","Infraestrutura",
  "Outras receitas e despesas operacionais",
  "Viagens e est.","Ganhos e perdas",
  "EBITDA",
];

// 🔥 helper para garantir tipo correto ao setState
const normalize = (arr: unknown[]): string[] =>
  arr.map((x) => String(x ?? "").trim()).filter(Boolean);

export default function PivotPage() {

  const [raw, setRaw] = useState<RawRow[]>([]);
  const [loading, setLoading] = useState(false);

  const [viewMode, setViewMode] = useState<ViewMode>("YTD");
  const [selectedMonth, setSelectedMonth] = useState<string>("Jan");

  const [cenarios, setCenarios] = useState<string[]>([]);
  const [anos, setAnos] = useState<string[]>([]);
  const [pacotes, setPacotes] = useState<string[]>([]);
  const [contas, setContas] = useState<string[]>([]);

  const [optCen, setOptCen] = useState<string[]>([]);
  const [optAno, setOptAno] = useState<string[]>([]);
  const [optPac, setOptPac] = useState<string[]>([]);
  const [optCon, setOptCon] = useState<string[]>([]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);

      const token = localStorage.getItem("athena_token") || "";

      const res = await fetch(`${API_URL}/admin/finance/pivot`, {
          method: "GET",
          headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          credentials: "include",
      });
      const json = await res.json();
      const arr = (json?.data?.raw ?? json?.raw ?? []) as RawRow[];

      setRaw(arr);

      const cenarios = normalize([...new Set(arr.map((r) => r.cenario))]);
      const anos = normalize([...new Set(arr.map((r) => r.ano))]);
      const pacs = normalize([...new Set(arr.map((r) => r.pacote))]);
      const cons = normalize([...new Set(arr.map((r) => r.nome_conta))]);

      setOptCen(cenarios);     setCenarios(cenarios);
      setOptAno(anos);         setAnos(anos);
      setOptPac(pacs);         setPacotes(pacs);
      setOptCon(cons);         setContas(cons);

      setLoading(false);
    };

    load();
  }, []);

  // 🔥 filtro seguro
  const rawFiltered = useMemo(() => {
    return raw.filter(r =>
      cenarios.includes(r.cenario) &&
      anos.includes(r.ano) &&
      pacotes.includes(r.pacote) &&
      contas.includes(r.nome_conta)
    );
  }, [raw, cenarios, anos, pacotes, contas]);

  // 🔥 função correta para valor
  const getValue = (r: RawRow): number => {
    if (viewMode === "YTD") return r.ytd ?? 0;
    if (viewMode === "Mensal") return r.meses[selectedMonth] ?? 0;
    return Object.values(r.meses).reduce((a, b) => a + (b ?? 0), 0);
  };

  const dre = useMemo(() => {
    const map: Record<string, number> = {};
    ALL_LINES.forEach(k => map[k] = 0);

    rawFiltered.forEach(r => {

      let linha = "G&A";

      if (/ROL/i.test(r.natureza)) linha = "ROL";
      if (/DOCENTE/i.test(r.agregador_conta)) linha = "Docentes";
      if (/APOIO/i.test(r.agregador_conta)) linha = "Apoio";
      if (/EDUCACIONAL/i.test(r.agregador_conta)) linha = "Educacionais";
      if (/PESSOAL/i.test(r.agregador_conta)) linha = "Pessoal";
      if (/INFRA/i.test(r.agregador_conta)) linha = "Infraestrutura";

      map[linha] += getValue(r);
    });

    map["Lucro Bruto"] = map["ROL"] - map["Docentes"] - map["Apoio"] - map["Educacionais"];
    map["EBITDA"] =
      map["Lucro Bruto"] - map["PDD"] - map["Pessoal"] - map["G&A"] - map["Ganhos e perdas"];

    return ALL_LINES.map(id => ({ id, valor: map[id] }));
  }, [rawFiltered, viewMode, selectedMonth]);

  return (
    <div className="card-glass pivot-card">

      <div className="pivot-header">
        <h2>Visão consolidada</h2>

        <div className="pivot-filters">
          <select
            className="input-glass"
            value={viewMode}
            onChange={(e) => setViewMode(e.target.value as ViewMode)}
          >
            <option value="YTD">YTD</option>
            <option value="Mensal">Mensal</option>
            <option value="Anual">Anual</option>
          </select>

          {viewMode === "Mensal" && (
            <select
              className="input-glass"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
            >
              {MONTHS.map(m => <option key={m}>{m}</option>)}
            </select>
          )}

          <GlassButton disabled={loading}>
            {loading ? "Carregando..." : "Aplicar"}
          </GlassButton>
        </div>
      </div>

      <table className="admin-table pivot-table">
        <thead>
          <tr>
            <th>DRE / Conta</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          {dre.map(row => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>{row.valor.toLocaleString("pt-BR")}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {!dre.length && !loading && (
        <p className="muted">Nenhum dado encontrado.</p>
      )}
    </div>
  );
}
