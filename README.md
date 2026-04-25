# MindTrack-Life

MindTrack-Life e uma plataforma web de analise comportamental que transforma registros diarios em inteligencia acionavel sobre habitos, humor, produtividade e evolucao pessoal.

## Visao do produto

O projeto foi desenhado para parecer um produto real:

- dashboard com forecast, insights humanos, streak e comparacao semanal
- camada de dados orientada a analytics
- API REST pronta para frontend mais moderno ou app mobile
- deploy preparado para PostgreSQL e execucao online

## Stack

- Backend: Flask factory + Blueprints
- ORM: Flask-SQLAlchemy
- Migracoes: Flask-Migrate + Alembic
- Banco: SQLite em desenvolvimento, PostgreSQL em producao
- Frontend: HTML + CSS responsivo + Chart.js
- Auth: sessao Flask + hash seguro com Werkzeug
- Infra: `.env`, `render.yaml`, `gunicorn`, logs simples
- Qualidade: `pytest`

## Principais features

- autenticacao com hash de senha e sessoes seguras
- registro diario com sono, estudo, exercicio, humor, progresso, produtividade e notas
- Life Score e perfil automatico do usuario
- previsao simples de humor para os proximos dias
- insights em linguagem humana
- streak, meta semanal e comparacao temporal
- exportacao CSV por usuario
- auditoria de eventos importantes
- snapshots pre-calculados para acelerar o dashboard

## Estrutura

```text
mindtrack-life/
|- app.py
|- mindtrack/
|  |- __init__.py
|  |- auth.py
|  |- config.py
|  |- database.py
|  |- models/
|  |  |- analytics_snapshot.py
|  |  |- audit_log.py
|  |  |- entry.py
|  |  |- goal.py
|  |  |- habit.py
|  |  |- habit_log.py
|  |  |- insight.py
|  |  |- user.py
|  |- routes/
|  |  |- api.py
|  |  |- auth.py
|  |  |- web.py
|  |- services/
|  |  |- analytics.py
|  |  |- audit.py
|  |  |- entries.py
|  |  |- forecast.py
|  |  |- goals.py
|  |  |- habits.py
|  |  |- insights.py
|  |- utils/
|     |- cache.py
|     |- helpers.py
|     |- security.py
|- migrations/
|- static/
|- templates/
|- tests/
|- .env.example
|- render.yaml
|- requirements.txt
```

## Database Architecture

O projeto utiliza uma arquitetura relacional orientada a dados, com PostgreSQL, tabelas normalizadas, constraints, indices, views analiticas, auditoria e snapshots de metricas para otimizar consultas do dashboard.

### Tabelas principais

- `users`: usuarios, roles e timestamps
- `daily_entries`: registro diario principal com UUID, checks e unicidade por data
- `habits`: habitos customizados do usuario
- `habit_logs`: execucao dos habitos por dia
- `goals`: metas pessoais com status e prazo
- `insights`: insights persistidos do sistema
- `analytics_snapshots`: metricas pre-calculadas por periodo
- `audit_logs`: trilha de auditoria com `old_data` e `new_data`

### Views analiticas

- `weekly_user_summary`
- `sleep_mood_analysis`

### O que isso comunica tecnicamente

- modelagem relacional
- suporte a migracoes versionadas
- integridade por constraints e indices
- base pronta para BI e analytics
- evolucao real para producao com PostgreSQL

## Como rodar localmente

### 1. Ambiente virtual

```powershell
uv venv .venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

### 2. Configuracao

Use `.env.example` como base:

```env
FLASK_ENV=development
SECRET_KEY=change-me-before-production
DATABASE_URL=sqlite:///instance/mindtrack.db
# DATABASE_URL=postgresql+psycopg://user:password@host:5432/mindtrack
CACHE_TTL_SECONDS=45
LOG_LEVEL=INFO
```

### 3. Aplicar migracoes

```powershell
flask --app app db upgrade
```

### 4. Executar

```powershell
flask --app app run
```

Acesse: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Comandos de migracao

```powershell
flask --app app db migrate -m "describe change"
flask --app app db upgrade
```

## API REST

### Core analytics

- `GET /api/dashboard`
- `GET /api/analytics`
- `GET /api/insights`
- `GET /api/forecast`
- `GET /api/snapshots`
- `GET /api/audit-logs`

### Daily entries

- `GET /api/entries`
- `POST /api/entries`
- `PUT /api/entries/<id>`
- `DELETE /api/entries/<id>`

### Habits

- `GET /api/habits`
- `POST /api/habits`
- `PUT /api/habits/<id>`
- `DELETE /api/habits/<id>`
- `GET /api/habit-logs`
- `POST /api/habit-logs`

### Goals

- `GET /api/goals`
- `POST /api/goals`
- `PUT /api/goals/<id>`
- `DELETE /api/goals/<id>`

Todas as respostas seguem o formato:

```json
{
  "success": true,
  "data": {}
}
```

## Testes

```powershell
pytest
```

## Deploy

O projeto esta preparado para Render ou Railway.

### Render

- build command: `pip install -r requirements.txt`
- start command: `flask --app app db upgrade && gunicorn app:app`
- variaveis obrigatorias:
  - `SECRET_KEY`
  - `DATABASE_URL`
  - `FLASK_ENV=production`

### Banco em producao

Use PostgreSQL no Render, Railway ou Supabase.

## Fluxo principal

1. usuario cria conta e faz login
2. registra o dia em um unico formulario
3. o sistema salva no banco
4. analytics, forecast e insights sao recalculados
5. dashboard mostra score, tendencias, comparacoes e recomendacoes

## Valor para portfolio e curriculo

Frase de curriculo:

> Modelei e implementei um banco de dados relacional com PostgreSQL, incluindo autenticacao, registros comportamentais, habitos, metas, insights, auditoria, indices, views analiticas e snapshots de metricas para dashboards.

## Validacao atual

- repositorio atualizado e versionado no GitHub
- migracoes Alembic versionadas no projeto
- schema migrado localmente de integer IDs para UUIDs
- snapshots e insights persistidos funcionando
- testes automatizados passando

## Melhorias futuras naturais

- screenshots reais no README
- deploy online com URL publica
- notificacoes e lembretes
- exportacao PDF
- filtros mensal e trimestral
