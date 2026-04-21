# MindTrack-Life

MindTrack-Life e um sistema web em Flask para acompanhar habitos, diario emocional e evolucao pessoal com foco em autoconhecimento orientado por dados.

## O que o projeto entrega

- autenticacao com cadastro, login e sessoes por usuario
- registro diario em tela unica com sono, estudo, exercicio, leitura, lazer, humor, energia, progresso e notas
- CRUD completo dos registros
- dashboard dark mode com cards, graficos e insights
- API REST em JSON para dashboard e registros
- analise comportamental com medias, tendencias, correlacoes e Life Score
- exportacao automatica de CSV por usuario

## Arquitetura

```text
MindTrack-Life/
|-- app.py
|-- mindtrack/
|   |-- __init__.py
|   |-- auth.py
|   |-- database.py
|   |-- models/
|   |-- routes/
|   |-- services/
|-- templates/
|-- static/
|-- instance/
|-- requirements.txt
```

## Como rodar

### 1. Criar e ativar ambiente virtual

Se voce tiver Python 3.12+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se preferir usar `uv`:

```powershell
uv venv .venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

### 2. Executar a aplicacao

```powershell
$env:FLASK_APP = "app.py"
flask run
```

Depois abra `http://127.0.0.1:5000`.

## Endpoints principais

- `GET /api/dashboard`
- `GET /api/entries`
- `POST /api/entries`
- `PUT /api/entries/<id>`
- `DELETE /api/entries/<id>`

## Git e GitHub

Para conectar com o repositrio remoto:

```powershell
git init
git branch -M main
git remote add origin https://github.com/guilhermemichael/MindTrack-Life.git
git add .
git commit -m "feat: scaffold initial MindTrack-Life platform"
git push -u origin main
```

## Proximas evolucoes sugeridas

- migracao para PostgreSQL
- tasks assincronas para insights mais pesados
- notificacoes e lembretes
- comparativos semanal e mensal
- deploy em Render ou Railway
