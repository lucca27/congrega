# Pipeline de ingestão de eventos médicos (protótipo)

Prova de conceito do "hub nacional automático": pega HTML de fontes com estruturas
diferentes → IA normaliza para um schema único → deduplica → catálogo pronto para o app.

## O que este protótipo já demonstra
Rodando em dados **reais** de duas fontes (bip + AgrupaMED, set/2026):

```
49 registros brutos → 40 eventos únicos (9 duplicatas mescladas)
```

- **Normalização**: fontes com HTML totalmente diferente viram o mesmo `MedEvent`.
- **Deduplicação**: o mesmo congresso em 2 fontes vira 1 registro, marcado como
  "confirmado por 2 fontes" (sinal de confiança + completa campos faltantes).
- **Taxonomia de especialidade**: permite filtrar "todos os eventos de cardiologia".

## Arquitetura (2 estágios)

```
sources.yaml ─▶ fetch ─▶ extractor(IA) ─▶ normaliza ─▶ dedup ─▶ data/events.json
  (fontes)     (HTML)   (schema único)                          (catálogo AMPLO e raso)
                                                                        │
                                          [estágio 2 — enriquecimento]  ▼
                                   por evento: abre o site/edital e extrai
                                   pontos CAP + prazo de call-for-papers
                                            (catálogo ESTREITO e profundo)
```

- **Estágio 1 (este código):** descoberta em massa. Barato, roda diário, cobre o Brasil.
- **Estágio 2 (a construir):** para cada evento, visita a página oficial e extrai os
  diferenciais — `pontos_cap` e `call_for_papers` (aberto/prazo). É o que faz o usuário voltar.

## Arquivos
| Arquivo | Papel |
|---|---|
| `models.py` | Schema canônico `MedEvent` + JSON Schema da extração por IA |
| `extractor.py` | Passo de IA: texto da fonte → eventos estruturados (Anthropic tool use) |
| `dedup.py` | Chave canônica + mescla de duplicatas entre fontes |
| `ingest.py` | Orquestrador: fontes → fetch → IA → dedup → JSON |
| `sources.yaml` | Lista de fontes (crescer isto = crescer a cobertura) |
| `_build_seed.py` | Gera o catálogo-semente com dados reais (validou a dedup) |
| `data/events.seed.json` | Catálogo-semente pronto (40 eventos) |

## Rodar

```bash
# Ver o catálogo-semente já extraído (sem custo, sem chave):
python3 ingest.py --demo

# Coleta AO VIVO (chama a IA nas fontes ativas do sources.yaml):
pip install anthropic pyyaml
export ANTHROPIC_API_KEY=sk-...
python3 ingest.py
```

Modelo de extração configurável: `export MED_EXTRACTOR_MODEL=claude-haiku-4-5-20251001`
(mais barato para volume). Padrão: `claude-sonnet-5`.

## Exemplo de registro enriquecido (meta do estágio 2)
```json
{
  "nome": "81º Congresso Brasileiro de Cardiologia",
  "data_inicio": "2026-10-08", "cidade": "Rio de Janeiro", "uf": "RJ",
  "especialidade": "Cardiologia",
  "pontos_cap": 25,
  "call_for_papers": { "aberto": true, "prazo_final": "2026-06-30", "url": "..." },
  "fontes": [{ "nome": "bip" }, { "nome": "AgrupaMED" }]
}
```
> `pontos_cap` e `call_for_papers` ficam `null`/vazios até o estágio 2. Não invente:
> só entram quando extraídos do edital/site oficial.

## Limitações conhecidas (honestas)
- APIs Even3/Sympla são **lado-organizador** (só seus próprios eventos), não um catálogo
  público — por isso a base vem de agregadores + sites de sociedades, não de uma API única.
- Dedup por nome canônico funciona bem quando a IA já devolve nome limpo; nomes muito
  divergentes podem escapar (aceitável no início; dá para reforçar com data+cidade).
- Regras do CAP/CNA mudam e são burocráticas — validar antes de prometer pontuação no app.

## Cobertura nacional total — como chegar lá

A cobertura não vem de uma fonte mágica; vem de **camadas que se complementam**,
crescendo o `sources.yaml`:

| Camada | O que garante | Esforço |
|---|---|---|
| **Agregadores** (bip, AgrupaMED, busca Even3/Sympla) | base ampla no dia 1 | baixo (já ativo) |
| **~30 sociedades nacionais** (1 por especialidade) | o calendário oficial de cada área | médio — crawler + IA |
| **Regionais/estaduais** (SOCESP, SOCERJ, …) | Norte/Centro-Oeste e eventos locais | incremental, por demanda |
| **APIs Even3/Sympla** | eventos de quem usa essas plataformas | parcerias (chave por conta) |
| **Cadastro + crowdsourcing** | o que escapa de tudo acima | organizadores/usuários enviam |

Regra prática: **~30 sociedades nacionais + 4 agregadores cobrem a grande maioria
dos congressos relevantes.** O restante entra por regionais e cadastro. A meta não é
"100% no dia 1", é um catálogo que se completa sozinho a cada rodada.

## Como manter atualizado (freshness)

Descoberta e enriquecimento rodam em ciclos, guiados pelo `cadence` de cada fonte:

```
diária    → APIs + agregadores grandes           (ingest.py)
semanal   → agregadores                           (ingest.py)
quinzenal → sociedades nacionais                  (ingest.py)
mensal    → regionais                             (ingest.py)
+ enrich.py roda depois, só no que mudou/faltou   (link, CAP, call-for-papers)
```

Mecanismos que evitam retrabalho e dado velho:
- **Detecção de mudança:** guardar um hash do conteúdo de cada fonte; se não mudou,
  pula a extração (economiza IA). Se mudou, reprocessa só aquela fonte.
- **Deduplicação estável:** a mesma chave de evento entre rodadas → atualiza em vez
  de duplicar (já em `dedup.py`).
- **Expiração:** evento com data passada sai do "próximos"; enriquecimento só reprocessa
  eventos futuros.
- **Reenriquecimento:** `enrich.py --force` revisita prazos de call-for-papers e pontos
  CAP, que mudam ao longo do ano.
- **QA leve:** sinalizar baixa `confianca`, datas impossíveis e links quebrados para
  revisão humana rápida (fila pequena, não curadoria manual do país inteiro).
- **Agendamento:** um cron (ou GitHub Actions) dispara `ingest.py` e `enrich.py` nas
  cadências acima e publica o `data/events.json`.

## Links clicáveis

- O link de cada card vem de `url_inscricao`, preenchido pelo `enrich.py`.
- Enquanto um evento não foi enriquecido, a landing usa um **fallback de busca**
  (rótulo "Buscar evento") — nunca um link oficial inventado. Ao rodar `enrich.py`,
  o rótulo vira "Inscrições" e aponta para a página real.

## Próximos passos
1. Ativar 3–5 sociedades no `sources.yaml` (`ativo: true`) e rodar `ingest.py` ao vivo.
2. Rodar o enriquecimento (usa a **API da Mistral**, com busca web nativa):
   ```bash
   export MISTRAL_API_KEY=...        # nunca commitar a chave
   python enrich.py --limit 5        # testa em poucos
   python enrich.py                  # preenche links oficiais + CAP + call-for-papers
   ```
3. Agendar as duas etapas (cron/Actions) nas cadências do `cadence`.
4. Expor `data/events.json` via API simples para a landing/app.

> Nota: `ingest.py` (descoberta) usa a API da Anthropic no `extractor.py`;
> `enrich.py` (enriquecimento) usa a API da Mistral. São independentes — dá para
> trocar o provedor de cada etapa isoladamente.
