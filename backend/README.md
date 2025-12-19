# Athena IA Specialist

## Backend (FastAPI)
- RAG com ingestao de politicas em `storage/policies` (PDF/DOCX/TXT). O watcher roda em thread de fundo e recalcula embeddings quando detectar mudancas.
- Autenticacao JWT com usuarios e administradores; um usuario admin inicial e criado no startup (`ADMIN_EMAIL`, `ADMIN_PASSWORD`).
- Banco SQLite em `data/athena.db` com tabelas de usuarios, chats e mensagens. Cada usuario pode manter multiplos chats e cada mensagem fica registrada com historico.
- Endpoints principais:
  - `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/change-password`
  - `GET/POST /chats`, `GET /chats/{id}/messages`, `POST /chats/{id}/ask`
  - `GET /admin/users`, `GET /admin/policies` (apenas admin)
  - `POST /athena/ask` (consulta direta sem chat persistido)

### Como rodar
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Variaveis de ambiente
Copie o arquivo `.env.example` para `.env` e ajuste conforme necessario:

```bash
cd backend
cp .env.example .env
```

Valores padrao incluidos:

- **LM Studio**: `LMSTUDIO_API_URL=http://127.0.0.1:1234/v1/responses` e `LMSTUDIO_MODEL=qwen2.5-7b-instruct-1m`.
- **JWT**: `SECRET_KEY=change-me`, `ALGORITHM=HS256`, expiracao de token `ACCESS_TOKEN_EXPIRE_MINUTES=720`.
- **Banco**: `DATABASE_URL=sqlite:///./data/athena.db` (SQLite local).
- **Watcher**: `CHECK_INTERVAL_SECONDS=86400` para reprocessar politicas em `storage/policies`.
- **Admin inicial**: `ADMIN_EMAIL=admin@athena.com` e `ADMIN_PASSWORD=change-me` (senha minima de 8 caracteres).
- **Seguranca**: `LOGIN_MAX_ATTEMPTS=5`, `LOGIN_LOCKOUT_MINUTES=15`, `FEEDBACK_DIRECTIVES_LIMIT=20`.

### Como verificar se tudo esta funcionando
1) **Suba o backend** com o `.env` configurado e acompanhe os logs do `uvicorn`; voce vera mensagens de criacao do banco, bootstrap do admin e ingestao das politicas em `storage/policies`.
2) **Testes de autenticacao**:
   - Crie um usuario comum:
     ```bash
     curl -X POST http://localhost:8000/api/v1/auth/register \
       -H "Content-Type: application/json" \
       -d '{"email":"usuario@exemplo.com","password":"Senha1234"}'
     ```
   - Faca login:
     ```bash
     curl -X POST http://localhost:8000/api/v1/auth/login \
       -H "Content-Type: application/json" \
       -d '{"email":"admin@athena.com","password":"change-me"}'
     ```
   - Use o token retornado para acessar rotas protegidas, por exemplo `/admin/users` (apenas admin) ou `/chats`.
3) **Teste de RAG**:
   ```bash
   # cria um chat
   curl -X POST http://localhost:8000/api/v1/chats \
     -H "Authorization: Bearer SEU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title":"Duvidas politicas"}'

   # envia pergunta
   curl -X POST http://localhost:8000/api/v1/chats/1/ask \
     -H "Authorization: Bearer SEU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"question":"Quais sao as politicas internas?"}'
   ```
4) **Frontend**: rode `npm run dev -- --host` em `frontend` e faca login com o admin inicial para validar dashboards e historico de chats.

Recomendacao: altere as credenciais do admin no `.env` antes de expor o sistema.
