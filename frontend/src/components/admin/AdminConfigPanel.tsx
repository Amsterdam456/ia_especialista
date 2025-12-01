import { useEffect, useState } from "react";
import { adminService } from "../../services/adminService";
import { GlassButton } from "../buttons/GlassButton";

type Props = {
  token: string;
};

export function AdminConfigPanel({ token }: Props) {
  const [modelName, setModelName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState("Desconhecido");

  useEffect(() => {
    adminService.getConfig(token).then((cfg) => setModelName(cfg.model_name || "")).catch(console.error);
  }, [token]);

  const save = async () => {
    await adminService.updateConfig({ model_name: modelName, api_key: apiKey }, token);
    setStatus("Salvo");
  };

  return (
    <div className="card-glass">
      <div className="card-title">Configuração do modelo</div>
      <label>Nome do modelo</label>
      <input className="input-glass" value={modelName} onChange={(e) => setModelName(e.target.value)} />
      <label>Chave LM Studio / OpenAI</label>
      <input className="input-glass" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
      <div className="mt-2">
        <GlassButton onClick={save}>Salvar alterações</GlassButton>
        <span className="muted" style={{ marginLeft: "8px" }}>Status: {status}</span>
      </div>
    </div>
  );
}
