import { useEffect, useMemo, useState, useRef } from "react";
import type { ChangeEvent } from "react";
import { adminService } from "../services/adminService";
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

const MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

const ALL_LINES = [
  "ROL", "BM_DIGITAL", "BM_PRESENCIAL", "BM_VIDATODA",
  "Docentes", "Apoio", "Educacionais",
  "Lucro Bruto",
  "PDD", "Pessoal", "Adm.", "Beneficios",
  "G&A", "Assessorias e Consultorias", "Despesas administrativas",
  "Imoveis", "Informatica e telecom", "Infraestrutura",
  "Outras receitas e despesas operacionais",
  "Viagens e est.", "Ganhos e perdas",
  "EBITDA",
];

const normalize = (arr: unknown[]): string[] =>
  arr.map((x) => String(x ?? "").trim()).filter(Boolean);

export default function PivotPage() {
  const [raw, setRaw] = useState<RawRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<ViewMode>("YTD");
  const [selectedMonth, setSelectedMonth] = useState<string>("Jan");

  const [cenarios, setCenarios] = useState<string[]>([]);
  const [anos, setAnos] = useState<string[]>([]);
  const [pacotes, setPacotes] = useState<string[]>([]);
  const [contas, setContas] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [optCen, setOptCen] = useState<string[]>([]);
  const [optAno, setOptAno] = useState<string[]>([]);
  const [optPac, setOptPac] = useState<string[]>([]);
  const [optCon, setOptCon] = useState<string[]>([]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem("athena_token") || "";
        const data = await adminService.getPivot(token);
        const arr = (data?.raw ?? data ?? []) as RawRow[];

        setRaw(arr);

        const cenarios = normalize([...new Set(arr.map((r) => r.cenario))]);
        const anos = normalize([...new Set(arr.map((r) => r.ano))]);
        const pacs = normalize([...new Set(arr.map((r) => r.pacote))]);
        const cons = normalize([...new Set(arr.map((r) => r.nome_conta))]);

        setOptCen(cenarios);
        setCenarios(cenarios);
        setOptAno(anos);
        setAnos(anos);
        setOptPac(pacs);
        setPacotes(pacs);
        setOptCon(cons);
        setContas(cons);
      } catch (err) {
        console.error(err);
        setError("Falha ao carregar dados financeiros. Tente novamente.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const rawFiltered = useMemo(() => {
    return raw.filter((r) =>
      cenarios.includes(r.cenario) &&
      anos.includes(r.ano) &&
      pacotes.includes(r.pacote) &&
      contas.includes(r.nome_conta)
    );
  }, [raw, cenarios, anos, pacotes, contas]);

  const getValue = (r: RawRow): number => {
    if (viewMode === "YTD") return r.ytd ?? 0;
    if (viewMode === "Mensal") return r.meses[selectedMonth] ?? 0;
    return Object.values(r.meses).reduce((a, b) => a + (b ?? 0), 0);
  };

  const dre = useMemo(() => {
    const map: Record<string, number> = {};
    ALL_LINES.forEach((k) => (map[k] = 0));

    rawFiltered.forEach((r) => {
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

    return ALL_LINES.map((id) => ({ id, valor: map[id] }));
  }, [rawFiltered, viewMode, selectedMonth]);

  const handleMulti = (event: ChangeEvent<HTMLSelectElement>, setter: (values: string[]) => void) => {
    const values = Array.from(event.target.selectedOptions).map((o) => o.value);
    setter(values);
  };

  const exportCsv = () => {
    if (!rawFiltered.length) return;
    const header = ["ano", "cenario", "natureza", "agregador_conta", "pacote", "nome_conta", "valor"];
    const lines = rawFiltered.map((r) => {
      const val = getValue(r);
      return [r.ano, r.cenario, r.natureza, r.agregador_conta, r.pacote, r.nome_conta, val].join(",");
    });
    const csv = [header.join(","), ...lines].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "pivot.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    try {
      setLoading(true);
      await adminService.uploadFinanceCsv(file);
      const token = localStorage.getItem("athena_token") || "";
      const data = await adminService.getPivot(token);
      const arr = (data?.raw ?? data ?? []) as RawRow[];
      setRaw(arr);
    } catch (err) {
      console.error(err);
      setError("Falha ao enviar CSV.");
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="card-glass pivot-card">
      <div className="pivot-header">
        <h2>Visao consolidada</h2>

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
              {MONTHS.map((m) => <option key={m}>{m}</option>)}
            </select>
          )}

          <GlassButton disabled={loading} onClick={exportCsv}>
            Exportar CSV
          </GlassButton>
          <GlassButton variant="ghost" disabled={loading} onClick={() => fileInputRef.current?.click()}>
            Enviar CSV
          </GlassButton>
          <input
            type="file"
            accept=".csv"
            ref={fileInputRef}
            style={{ display: "none" }}
            onChange={handleUpload}
          />
        </div>
      </div>

      {error && <p className="muted">{error}</p>}

      <div className="pivot-filters grid-4">
        <label>
          Cenario
          <select multiple className="input-glass" value={cenarios} onChange={(e) => handleMulti(e, setCenarios)}>
            {optCen.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label>
          Ano
          <select multiple className="input-glass" value={anos} onChange={(e) => handleMulti(e, setAnos)}>
            {optAno.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label>
          Pacote
          <select multiple className="input-glass" value={pacotes} onChange={(e) => handleMulti(e, setPacotes)}>
            {optPac.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label>
          Conta
          <select multiple className="input-glass" value={contas} onChange={(e) => handleMulti(e, setContas)}>
            {optCon.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
      </div>

      <table className="admin-table pivot-table">
        <thead>
          <tr>
            <th>DRE / Conta</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          {dre.map((row) => (
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
