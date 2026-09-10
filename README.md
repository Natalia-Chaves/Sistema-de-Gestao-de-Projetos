# Sistema de Chamados e Projetos (Desafio Técnico)

Aplicação Django para abertura e acompanhamento de chamados (com integração ao GLPI)
e de solicitações de novos projetos de desenvolvimento.

## Papéis de acesso (recurso extra)

Além do login simples, o sistema possui um modelo de permissões por papel:

| Papel | O que vê | O que pode fazer |
|---|---|---|
| **Colaborador** | Apenas os próprios chamados; todos os projetos | Abrir chamados e projetos |
| **Colaborador de área TI** (recurso extra) | Todos os chamados, de qualquer área | Tudo do Colaborador + alterar status de qualquer chamado + "pegar" chamados na **Esteira** |
| **Gestor de área** | Chamados e projetos da sua área | Abrir chamados/projetos + alterar status dos itens da sua área + criar Colaboradores da própria área |
| **Gestor de Desenvolvimento** | Todos os chamados e projetos, de todas as áreas | Tudo dos gestores de área + criar/gerenciar acessos de colaboradores e gestores de qualquer área |

Áreas disponíveis: Engenharia, Produção, Manutenção, Qualidade, Suprimentos, Administrativo, TI.

- Um usuário criado via `createsuperuser` é tratado automaticamente como **Gestor de Desenvolvimento**
  (mesmo sem um registro em `Perfil`), podendo acessar `/usuarios/` e cadastrar os
  demais acessos.
- Qualquer **Colaborador com área = TI** vira automaticamente um atendente: consegue ver a fila
  de chamados sem atendimento em **Esteira**, "pegar" um chamado (vincula a si e muda o status
  para "Em atendimento") e alterar o status de qualquer chamado, não só o próprio.
- O Gestor de Desenvolvimento cria colaboradores e gestores de área em **Usuários → Novo usuário**,
  escolhendo papel e área livremente. O Gestor de área também acessa essa tela, mas só consegue
  criar **Colaboradores da própria área** (os campos de papel/área ficam travados no formulário).
- O **login é feito com e-mail e senha**. A matrícula continua existindo como identificação
  interna do colaborador (deve conter apenas números), mas não é mais usada para logar.
- O Gestor não define senha na criação: **a senha inicial é a própria matrícula**
  do colaborador. O usuário pode trocá-la depois em **Alterar senha**.

## Stack

- Backend: Python + Django
- Frontend: Django Templates + Tailwind CSS (via CDN) + JavaScript
- Banco: PostgreSQL (produção) ou SQLite (desenvolvimento local)
- Integração: API REST do GLPI, com fallback automático para modo simulado (mock)
- Infra: Docker (imagem única, usada no deploy no Render) + WhiteNoise para arquivos estáticos

## Estrutura do projeto

```
desafio_eqs/        # configurações do projeto Django (settings, urls)
core/                # app principal: models, views, forms, integração GLPI, testes
templates/core/      # templates HTML (Tailwind)
Dockerfile
entrypoint.sh
requirements.txt
```

---

## Rodar localmente (SQLite)

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
| Acesso | Login (e-mail + senha), identificação do usuário logado, portal com acesso a Chamados e Projetos |
| Chamados | Abertura, campos obrigatórios (título, descrição, categoria, prioridade), integração GLPI real/mock, ID do GLPI, listagem com busca/filtro, tela de detalhes, status |
| Esteira (recurso extra) | Fila de chamados sem atendimento, "pegar chamado" (atribui a si e muda o status) |
| Projetos | Abertura, campos obrigatórios (título, área, descrição, objetivo, prioridade), campos opcionais (benefício, prazo), ID único, listagem com busca/filtro, fluxo de status, tela de detalhes |
| Dashboard | Totais e contagem por status de chamados e projetos, filtrados pelo papel/área de quem está logado |
| Auditoria | Data de criação e última atualização em todos os registros |
| Erros | Validação de formulário e tratamento de falha de integração com mensagens claras |

---

## Guia de teste

### Usuários de teste

Contas já cadastradas no banco local de desenvolvimento para testar cada papel
(senha = a própria matrícula, será pedida a troca no primeiro login):

| E-mail | Matrícula (senha) | Papel | Área |
|---|---|---|---|
| gestorti@empresa.com | 01 | Gestor de Desenvolvimento | — |
| atendenteti@empresa.com | 02 | Colaborador (atendente de TI) | TI |
| gestorengenharia@empresa.com | 03 | Gestor de área | Engenharia |

> Essas contas existem apenas no banco local usado durante o desenvolvimento — não são
> criadas automaticamente em um banco novo (ex.: ao rodar `migrate` do zero ou no deploy
> no Render). Para recriá-las em outro ambiente, rode:
> ```powershell
> python manage.py shell -c "
> from django.contrib.auth import get_user_model
> from core.models import Perfil
> U = get_user_model()
> def cria(matricula, email, papel, area):
>     if U.objects.filter(username=matricula).exists():
>         return
>     u = U.objects.create_user(username=matricula, email=email, password=matricula)
>     Perfil.objects.create(user=u, papel=papel, area=area, senha_temporaria=True)
> cria('01', 'gestorti@empresa.com', Perfil.PAPEL_GESTOR_TI, '')
> cria('02', 'atendenteti@empresa.com', Perfil.PAPEL_COLABORADOR, 'TI')
> cria('03', 'gestorengenharia@empresa.com', Perfil.PAPEL_GESTOR, 'Engenharia')
> "
> ```

