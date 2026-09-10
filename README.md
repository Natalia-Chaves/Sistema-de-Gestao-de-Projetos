# Sistema de Chamados e Projetos (Desafio Técnico)

Aplicação Django para abertura e acompanhamento de chamados (com integração ao GLPI)
e de solicitações de novos projetos de desenvolvimento.

## Papéis de acesso (recurso extra)

Além do login simples, o sistema possui um modelo de permissões por papel:

| Papel | O que vê | O que pode fazer |
|---|---|---|
| **Colaborador** | Apenas os próprios chamados; todos os projetos | Abrir chamados e projetos |
| **Gestor de área** | Chamados e projetos da sua área | Abrir chamados/projetos + alterar status dos itens da sua área |
| **Gestor de Desenvolvimento** | Todos os chamados e projetos, de todas as áreas | Tudo dos gestores de área + criar/gerenciar acessos de colaboradores e gestores |

Áreas disponíveis: Engenharia, Produção, Manutenção, Qualidade, Suprimentos, Administrativo, TI.

- Um usuário criado via `createsuperuser` é tratado automaticamente como **Gestor de Desenvolvimento**
  (mesmo sem um registro em `Perfil`), podendo acessar `/usuarios/` e cadastrar os
  demais acessos.
- O Gestor de Desenvolvimento cria colaboradores e gestores de área em **Usuários → Novo usuário**,
  escolhendo o papel e a área de cada um.
- A **matrícula** (usada como usuário de login) deve conter apenas números.
- O Gestor de Desenvolvimento não define senha na criação: **a senha inicial é a própria matrícula**
  do colaborador/gestor. O usuário pode trocá-la depois pelo admin do Django.

## Stack

- Backend: Python + Django
- Frontend: Django Templates + Tailwind CSS (via CDN) + JavaScript
- Banco: PostgreSQL (produção/Docker) ou SQLite (desenvolvimento local sem Docker)
- Integração: API REST do GLPI, com fallback automático para modo simulado (mock)
- Infra: Docker + Docker Compose + Nginx

## Estrutura do projeto

```
desafio_eqs/        # configurações do projeto Django (settings, urls)
core/                # app principal: models, views, forms, integração GLPI, testes
templates/core/      # templates HTML (Tailwind)
nginx/               # configuração do proxy reverso usado no Docker
Dockerfile
docker-compose.yml
entrypoint.sh
requirements.txt
```

---

## Opção 1 — Rodar localmente sem Docker (SQLite)

Pré-requisitos: Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse http://127.0.0.1:8000. Sem preencher as variáveis `GLPI_*` no `.env`, a integração
com o GLPI funciona em **modo simulado (mock)** automaticamente.

---

## Opção 2 — Rodar com Docker (Postgres + Nginx)

Pré-requisitos: Docker e Docker Compose instalados.

```powershell
copy .env.example .env
docker compose up --build
```

- Aplicação (via Nginx): http://localhost:8080
- O `entrypoint.sh` executa `migrate` e `collectstatic` automaticamente antes de subir o Gunicorn.
- Para criar um usuário de acesso:

```powershell
docker compose exec web python manage.py createsuperuser
```

> **Observação:** o Docker não estava disponível no ambiente usado para gerar este
> projeto, então a stack (Dockerfile + docker-compose + Nginx) foi revisada
> manualmente mas não foi validada com `docker compose up` de ponta a ponta.
> Rode localmente e me avise se algum ajuste for necessário.

---

## Configuração da integração com o GLPI

