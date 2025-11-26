# IA Especialista - Operações e Deploy Local

Este repositório contém o backend (FastAPI + SQLite + RAG) e o frontend (React/Vite) para o assistente da Estácio. Como o repositório local não possui um remoto configurado, use o passo a passo abaixo para conectar-se ao GitHub, testar e publicar suas alterações.

## 1. Conectar ao GitHub e subir a branch `work`
1. Crie o repositório no GitHub (ou use o existente) e copie a URL HTTPS ou SSH.
2. Adicione o remoto:
   ```bash
   git remote add origin <URL_DO_SEU_REPOSITORIO>
   git fetch origin
   ```
3. Publique a branch atual (`work`):
   ```bash
   git push -u origin work
   ```
4. Nas próximas alterações, basta usar `git push` para enviar novos commits.

> Dica: se o comando `git pull` disser que "já está atualizado", é porque o remoto ainda não foi configurado. Após adicionar o `origin` e publicar a `work`, o `git pull`/`git push` passam a funcionar normalmente.

### Baixar os arquivos sem remoto (zip)
Se preferir levar o código para outra máquina antes de conectar ao GitHub, gere um zip a partir da raiz do projeto:

```bash
git archive --format=zip --output ../ia_especialista.zip HEAD
```

Transfira o arquivo `../ia_especialista.zip` para sua máquina, extraia e siga os passos acima para conectar ao GitHub e publicar.

## 2. Rodar o backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ajuste as variáveis se precisar
uvicorn app.main:app --reload --port 8000
```

Pontos importantes:
- Um admin padrão é criado no startup (e pode ser ajustado no `.env`).
- Os PDFs/DOCX em `app/policies` são ingeridos e monitorados pelo watcher, que recalcula embeddings quando há mudanças.

## 3. Rodar o frontend
```bash
cd frontend
npm install
cp .env.example .env  # defina VITE_API_URL se usar outra porta/host
npm run dev -- --host
```
A interface usa a API em `http://localhost:8000` por padrão ou o valor configurado em `VITE_API_URL`.

## 4. Verificações rápidas
- Login com admin padrão e criação de usuários/chats podem ser feitos via frontend ou `curl` conforme o `backend/README.md`.
- Para validar build:
  ```bash
  (backend) python -m compileall app
  (frontend) npm run build
  ```
