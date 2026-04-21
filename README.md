# MindTrack-Life

MindTrack-Life e uma plataforma web de analise comportamental que transforma registros diarios em metricas, insights humanos, previsao simples e um score de evolucao pessoal.

## O que o projeto entrega

- autenticacao com hash de senha, sessao segura e usuarios independentes
- registro diario rapido com sono, estudo, exercicio, leitura, lazer, humor, energia, progresso e notas
- dashboard dark mode com Life Score, streak, forecast, comparacao semanal e graficos Chart.js
- analise comportamental com medias, min/max, correlacoes, perfil e gamificacao
- insights em linguagem humana e previsao de humor para os proximos dias
- exportacao CSV por usuario e API REST em JSON consistente
- arquitetura Flask factory pronta para SQLite em dev e PostgreSQL em producao

## Stack

- Backend: Flask + Flask-SQLAlchemy
- Banco: SQLite em desenvolvimento, PostgreSQL no deploy
- Frontend: HTML + CSS responsivo + Chart.js
- Auth: sessao Flask + hash seguro com Werkzeug
- Infra: `.env`, `render.yaml`, `gunicorn`, logs simples
- Qualidade: `pytest` com smoke tests

## Estrutura

```text
mindtrack-life/
├── app.py
├── mindtrack/
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── entry.py
│   │   └── user.py
│   ├── routes/
│   │   ├── api.py
│   │   ├── auth.py
│   │   └── web.py
│   ├── services/
│   │   ├── analytics.py
│   │   ├── entries.py
│   │   ├── forecast.py
│   │   └── insights.py
│   └── utils/
│       ├── cache.py
│       ├── helpers.py
│       └── security.py
├── static/
├── templates/
├── tests/
├── .env.example
├── render.yaml
└── requirements.txt
```

## Features que vendem o projeto

- Life Score de 0 a 100 baseado em sono, estudo e humor
- perfil automatico do usuario: `Produtivo Consistente`, `Equilibrado` ou `Oscilante`
- correlacao entre sono e humor, estudo e progresso, exercicio e humor
- forecast simples:
  `Se continuar assim, seu humor medio pode chegar a X em 7 dias`
- streak atual, melhor streak e meta semanal visual
- API pronta para integracao com frontend mais moderno ou app mobile

## Como rodar localmente

### 1. Ambiente virtual

```powershell
uv venv .venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

### 2. Configuracao

Crie o arquivo `.env` a partir do `.env.example`.

```env
FLASK_ENV=development
SECRET_KEY=change-me-before-production
DATABASE_URL=sqlite:///instance/mindtrack.db
CACHE_TTL_SECONDS=45
LOG_LEVEL=INFO
```

### 3. Executar

```powershell
$env:FLASK_APP = "app.py"
flask run
```

Acesse: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Testes

```powershell
pytest
```

## API principal

- `GET /api/dashboard`
- `GET /api/entries`
- `POST /api/entries`
- `PUT /api/entries/<id>`
- `DELETE /api/entries/<id>`
- `GET /api/analytics`
- `GET /api/insights`
- `GET /api/forecast`

Todas as respostas seguem o formato:

```json
{
  "success": true,
  "data": {}
}
```

## Deploy no Render

O repositorio ja inclui `render.yaml` e esta pronto para subir com:

- build command: `pip install -r requirements.txt`
- start command: `gunicorn app:app`
- variaveis obrigatorias:
  - `SECRET_KEY`
  - `DATABASE_URL`
  - `FLASK_ENV=production`

Para producao, use PostgreSQL do proprio Render ou Railway.

## Fluxo do produto

1. usuario cria conta e faz login
2. registra o dia em um unico formulario
3. o sistema salva no banco
4. analytics, forecast e insights sao recalculados
5. dashboard mostra score, tendencias, comparacoes e recomendacoes

## Status atual

- repositorio versionado e publicado no GitHub
- base pronta para deploy
- README atualizado para recrutador e avaliador tecnico

## Proximos upgrades naturais

- screenshots reais do dashboard no README
- filtros mensal e trimestral
- notificacoes e lembretes
- exportacao PDF
- deploy online final com URL publica
