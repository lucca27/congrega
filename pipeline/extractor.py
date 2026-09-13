"""Passo de IA: HTML bagunçado de qualquer fonte -> lista de eventos estruturados.

É aqui que o "tudo automático" acontece. Cada fonte tem HTML diferente; o
modelo lê o texto e devolve sempre o mesmo schema (models.EXTRACTION_TOOL).
"""
from __future__ import annotations

import os
import re

from models import EXTRACTION_TOOL

# Extração é alto volume -> use um modelo barato/rápido. Sonnet dá margem de
# qualidade; troque por 'claude-haiku-4-5-20251001' para reduzir custo em escala.
MODEL = os.environ.get("MED_EXTRACTOR_MODEL", "claude-sonnet-5")

PROMPT = """Você extrai eventos médicos de um texto de fonte brasileira.
Regras:
- Extraia SÓ eventos reais (congressos, jornadas, simpósios, cursos). Ignore menus, rodapés e anúncios.
- Datas sempre em ISO YYYY-MM-DD. Se só houver mês, use o dia 01 e reduza a confiança implícita omitindo o dia exato quando impossível.
- 'uf' é a sigla do estado (SP, RJ, MG...). Se for remoto, online=true e uf="ONLINE".
- 'especialidade' DEVE ser um dos valores permitidos; use "Outros" se nenhum servir.
- Não invente. Se um campo não estiver no texto, use null.
Chame a ferramenta registrar_eventos com tudo que encontrar."""


def html_to_text(html: str) -> str:
    """Redução barata de HTML->texto antes de mandar pro modelo (economiza tokens)."""
    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;|&amp;", " ", text)
    return re.sub(r"[ \t]*\n[ \t\n]*", "\n", re.sub(r"[ \t]+", " ", text)).strip()


def extract_events(source_text: str) -> list[dict]:
    """Chama o modelo com saída estruturada. Retorna lista de dicts de evento cru."""
    from anthropic import Anthropic  # import tardio: só precisa da lib se rodar de verdade

    client = Anthropic()  # usa ANTHROPIC_API_KEY do ambiente
    msg = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "registrar_eventos"},
        messages=[{"role": "user",
                   "content": f"{PROMPT}\n\n=== TEXTO DA FONTE ===\n{source_text[:120000]}"}],
    )
    for block in msg.content:
        if block.type == "tool_use" and block.name == "registrar_eventos":
            return block.input.get("eventos", [])
    return []