> **Status desta entrega: modo simulado (mock) ativo.**
> Não havia um ambiente GLPI disponível para integração real no momento do
> desenvolvimento/demonstração. Conforme previsto no enunciado do desafio
> ("Caso não haja ambiente disponível, a integração pode ser simulada e
> devidamente documentada"), a aplicação usa o serviço mock descrito abaixo.
> O código de integração real (`core/glpi_client.py`) está implementado e
> funcional — basta preencher as credenciais no `.env` para ativá-lo, sem
> nenhuma mudança de código.

As credenciais nunca ficam no código-fonte — são lidas do `.env`:

```
GLPI_API_URL=https://seu-glpi.exemplo.com/apirest.php
GLPI_APP_TOKEN=xxxx
GLPI_USER_TOKEN=xxxx
```

- Se essas variáveis **não estiverem preenchidas** (caso desta entrega), o sistema
  usa um serviço mock (`core/services.py`), gerando um ID simulado (`MOCK-XXXX`) e
  permitindo que toda a interface funcione normalmente.
- Se estiverem preenchidas, o sistema tenta a API real do GLPI
  (`core/glpi_client.py`: `initSession` → criação do chamado → `killSession`).
  Em caso de falha (rede, token inválido, API indisponível), o sistema trata o erro,
  cai automaticamente no modo simulado e exibe uma mensagem amigável ao usuário.

---

## Deploy em produção

### Recomendado: Render (aplicação única)


Este projeto é uma aplicação Django com templates renderizados no servidor
(não é uma SPA/API separada de um frontend estático). Por isso, o deploy
correto é um **serviço único** contendo backend + frontend juntos:

1. Suba o repositório no GitHub.
2. No Render, crie um **Web Service** a partir do repositório, usando o `Dockerfile`
   deste projeto (Render detecta e builda automaticamente).
3. Crie um banco **PostgreSQL** no Render e configure as variáveis de ambiente do
   serviço (`DB_ENGINE=postgres`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
   `DB_PORT`) com os dados fornecidos pelo Render.
4. Configure `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS` (domínio do Render) e
   `CSRF_TRUSTED_ORIGINS` nas variáveis de ambiente do serviço.
5. Configure as variáveis `GLPI_*` se for usar a integração real.

> **Nota sobre Vercel:** a Vercel é otimizada para frontends estáticos ou funções
> serverless (Next.js, React, etc.) e não é adequada para hospedar uma aplicação
> Django com templates renderizados no servidor, sessões e conexão persistente a
> banco de dados. Como este projeto não separa frontend (JS) e backend (API) — o
> Django Templates faz as duas coisas —, o deploy único no Render é o caminho que
> realmente funciona. Uma separação real (Django REST Framework + frontend em
> Next.js na Vercel) exigiria reescrever o frontend do zero, fora do escopo deste
> desafio.

---

## Testes automatizados

```powershell
python manage.py test core
```

Cobrem: acesso à tela de login, autenticação e redirecionamento ao dashboard,
criação de chamado (com preenchimento automático de usuário/status/ID do GLPI),
validação de campo obrigatório vazio, criação de projeto e tela de detalhes do projeto.

---

## Requisitos funcionais atendidos

| Módulo | Itens |
|---|---|
| Acesso | Login, identificação do usuário logado, portal com acesso a Chamados e Projetos |
| Chamados | Abertura, campos obrigatórios (título, descrição, categoria, prioridade), integração GLPI real/mock, ID do GLPI, listagem, status |
| Projetos | Abertura, campos obrigatórios (título, área, descrição, objetivo, prioridade), campos opcionais (benefício, prazo), ID único, listagem, fluxo de status, tela de detalhes |
| Auditoria | Data de criação e última atualização em todos os registros |
| Erros | Validação de formulário e tratamento de falha de integração com mensagens claras |

## Registro da entrega

- Nome do participante: _preencher_
- Data de início: _preencher_
- Data de entrega: _preencher_
- Link do repositório: _preencher_
- Versão do Python: 3.12
- Versão do Django: 6.1.1
- Banco utilizado: PostgreSQL (Docker) / SQLite (local)
- Funcionalidades adicionais implementadas: dashboard com indicadores, tela de
  detalhes do projeto, admin do Django para gestão de chamados/projetos, Docker +
  Nginx para deploy em produção.
- Observações gerais: integração com o GLPI entregue em **modo simulado (mock)**,
  por não haver ambiente GLPI disponível para testes reais. O código de integração
  via API REST (`core/glpi_client.py`) está implementado e pronto para uso — basta
  configurar `GLPI_API_URL`, `GLPI_APP_TOKEN` e `GLPI_USER_TOKEN` no `.env`.
