"""Orquestrador do pipeline, ponta a ponta:

    descoberta (ingest.py)  →  enriquecimento (enrich.py)  →  build da landing

É resiliente: cada etapa que precisa de chave é PULADA se a chave não estiver no
ambiente — então roda mesmo sem chave nenhuma (só reempacota o catálogo atual).
Assim o site publica desde o dia 1 e melhora conforme você adiciona as chaves.

Uso:
    python run_pipeline.py
Variáveis de ambiente (opcionais):
    ANTHROPIC_API_KEY   habilita a descoberta (ingest.py)
    MISTRAL_API_KEY     habilita o enriquecimento (enrich.py)
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "events.json")
SEED = os.path.join(HERE, "data", "events.seed.json")


def step(script, needs_key=None):
    if needs_key and not os.environ.get(needs_key):
        print(f"↷ pulando {script} ({needs_key} ausente)", file=sys.stderr)
        return
    print(f"▶ {script}", file=sys.stderr)
    subprocess.run([sys.executable, os.path.join(HERE, script)], check=True)


def main():
    # garante um events.json de partida (a partir do seed) se ainda não existe
    if not os.path.exists(DATA) and os.path.exists(SEED):
        shutil.copy(SEED, DATA)
        print("• events.json inicializado a partir do seed", file=sys.stderr)

    step("ingest.py", needs_key="ANTHROPIC_API_KEY")   # descoberta ao vivo
    step("enrich.py", needs_key="MISTRAL_API_KEY")     # links + CAP + call-for-papers
    step("build_landing_data.py")                       # sempre: gera landing/events.json
    print("✓ pipeline concluído", file=sys.stderr)


if __name__ == "__main__":
    main()
