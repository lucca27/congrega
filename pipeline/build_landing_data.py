"""Converte a base do pipeline (data/events.json, schema rico) para o formato
compacto que a landing consome (landing/events.json): uma lista de tuplas
[nome, ini, fim, cidade, uf, especialidade, nº_fontes, url?, cfp?].

A landing tenta `fetch('events.json')`; se existir, usa; senão, cai no catálogo
embutido no próprio HTML.

Uso: python build_landing_data.py
"""
import json
import os

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "data", "events.json")
if not os.path.exists(SRC):
    SRC = os.path.join(HERE, "data", "events.seed.json")
OUT = os.path.join(HERE, "..", "landing", "events.json")


def cfp_label(ev):
    c = ev.get("call_for_papers") or {}
    if not c.get("aberto"):
        return None
    return c.get("prazo_final") or "aberta"   # data ISO, ou marca "aberta"


def to_row(ev):
    s = len(ev.get("fontes") or []) or 1
    row = [ev["nome"], ev.get("data_inicio"), ev.get("data_fim"),
           ev.get("cidade") or "", ev.get("uf") or "", ev.get("especialidade") or "Outros", s]
    url = ev.get("url_inscricao")
    cfp = cfp_label(ev)
    if url or cfp:
        row.append(url)          # pode ser None -> landing cai na busca
    if cfp:
        row.append(cfp)
    return row


def main():
    doc = json.load(open(SRC))
    evs = sorted(doc["eventos"], key=lambda e: (e.get("data_inicio") or "9999"))
    rows = [to_row(e) for e in evs]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rows, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
    com_link = sum(1 for r in rows if len(r) > 7 and r[7])
    print(f"✓ {len(rows)} eventos ({com_link} com link oficial) → landing/events.json")


if __name__ == "__main__":
    main()
