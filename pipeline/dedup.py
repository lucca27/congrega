"""Deduplicação: o mesmo congresso aparece em várias fontes.

Estratégia: chave = (nome canônico sem edição/ano) + ano da data_inicio.
Ao encontrar duplicata, mescla as fontes e mantém o registro mais completo.
"""
from __future__ import annotations

import re
import unicodedata

from models import MedEvent


_STOP = re.compile(
    r"\b(\d+[º°ª]?|congresso|brasileiro|brasileira|internacional|nacional|"
    r"jornada|simposio|reuniao|anual|de|da|do|dos|das|e|em|the|of|and)\b",
    re.IGNORECASE,
)


def _slug(nome: str) -> str:
    """Reduz o nome a um núcleo comparável: sem acento, sem edição, sem palavras-ruído."""
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    s = _STOP.sub(" ", s.lower())
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return "-".join(sorted(set(s.split())))  # ordena p/ tolerar ordem diferente de palavras


def event_id(nome: str, data_inicio: str | None) -> str:
    ano = (data_inicio or "____")[:4]
    return f"{_slug(nome)}--{ano}"


def _completeness(e: MedEvent) -> int:
    """Quantos campos úteis o registro tem — usado p/ escolher o 'vencedor' na mescla."""
    campos = [e.data_inicio, e.data_fim, e.cidade, e.uf, e.url_inscricao,
              e.edicao, e.pontos_cap]
    return sum(1 for c in campos if c)


def dedup(eventos: list[MedEvent]) -> list[MedEvent]:
    por_id: dict[str, MedEvent] = {}
    for ev in eventos:
        ev.id = event_id(ev.nome, ev.data_inicio)
        if ev.id not in por_id:
            por_id[ev.id] = ev
            continue
        # já existe: mantém o mais completo e une as fontes
        atual = por_id[ev.id]
        vencedor, perdedor = (ev, atual) if _completeness(ev) > _completeness(atual) else (atual, ev)
        vencedor.fontes = _merge_fontes(atual.fontes, ev.fontes)
        # preenche buracos do vencedor com dados do perdedor
        for campo in ("data_inicio", "data_fim", "cidade", "uf", "edicao",
                      "url_inscricao", "pontos_cap"):
            if not getattr(vencedor, campo) and getattr(perdedor, campo):
                setattr(vencedor, campo, getattr(perdedor, campo))
        por_id[ev.id] = vencedor
    return list(por_id.values())


def _merge_fontes(a, b):
    vistos, out = set(), []
    for f in [*a, *b]:
        if f.nome not in vistos:
            vistos.add(f.nome)
            out.append(f)
    return out