### 1. Login e identificação (RF-01, RF-02, RF-03)
1. Acesse a tela de login — deve exibir o nome "Sistema de Gestão de Chamados".
2. Entre com `gestorti@empresa.com` / `01`. Como a senha é a própria matrícula, o sistema deve
   redirecionar para **Alterar senha** antes de liberar o resto do sistema.
3. Troque a senha e confirme que é redirecionado ao **Dashboard**, com seu nome/papel visíveis
   no menu superior e a faixa "Portal: Gestor de Desenvolvimento" logo abaixo.
4. Tente digitar uma senha errada 5 vezes seguidas: o sistema deve bloquear novas tentativas
   por alguns minutos.

### 2. Abrir e consultar chamados (RF-04 a RF-10)
1. Logado como qualquer usuário, vá em **Chamados → Novo chamado**.
2. Tente salvar sem preencher a descrição — deve validar e não deixar salvar.
3. Preencha título, descrição, categoria e prioridade e salve. Deve aparecer uma mensagem
   informando que o chamado foi registrado (real ou simulado no GLPI) com um ID.
4. Na listagem de **Chamados**, confirme que o novo chamado aparece com o status "Novo" e o
   ID do GLPI preenchido.
5. Clique no título do chamado — deve abrir a tela de **detalhe** com todos os campos.
6. Use os filtros de busca/status/prioridade no topo da listagem e confirme que a lista é
   filtrada corretamente.

### 3. Esteira e atendimento de TI (recurso extra)
1. Faça login como `atendenteti@empresa.com` / `02` (Colaborador da área TI).
2. No menu, deve aparecer o link **Esteira** — acesse e confirme que aparecem todos os
   chamados com status "Novo" e sem atendente, de qualquer área.
3. Clique em **Pegar chamado** em um deles — deve sumir da esteira, e na listagem de
   **Chamados** ele deve aparecer com status "Em atendimento" e você como atendente.
4. Faça login com um Colaborador comum (papel Colaborador, área diferente de TI) e confirme
   que o link **Esteira** não aparece e que `/esteira/` redireciona para o Dashboard.

### 4. Projetos (RF-11 a RF-17)
1. Vá em **Projetos → Novo projeto** e tente salvar sem preencher objetivo — deve validar.
2. Preencha todos os campos obrigatórios (título, área, descrição do problema, objetivo,
   prioridade) e deixe benefício/prazo em branco — deve salvar normalmente (são opcionais).
3. Na listagem, clique no título do projeto e confirme que a tela de detalhe mostra todos
   os dados, inclusive os campos opcionais quando preenchidos.
4. Logado como `gestorengenharia@empresa.com` / `03`, altere o status de um projeto da área
   Engenharia — deve funcionar. Tente alterar um projeto de outra área — deve ser bloqueado.

### 5. Papéis e controle de acesso (recurso extra)
1. Logado como `gestorengenharia@empresa.com` / `03`, vá em **Usuários → Novo usuário**.
   Os campos Papel e Área devem aparecer travados em "Colaborador" / "Engenharia".
2. Crie um colaborador — confirme que ele só consegue ver os próprios chamados ao logar.
3. Logado como `gestorti@empresa.com` / `01`, confirme que os campos Papel/Área ficam
   livres e que é possível criar um Gestor de área em qualquer área.
4. Tente acessar `/usuarios/` logado como um Colaborador comum — deve ser redirecionado
   ao Dashboard com uma mensagem de acesso negado.

### 6. Dashboard (RF-19) e auditoria (RF-20)
1. Compare o Dashboard logado como Colaborador (só os próprios chamados), Gestor de área
   (só a própria área) e Gestor de Desenvolvimento (tudo) — os totais e a contagem por
   status devem mudar de acordo com o papel.
2. Abra o admin do Django (`/admin/`, com um superusuário) e confirme que todo chamado/
   projeto tem `data_criacao` e `data_atualizacao` preenchidos automaticamente.

---

## Registro da entrega

- Nome do participante: _preencher_
- Data de início: _preencher_
- Data de entrega: _preencher_
- Link do repositório: _preencher_
- Versão do Python: 3.12
- Versão do Django: 6.1.1
- Banco utilizado: PostgreSQL (Docker) / SQLite (local)
- Funcionalidades adicionais implementadas: dashboard com indicadores por papel/área, tela de
  detalhes do chamado e do projeto, esteira de atendimento para colaboradores da área de TI,
  admin do Django para gestão de chamados/projetos, login por e-mail, Docker para deploy em
  produção (Render).
- Observações gerais: integração com o GLPI entregue em **modo simulado (mock)**,
  por não haver ambiente GLPI disponível para testes reais. O código de integração
  via API REST (`core/glpi_client.py`) está implementado e pronto para uso — basta
  configurar `GLPI_API_URL`, `GLPI_APP_TOKEN` e `GLPI_USER_TOKEN` no `.env`.
