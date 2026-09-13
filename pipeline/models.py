"""Schema canônico de um evento médico + JSON Schema usado na extração por IA.

O pipeline inteiro converge para `MedEvent`: não importa se a fonte é o site
de uma sociedade, um agregador ou a API da Even3 — tudo vira este formato.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional


# Taxonomia de especialidades. Normalizar aqui é o que permite filtrar
# "todos os eventos de cardiologia do Brasil" mesmo que cada fonte escreva diferente.
ESPECIALIDADES = [
    "Cardiologia", "Pediatria", "Ortopedia e Traumatologia", "Dermatologia",
    "Ginecologia e Obstetrícia", "Neurologia", "Neurocirurgia", "Oftalmologia",
    "Psiquiatria", "Clínica Médica", "Radiologia", "Urologia", "Oncologia",
    "Endocrinologia", "Gastroenterologia", "Nefrologia", "Pneumologia",
    "Infectologia", "Anestesiologia", "Cirurgia Geral", "Cirurgia Plástica",
    "Cirurgia Vascular", "Geriatria", "Reumatologia", "Hematologia",
    "Medicina Intensiva", "Medicina de Emergência", "Medicina de Família e Comunidade",
    "Coloproctologia", "Otorrinolaringologia", "Patologia", "Nutrologia",
    "Medicina Física e Reabilitação", "Educação Médica", "Medicina Estética",
    "Cuidados Paliativos", "Medicina Tropical", "Outros",
]


@dataclass
class CallForPapers:
    """Submissão de trabalhos científicos — diferencial para residente/acadêmico."""
    aberto: Optional[bool] = None       # None = desconhecido (precisa enriquecer)
    prazo_final: Optional[str] = None   # ISO date "YYYY-MM-DD"
    url: Optional[str] = None


@dataclass
class Fonte:
    nome: str            # ex.: "AgrupaMED", "SBC", "Even3"
    url: str
    coletado_em: str     # ISO datetime


@dataclass
class MedEvent:
    id: str                              # slug estável p/ dedup (ver dedup.py)
    nome: str
    data_inicio: Optional[str]           # ISO "YYYY-MM-DD"
    data_fim: Optional[str]              # ISO "YYYY-MM-DD"
    cidade: Optional[str]
    uf: Optional[str]                    # sigla estado, ou "ONLINE"
    online: bool = False
    especialidade: str = "Outros"
    edicao: Optional[str] = None         # ex.: "81º"
    url_inscricao: Optional[str] = None
    # --- camada profunda (preenchida no passo de enriquecimento) ---
    pontos_cap: Optional[int] = None     # pontos de acreditação CAP/CNA
    call_for_papers: CallForPapers = field(default_factory=CallForPapers)
    # --- proveniência / qualidade ---
    fontes: list[Fonte] = field(default_factory=list)
    confianca: float = 1.0               # 0..1 confiança da extração

    def to_dict(self) -> dict:
        return asdict(self)


# JSON Schema entregue ao modelo para forçar saída estruturada (tool use).
# Só os campos que dá pra extrair da LISTAGEM; pontos_cap e call_for_papers
# vêm depois, no passo de enriquecimento por evento.
EXTRACTION_TOOL = {
    "name": "registrar_eventos",
    "description": "Registra os eventos médicos encontrados no texto da fonte.",
    "input_schema": {
        "type": "object",
        "properties": {
            "eventos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "edicao": {"type": ["string", "null"],
                                    "description": "ex.: '81º', '42º'. null se não houver."},
                        "data_inicio": {"type": ["string", "null"],
                                         "description": "ISO YYYY-MM-DD. null se indefinida."},
                        "data_fim": {"type": ["string", "null"], "description": "ISO YYYY-MM-DD."},
                        "cidade": {"type": ["string", "null"]},
                        "uf": {"type": ["string", "null"],
                                "description": "Sigla do estado (SP, RJ...). 'ONLINE' se remoto."},
                        "online": {"type": "boolean"},
                        "especialidade": {"type": "string", "enum": ESPECIALIDADES},
                        "url_inscricao": {"type": ["string", "null"]},
                    },
                    "required": ["nome", "especialidade", "online"],
                },
            }
        },
        "required": ["eventos"],
    },
}
