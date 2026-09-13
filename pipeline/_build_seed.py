"""Gera data/events.seed.json a partir dos dados REAIS coletados de duas fontes
(bip e AgrupaMED, set/2026) rodando-os pela dedup.py de verdade.

Serve de demonstração: mesmos eventos, fontes diferentes, saída normalizada e
deduplicada — exatamente o que o extractor de IA produziria em produção.
"""
import datetime as dt
import json
import os

from dedup import dedup
from models import CallForPapers, Fonte, MedEvent

AGORA = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
F_BIP = Fonte("bip", "https://www.usebip.com/blogs/bip-insights/calendario-de-congressos-medicos-2026", AGORA)
F_AGR = Fonte("AgrupaMED", "https://agrupamed.com.br/congressos", AGORA)

# (nome, ini, fim, cidade, uf, online, especialidade)  — transcritos das fontes
BIP = [
    ("Congresso Internacional EB2026", "2026-01-20", "2026-01-22", "São Paulo", "SP", False, "Dermatologia"),
    ("2nd South Atlantic Forum on Osteoarthritis", "2026-02-27", "2026-02-28", "São Paulo", "SP", False, "Ortopedia e Traumatologia"),
    ("XII Congresso Latinoamericano de Cuidados Paliativos", "2026-03-11", "2026-03-14", "São Paulo", "SP", False, "Cuidados Paliativos"),
    ("Congresso Norte e Nordeste de Oftalmologia 2026", "2026-03-19", "2026-03-21", "Fortaleza", "CE", False, "Oftalmologia"),
    ("ABN Summit Sul", "2026-03-20", "2026-03-21", "Curitiba", "PR", False, "Neurologia"),
    ("Congresso Clínica Psiquiátrica (CCP)", "2026-03-26", "2026-03-28", "São Paulo", "SP", False, "Psiquiatria"),
    ("2º Congresso dos Departamentos da SBC", "2026-04-10", "2026-04-11", "Belo Horizonte", "MG", False, "Cardiologia"),
    ("Congresso Internacional de Uro-Oncologia 2026", "2026-04-15", "2026-04-18", "São Paulo", "SP", False, "Urologia"),
    ("20º Congresso Brasileiro de Coluna (CSBC)", "2026-04-18", "2026-04-21", "Curitiba", "PR", False, "Ortopedia e Traumatologia"),
    ("Jornada Paulista de Radiologia (JPR)", "2026-04-30", "2026-05-03", "São Paulo", "SP", False, "Radiologia"),
    ("43º Congresso SOCERJ", "2026-05-07", "2026-05-08", "Rio de Janeiro", "RJ", False, "Cardiologia"),
    ("63º Congresso Brasileiro de Ginecologia e Obstetrícia", "2026-05-27", "2026-05-30", "Belo Horizonte", "MG", False, "Ginecologia e Obstetrícia"),
    ("GASTRÃO 2026", "2026-06-24", "2026-06-26", "São Paulo", "SP", False, "Gastroenterologia"),
    ("88º Congresso da SBO", "2026-07-02", "2026-07-04", "Rio de Janeiro", "RJ", False, "Oftalmologia"),
    ("26ª Conferência Internacional sobre AIDS (AIDS 2026)", "2026-07-25", "2026-07-30", "Rio de Janeiro", "RJ", False, "Infectologia"),
    ("XXXVI Congresso Brasileiro de Neurocirurgia", "2026-08-11", "2026-08-15", "Rio de Janeiro", "RJ", False, "Neurocirurgia"),
    ("31º Congresso Brasileiro de Endocrinologia e Metabologia", "2026-08-26", "2026-08-29", "Rio de Janeiro", "RJ", False, "Endocrinologia"),
    ("43º Congresso Brasileiro de Reumatologia", "2026-09-02", "2026-09-05", "Curitiba", "PR", False, "Reumatologia"),
    ("79º Congresso Brasileiro de Dermatologia", "2026-09-10", "2026-09-12", "Fortaleza", "CE", False, "Dermatologia"),
    ("58º Congresso Anual SBOT 2026", "2026-11-18", "2026-11-20", "Porto Alegre", "RS", False, "Ortopedia e Traumatologia"),
    ("Congresso Brasileiro de Anestesiologia", "2026-11-26", "2026-11-29", "Fortaleza", "CE", False, "Anestesiologia"),
    ("XXII Congresso Brasileiro do Sono", "2026-12-02", "2026-12-05", None, None, False, "Outros"),
    # --- os 9 abaixo também aparecem na AgrupaMED (devem deduplicar) ---
    ("XXXIII Congresso Brasileiro de Nefrologia", "2026-09-16", "2026-09-19", "Belo Horizonte", "MG", False, "Nefrologia"),
    ("64º COBEM – Congresso Brasileiro de Educação Médica", "2026-09-17", "2026-09-20", "Porto Alegre", "RS", False, "Educação Médica"),
    ("55º Congresso Brasileiro de Radiologia (CBR26)", "2026-09-17", "2026-09-19", "Recife", "PE", False, "Radiologia"),
    ("74º Congresso Brasileiro de Coloproctologia", "2026-09-24", "2026-09-26", "Balneário Camboriú", "SC", False, "Coloproctologia"),
    ("20th World Congress on Menopause", "2026-09-30", "2026-10-03", "Rio de Janeiro", "RJ", False, "Ginecologia e Obstetrícia"),
    ("XXXII Congresso Brasileiro de Neurologia", "2026-10-07", "2026-10-10", "Rio de Janeiro", "RJ", False, "Neurologia"),
    ("81º Congresso Brasileiro de Cardiologia", "2026-10-08", "2026-10-10", "Rio de Janeiro", "RJ", False, "Cardiologia"),
    ("42º Congresso Brasileiro de Pediatria", "2026-10-13", "2026-10-17", "Belo Horizonte", "MG", False, "Pediatria"),
    ("XLIII Congresso Brasileiro de Psiquiatria", "2026-10-28", "2026-10-31", "São Paulo", "SP", False, "Psiquiatria"),
]

