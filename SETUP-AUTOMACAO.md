# Automação do Congrega — setup (conta PESSOAL)

> ⚠️ **Nada disto deve tocar o ambiente ou as contas da publica.la.**
> Use uma conta GitHub **pessoal** e chaves de API **pessoais**. As chaves ficam
> nos *Secrets* do GitHub — nunca no código, nunca no chat, nunca commitadas.

Depois de configurado, o pipeline roda sozinho (cron semanal) e publica o site.
Ele **funciona mesmo sem chave nenhuma** — nesse caso só reempacota o catálogo
atual e publica; conforme você adiciona as chaves, ele passa a descobrir e
enriquecer automaticamente.

## Passo a passo (uma vez)

1. **Crie um repositório pessoal** (ex.: `congrega`) na sua conta GitHub pessoal
   e suba esta pasta:
   ```bash
   cd "APP - conectar pessoas a congressos"
   git init && git add . && git commit -m "Congrega: pipeline + landing"
   git branch -M main
   git remote add origin git@github.com:SEU-USUARIO-PESSOAL/congrega.git
   git push -u origin main
   ```

2. **Ative o GitHub Pages:** repositório → *Settings* → *Pages* →
   *Build and deployment* → *Source: **GitHub Actions***.

3. **(Opcional) Adicione as chaves** em *Settings* → *Secrets and variables* →
   *Actions* → *New repository secret*:
   - `ANTHROPIC_API_KEY` — habilita a descoberta (`ingest.py`)
   - `MISTRAL_API_KEY` — habilita o enriquecimento (`enrich.py`)
   Sem elas, o site ainda publica com o catálogo atual.

4. **Rode uma vez à mão:** aba *Actions* → *pipeline-congrega* → *Run workflow*.
   Ao terminar, o site fica em `https://SEU-USUARIO.github.io/congrega/`.

Depois disso, o cron (`0 6 * * 1` — segundas 06:00 UTC) roda tudo sozinho,
commita o catálogo atualizado e republica o site. Ajuste o horário em
`.github/workflows/pipeline.yml`.

## Rodar localmente (sem nuvem)

```bash
cd pipeline
export ANTHROPIC_API_KEY=...   # opcional
export MISTRAL_API_KEY=...     # opcional
python3 run_pipeline.py        # descoberta → enriquecimento → build
```
Depois sirva a landing: `cd ../landing && python3 -m http.server 4173`.

## Peças
| Arquivo | Papel |
|---|---|
| `pipeline/run_pipeline.py` | orquestra ingest → enrich → build |
| `pipeline/ingest.py` | descoberta (Anthropic) |
| `pipeline/enrich.py` | links + CAP + call-for-papers (Mistral) |
| `pipeline/build_landing_data.py` | gera `landing/events.json` |
| `.github/workflows/pipeline.yml` | cron + publicação no GitHub Pages |
| `landing/index.html` | o site (consome `events.json`, com fallback embutido) |
