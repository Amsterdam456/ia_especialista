# ATHENA IA - Operacoes e Validacao

Este repositorio contem o backend (FastAPI + SQLite + RAG) e o frontend (React/Vite) para o assistente da Estacio.

## 1. Preparar o ambiente
1) Copie os exemplos de variaveis:
```bash
cd backend
cp .env.example .env
cd ..\\frontend
cp .env.example .env
```
2) Ajuste no `backend/.env`:
- `ADMIN_EMAIL` e `ADMIN_PASSWORD` (senha minima 8 caracteres).
- `SECRET_KEY` (obrigatorio para JWT).
- `LMSTUDIO_API_URL` e `LMSTUDIO_MODEL` (se usar LM Studio local).
3) Ajuste no `frontend/.env`:
- `VITE_API_URL=http://localhost:8000` (ou URL da API).

## 2. Rodar o backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Pontos importantes:
- Um admin inicial e criado no startup (use o `ADMIN_EMAIL`/`ADMIN_PASSWORD` do `.env`).
- Os arquivos em `storage/policies` sao ingeridos e monitorados pelo watcher.
- Se ja existir um banco antigo, use `alembic stamp head` antes do upgrade.

## 3. Rodar o frontend
```bash
cd frontend
npm install
npm run dev -- --host
```

A interface usa a API em `http://localhost:8000` por padrao ou o valor configurado em `VITE_API_URL`.

## 4. Validar as mudancas (passo a passo)
### 4.1 Autenticacao e perfil
1) Acesse `http://localhost:5173` e faca login com o admin.
2) Va em "Meu perfil" e teste a troca de senha (minimo 8 caracteres).
3) Teste bloqueio por tentativas invalidas e reativacao no admin.

### 4.2 Painel administrativo
1) Acesse `/admin` e confirme:
- Lista de usuarios carregando.
- Polticas carregando e status exibido.
2) Teste criacao e edicao de usuario.
3) Teste reset de senha e criacao em lote (CSV).
4) Baixe o CSV de auditoria em Auditoria > Exportar CSV.

### 4.3 Polticas e RAG
1) Envie um arquivo `.pdf`, `.docx` ou `.txt` em "Politicas".
2) Clique em "Processar politicas".
3) Abra um chat e pergunte algo que exista no documento.
4) Confirme se as fontes aparecem no chat.

### 4.4 Chat e streaming
1) Inicie uma nova conversa e envie uma pergunta.
2) Verifique se o streaming funciona e se o historico do chat grava.
3) Teste renomear e excluir chats no menu lateral.

### 4.5 Feedback e melhoria da IA
1) Envie feedback com comentario nas respostas (alunos/usuarios).
2) No painel admin, aprove ou rejeite as diretrizes pendentes.
3) Feedback de admins e aplicado direto nas proximas respostas.

### 4.6 Pivot financeiro
1) Acesse `/pivot`.
2) Se necessario, envie um CSV em "Enviar CSV".
3) Verifique filtros e exportacao CSV.

## 5. Validacoes tecnicas (opcional)
```bash
cd backend
python -m compileall app

cd ..\\frontend
npm run build
```

## 6. Observacoes de seguranca
- Nao use `ADMIN_PASSWORD=change-me` em ambiente real.
- Ajuste `CORS_ORIGINS` se publicar a interface em outro dominio.
- Mantenha o `SECRET_KEY` privado.
