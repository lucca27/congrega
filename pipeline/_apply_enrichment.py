"""Grava na base do pipeline os enriquecimentos já verificados (links oficiais +
call-for-papers + 2 correções de edição). Reproduz, na fonte de dados, o que o
enrich.py faria — para a base ficar consistente com a landing.

Roda uma vez: python _apply_enrichment.py
"""
import json
import os

HERE = os.path.dirname(__file__)

# nome_original -> {url, cfp?, nome?(renomear)}
PATCH = {
    "ABN Summit Sul": {"url": "https://abneuro.iweventos.com.br/summits2026"},
    "Jornada Paulista de Radiologia (JPR)": {"url": "https://www.spr.org.br/evento/416/jornada-paulista-de-radiologia/sobre-a-jpr"},
    "43º Congresso SOCERJ": {"url": "https://socerj.org.br"},
    "63º Congresso Brasileiro de Ginecologia e Obstetrícia": {"url": "https://cbgo2026.com.br/"},
    "26ª Conferência Internacional sobre AIDS (AIDS 2026)": {"url": "https://www.aids2026.org"},
    "XXXVI Congresso Brasileiro de Neurocirurgia": {"url": "https://cbn2026.com.br/"},
    "31º Congresso Brasileiro de Endocrinologia e Metabologia": {
        "url": "https://cbemsbem.com.br/",
        "nome": "37º Congresso Brasileiro de Endocrinologia e Metabologia (CBEM 2026)"},
    "43º Congresso Brasileiro de Reumatologia": {"url": "https://sbr2026.eventize.com.br/"},
    "79º Congresso Brasileiro de Dermatologia": {"url": "https://eventos.sbd.org.br/79csbd/"},
    "XXXIII Congresso Brasileiro de Nefrologia": {"url": "https://congressonefro.com.br/"},
    "64º COBEM – Congresso Brasileiro de Educação Médica": {
        "url": "https://cobem.com.br/2026/",
        "cfp": {"aberto": True, "prazo_final": None, "url": "https://cobem.com.br/2026/"}},
    "55º Congresso Brasileiro de Radiologia (CBR26)": {"url": "https://cbr.org.br/en/atividades-cbr/55o-congresso-brasileiro-de-radiologia-e-diagnostico-por-imagem-cbr26/"},
    "74º Congresso Brasileiro de Coloproctologia": {"url": "https://coloprocto2026.com.br/"},
    "20th World Congress on Menopause": {"url": "https://imsrio2026.com/"},
    "XXXII Congresso Brasileiro de Neurologia": {"url": "https://congressoabneuro2026.com.br/"},
    "81º Congresso Brasileiro de Cardiologia": {"url": "https://sbc.iweventos.com.br/cardio2026"},
    "42º Congresso Brasileiro de Pediatria": {"url": "https://cbpediatria.com.br/"},
    "XLIII Congresso Brasileiro de Psiquiatria": {
        "url": "https://cbpabp.org.br/",
        "cfp": {"aberto": True, "prazo_final": "2026-04-12", "url": "https://cbpabp.org.br/"}},
    "Congresso Brasileiro de Hematologia (HEMO 2026)": {"url": "https://hemo.org.br/hemo2026"},
    "58º Congresso Anual SBOT 2026": {"url": "https://sbot.org.br/congresso/"},
    "Congresso Brasileiro de Anestesiologia": {
        "url": "https://cba2026.com.br/",
        "nome": "71º Congresso Brasileiro de Anestesiologia (CBA 2026)"},
    "88º Congresso da SBO": {"url": "https://www.sbo2026.com.br/"},
    "46º Congresso Brasileiro de Angiologia e Cirurgia Vascular": {"url": "https://bahiavascular2026.com.br/"},
    "30º Congresso Brasileiro de Ultrassonografia da SBUS": {"url": "https://congressosbus2026.com.br/"},
    "20º Congresso Brasileiro de Coluna (CSBC)": {"url": "https://csbc.coluna.com.br/"},
    "Congresso Internacional de Uro-Oncologia 2026": {"url": "https://congressourooncologia.com.br/"},
    "XXX Congresso Brasileiro de Nutrologia 2026": {"url": "https://abran.org.br/cbn2026/"},
    "8º Congresso Internacional Sabará-Pensi de Saúde Infantil": {"url": "https://www.congressosabarapensi.org.br/"},
    "13º Congresso de Cirurgia Plástica e Cosmiatria (CBCP)": {"url": "https://congressocbcp.com.br/"},
}


def apply_to(path):
    if not os.path.exists(path):
        return
    doc = json.load(open(path))
    n = 0
    for ev in doc["eventos"]:
        p = PATCH.get(ev["nome"])
        if not p:
            continue
        ev["url_inscricao"] = p["url"]
        if p.get("cfp"):
            ev["call_for_papers"] = p["cfp"]
        if p.get("nome"):
            ev["nome"] = p["nome"]
        ev["_enriched"] = True
        n += 1
    json.dump(doc, open(path, "w"), ensure_ascii=False, indent=2)
    print(f"{n} eventos enriquecidos em {os.path.basename(path)}")


if __name__ == "__main__":
    for f in ("events.seed.json", "events.json"):
        apply_to(os.path.join(HERE, "data", f))
