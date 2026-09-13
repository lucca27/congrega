"""Estágio 2 — enriquecimento por evento (via API da Mistral, com busca web).

Para cada evento do catálogo, a IA busca na web a página OFICIAL e extrai:
  • url_inscricao  — o link real do evento (vira o clique "Inscrições" no app)
  • pontos_cap     — pontos de acreditação CAP/CNA, se divulgados
  • call_for_papers — se a submissão de trabalhos está aberta e o prazo

Usa a Conversations API da Mistral com o conector nativo `web_search`.
Docs: https://docs.mistral.ai/agents/connectors/websearch/

Uso:
    export MISTRAL_API_KEY=...            # NUNCA cole a chave no código/chat
    python enrich.py                      # enriquece só o que falta
    python enrich.py --force              # reenriquece tudo (dados mudam no ano)
    python enrich.py --limit 5            # testa em poucos
    python enrich.py --limit 1 --debug    # imprime a resposta crua da Mistral
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data", "events.json")
if not os.path.exists(DATA):
    DATA = os.path.join(HERE, "data", "events.seed.json")

API_URL = "https://api.mistral.ai/v1/conversations"
MODEL = os.environ.get("MED_ENRICH_MODEL", "mistral-medium-latest")
KEY = os.environ.get("MISTRAL_API_KEY", "")

PROMPT = """Você enriquece o cadastro de um congresso médico brasileiro.
Evento: "{nome}" — {cidade}/{uf}, {data}.

Busque na web a PÁGINA OFICIAL do evento (site próprio, ou página no Even3/Sympla/Doity).
Depois responda SOMENTE com um objeto JSON, sem texto ao redor, no formato:
{{"url_inscricao": "<url oficial, ou null>",
  "pontos_cap": <inteiro de pontos CAP/CNA divulgados, ou null>,
  "call_for_papers": {{"aberto": <true|false|null>, "prazo_final": "<YYYY-MM-DD|null>", "url": "<url|null>"}},
  "confianca": <0 a 1>}}
Regras: não invente. Se não achar a página oficial com segurança, url_inscricao=null.
Só preencha pontos_cap/call_for_papers se estiverem explícitos. Datas em ISO."""


def call_mistral(prompt: str) -> dict:
    body = json.dumps({
        "model": MODEL,
        "tools": [{"type": "web_search"}],
        "inputs": prompt,
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")


def extract_text(resp: dict) -> str:
    """Junta o texto da resposta, ignorando as execuções de ferramenta (busca)."""
    parts = []
    for o in resp.get("outputs", []):
        if "tool" in o.get("type", ""):
            continue
        c = o.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for ch in c:
                if isinstance(ch, dict) and ch.get("text"):
                    parts.append(ch["text"])
                elif isinstance(ch, str):
                    parts.append(ch)
    return "\n".join(parts)


def enrich_one(ev: dict, debug: bool = False) -> dict | None:
    data = ev.get("data_inicio") or "2026"
    resp = call_mistral(PROMPT.format(
        nome=ev["nome"], cidade=ev.get("cidade") or "?",
        uf=ev.get("uf") or "?", data=data))
    if debug:
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:2000], file=sys.stderr)
    text = extract_text(resp)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def needs_enrich(ev: dict) -> bool:
    return not ev.get("url_inscricao") and not ev.get("_enriched")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--debug", action="store_true", help="imprime a resposta crua da Mistral")
    args = ap.parse_args()
    if not KEY:
        sys.exit("Defina MISTRAL_API_KEY no ambiente (export MISTRAL_API_KEY=...).")

    doc = json.load(open(DATA))
    evs = doc["eventos"]
    alvos = [e for e in evs if args.force or needs_enrich(e)]
    if args.limit:
        alvos = alvos[:args.limit]
    print(f"Enriquecendo {len(alvos)} de {len(evs)} eventos com {MODEL}…", file=sys.stderr)

    for i, ev in enumerate(alvos, 1):
        try:
            got = enrich_one(ev, debug=args.debug)
        except Exception as e:
            print(f"  [{i}] ERRO {ev['nome'][:40]}: {e}", file=sys.stderr)
            continue
        if got:
            ev["url_inscricao"] = got.get("url_inscricao") or ev.get("url_inscricao")
            if got.get("pontos_cap") is not None:
                ev["pontos_cap"] = got["pontos_cap"]
            if isinstance(got.get("call_for_papers"), dict):
                ev["call_for_papers"] = got["call_for_papers"]
            ev["_enriched"] = True
            tag = "✓ link" if ev.get("url_inscricao") else "· sem link"
            cap = f" · {ev['pontos_cap']}pts" if ev.get("pontos_cap") else ""
            print(f"  [{i}/{len(alvos)}] {tag}{cap}  {ev['nome'][:44]}", file=sys.stderr)
        json.dump(doc, open(DATA, "w"), ensure_ascii=False, indent=2)  # salva incremental
        time.sleep(1)  # gentil com rate limit

    com_link = sum(1 for e in evs if e.get("url_inscricao"))
    print(f"\n✓ {com_link}/{len(evs)} eventos com link oficial → {DATA}", file=sys.stderr)


if __name__ == "__main__":
    main()