AGRUPAMED = [
    # os 9 duplicados (mesmo nome canônico, dados às vezes mais completos)
    ("XXXIII Congresso Brasileiro de Nefrologia", "2026-09-16", "2026-09-19", "Belo Horizonte", "MG", False, "Nefrologia"),
    ("64º COBEM – Congresso Brasileiro de Educação Médica", "2026-09-17", "2026-09-20", "Porto Alegre", "RS", False, "Educação Médica"),
    ("55º Congresso Brasileiro de Radiologia (CBR26)", "2026-09-17", "2026-09-19", "Recife", "PE", False, "Radiologia"),
    ("74º Congresso Brasileiro de Coloproctologia", "2026-09-24", "2026-09-26", "Balneário Camboriú", "SC", False, "Coloproctologia"),
    ("20th World Congress on Menopause", "2026-09-30", "2026-10-03", "Rio de Janeiro", "RJ", False, "Ginecologia e Obstetrícia"),
    ("XXXII Congresso Brasileiro de Neurologia", "2026-10-07", "2026-10-12", "Rio de Janeiro", "RJ", False, "Neurologia"),
    ("81º Congresso Brasileiro de Cardiologia", "2026-10-08", "2026-10-10", "Rio de Janeiro", "RJ", False, "Cardiologia"),
    ("42º Congresso Brasileiro de Pediatria", "2026-10-13", "2026-10-17", "Belo Horizonte", "MG", False, "Pediatria"),
    ("XLIII Congresso Brasileiro de Psiquiatria", "2026-10-28", "2026-10-31", "São Paulo", "SP", False, "Psiquiatria"),
    # únicos da AgrupaMED
    ("XIV Congresso Mineiro de Clínica Médica", "2026-09-23", "2026-09-26", "Belo Horizonte", "MG", False, "Clínica Médica"),
    ("XXX Congresso Brasileiro de Nutrologia 2026", "2026-09-24", "2026-09-26", "São Paulo", "SP", False, "Nutrologia"),
    ("46º Congresso Brasileiro de Angiologia e Cirurgia Vascular", "2026-10-05", "2026-10-09", "Salvador", "BA", False, "Cirurgia Vascular"),
    ("Congresso Sul-brasileiro de Clínica Médica", "2026-10-09", "2026-10-11", "Florianópolis", "SC", False, "Clínica Médica"),
    ("13º Congresso de Cirurgia Plástica e Cosmiatria (CBCP)", "2026-10-09", "2026-10-11", "São Paulo", "SP", False, "Cirurgia Plástica"),
    ("30º Congresso Brasileiro de Ultrassonografia da SBUS", "2026-10-14", "2026-10-17", "São Paulo", "SP", False, "Radiologia"),
    ("14º Congresso Paulista de Clínica Médica", "2026-10-16", "2026-10-17", "Campinas", "SP", False, "Clínica Médica"),
    ("Congresso Brasileiro de Hematologia (HEMO 2026)", "2026-10-28", "2026-10-31", "Rio de Janeiro", "RJ", False, "Hematologia"),
    ("8º Congresso Internacional Sabará-Pensi de Saúde Infantil", "2026-10-01", "2026-10-03", "São Paulo", "SP", False, "Pediatria"),
]


def make(row, fonte):
    nome, ini, fim, cidade, uf, online, esp = row
    return MedEvent(id="", nome=nome, data_inicio=ini, data_fim=fim, cidade=cidade,
                    uf=uf, online=online, especialidade=esp,
                    call_for_papers=CallForPapers(), fontes=[fonte])


def main():
    brutos = [make(r, F_BIP) for r in BIP] + [make(r, F_AGR) for r in AGRUPAMED]
    final = dedup(brutos)
    final.sort(key=lambda e: (e.data_inicio or "9999"))
    out = os.path.join(os.path.dirname(__file__), "data", "events.seed.json")
    payload = {"gerado_em": AGORA, "brutos_coletados": len(brutos),
               "total": len(final), "eventos": [e.to_dict() for e in final]}
    json.dump(payload, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"{len(brutos)} brutos → {len(final)} únicos ({len(brutos) - len(final)} duplicatas mescladas)")
    print(f"✓ {out}")


if __name__ == "__main__":
    main()
