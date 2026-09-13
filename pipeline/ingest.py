"""Orquestrador do pipeline: fontes -> fetch -> IA -> normaliza -> dedup -> JSON.

Uso:
    python ingest.py                 # roda de verdade (precisa ANTHROPIC_API_KEY)
    python ingest.py --demo          # não chama IA: mostra o catálogo-semente já extraído
    python ingest.py --stats         # imprime estatísticas do catálogo atual

O passo de enriquecimento (pontos CAP + call-for-papers por evento) é um
segundo estágio, ainda não incluído aqui — ver README.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from collections import Counter

from dedup import dedup
from extractor import extract_events, html_to_text
from models import CallForPapers, Fonte, MedEvent

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "data", "events.json")
SEED = os.path.join(HERE, "data", "events.seed.json")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "MedEventsBot/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def _raw_to_event(raw: dict, fonte: Fonte) -> MedEvent:
    return MedEvent(
        id="",  # atribuído no dedup
        nome=raw["nome"].strip(),
        edicao=raw.get("edicao"),
        data_inicio=raw.get("data_inicio"),
        data_fim=raw.get("data_fim"),
        cidade=raw.get("cidade"),
        uf=raw.get("uf"),
        online=raw.get("online", False),
        especialidade=raw.get("especialidade", "Outros"),
        url_inscricao=raw.get("url_inscricao"),
        call_for_papers=CallForPapers(),
        fontes=[fonte],
    )


def run() -> list[MedEvent]:
    import yaml  # pip install pyyaml (só necessário na coleta ao vivo)
    cfg = yaml.safe_load(open(os.path.join(HERE, "sources.yaml")))
    agora = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    coletados: list[MedEvent] = []
    for s in cfg["sources"]:
        if not s.get("ativo") or s["tipo"] != "html":
            continue
        print(f"→ coletando {s['nome']} ...", file=sys.stderr)
        try:
            texto = html_to_text(fetch(s["url"]))
            fonte = Fonte(nome=s["nome"], url=s["url"], coletado_em=agora)
            brutos = extract_events(texto)
            coletados += [_raw_to_event(b, fonte) for b in brutos]
            print(f"  {len(brutos)} eventos", file=sys.stderr)
        except Exception as e:  # uma fonte quebrada não derruba o resto
            print(f"  ERRO em {s['nome']}: {e}", file=sys.stderr)
    final = dedup(coletados)
    save(final)
    return final


def save(eventos: list[MedEvent]) -> None:
    payload = {"gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "total": len(eventos),
               "eventos": [e.to_dict() for e in eventos]}
    json.dump(payload, open(OUT, "w"), ensure_ascii=False, indent=2)
    print(f"✓ {len(eventos)} eventos únicos → {OUT}", file=sys.stderr)


def stats(path: str) -> None:
    data = json.load(open(path))
    evs = data["eventos"]
    print(f"Catálogo: {len(evs)} eventos únicos ({os.path.basename(path)})\n")
    esp = Counter(e["especialidade"] for e in evs)
    print("Por especialidade (top 12):")
    for k, v in esp.most_common(12):
        print(f"  {v:3d}  {k}")
    uf = Counter(e["uf"] for e in evs if e["uf"])
    print("\nPor UF (top 8):")
    for k, v in uf.most_common(8):
        print(f"  {v:3d}  {k}")
    multi = [e for e in evs if len(e["fontes"]) > 1]
    print(f"\nEventos confirmados por 2+ fontes (dedup): {len(multi)}")
    for e in multi[:8]:
        print(f"  • {e['nome']}  [{', '.join(f['nome'] for f in e['fontes'])}]")
    com_cfp = [e for e in evs if e["call_for_papers"].get("aberto")]
    com_cap = [e for e in evs if e.get("pontos_cap")]
    print(f"\nCom call-for-papers aberto: {len(com_cfp)}   |   Com pontos CAP: {len(com_cap)}")
    print("(ambos ~0 até rodar o passo de enriquecimento por evento)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="usa o catálogo-semente, sem chamar IA")
    ap.add_argument("--stats", action="store_true", help="só imprime estatísticas")
    args = ap.parse_args()

    if args.stats:
        stats(OUT if os.path.exists(OUT) else SEED)
    elif args.demo:
        stats(SEED)
        print(f"\n(demo: catálogo-semente em {SEED} — rode sem --demo p/ coletar ao vivo)")
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("Defina ANTHROPIC_API_KEY, ou use --demo para ver o catálogo-semente.")
        run()
        stats(OUT)
