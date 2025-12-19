import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";

type Props = {
  token: string;
};

export function AdminConfigPanel({ token }: Props) {
  const [modelName, setModelName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [temperature, setTemperature] = useState(0.25);
  const [topP, setTopP] = useState(1.0);
  const [status, setStatus] = useState("Desconhecido");

  useEffect(() => {
    adminService
      .getConfig(token)
      .then((cfg) => {
        setModelName(cfg.model_name || "");
        setSystemPrompt(cfg.system_prompt || "");
        setTemperature(Number(cfg.temperature ?? 0.25));
        setTopP(Number(cfg.top_p ?? 1.0));
      })
      .catch(console.error);
  }, [token]);

  const save = async () => {
    await adminService.updateConfig(
      { model_name: modelName, system_prompt: systemPrompt, temperature, top_p: topP },
      token
    );
    setStatus("Salvo");
  };

  return (
    <div className="card-glass">
      <div className="card-title">Configuracao do modelo</div>
      <label>Nome do modelo</label>
      <input className="input-glass" value={modelName} onChange={(e) => setModelName(e.target.value)} />
      <label>System prompt</label>
      <textarea
        className="input-glass"
        value={systemPrompt}
        onChange={(e) => setSystemPrompt(e.target.value)}
        rows={6}
      />
      <div className="grid-2">
        <div>
          <label>Temperatura</label>
          <input
            className="input-glass"
            type="number"
            step="0.05"
            min="0"
            max="2"
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
          />
        </div>
        <div>
          <label>Top P</label>
          <input
            className="input-glass"
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={topP}
            onChange={(e) => setTopP(Number(e.target.value))}
          />
        </div>
      </div>
      <div className="mt-2">
        <GlassButton onClick={save}>Salvar alteracoes</GlassButton>
        <span className="muted" style={{ marginLeft: "8px" }}>
          Status: {status}
        </span>
      </div>
    </div>
  );
}
