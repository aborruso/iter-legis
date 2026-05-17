# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Progetto

**iter-legis** — pipeline ETL per costruire un dataset strutturato dei processi legislativi del Senato Italiano (standard Akoma Ntoso) al fine di analizzare la relazione tra frammentazione politica e complessità legislativa. Progetto di tesi accademica.

La fonte dati principale è il repository GitHub pubblico [SenatoDellaRepubblica/AkomaNtosoBulkData](https://github.com/SenatoDellaRepubblica/AkomaNtosoBulkData).

## Comandi principali

```bash
# Esplorare il repository Senato remoto
uv run script/senato_pilot.py list-atti --limit 10
uv run script/senato_pilot.py inspect-atto Atto00055193
uv run script/senato_pilot.py list-dir Leg19/Atto00055193/ddlpres
uv run script/senato_pilot.py find-rich-atti --min-dirs 3 --limit 20

# Fase 1: Parsing DDL (XML → JSON)
uv run script/parser_ddl.py data/Leg19/Atto00055193/ddlpres/<file>.akn.xml --output data/Leg19/Atto00055193/ddlpres/<file>.json

# Fase 2: Parsing emendamenti (XML → JSON)
uv run script/parser_emendamenti.py data/Leg19/Atto00055193/emendc/<file>.akn.xml --output data/Leg19/Atto00055193/emendc/<file>.json

# Anagrafica senatori (RDF → JSON)
uv run script/parser_anagrafica.py <rdf_file> --output data/Leg19/Anagrafica/senatori_19.json
uv run script/flatten_anagrafica.py   # JSON → CSV (percorsi hardcoded)

# Sync completo di un atto (download + parsing in un solo passaggio)
uv run script/sync_atto.py Atto00055193 --leg 19

# Consolidamento (unisce DDL + emendamenti + arricchimento politico)
uv run script/consolidate_atto.py Atto00055193 --leg 19
# Output: data/Leg19/Atto00055193/Atto00055193_consolidated.json

# Flattening (JSON consolidato → CSV relazionali)
uv run script/flatten_custom.py data/Leg19/Atto00055193/Atto00055193_consolidated.json --out data/Leg19/Atto00055193/flattened_custom

# Caricamento DuckDB (aggrega tutti gli atti già appiattiti)
uv run script/init_duckdb.py
# Output: data/iter_legis.duckdb

# Query DuckDB
duckdb -c "SELECT count(*) FROM t_emendamenti" data/iter_legis.duckdb
```

## Architettura della pipeline

La pipeline è sequenziale e **idempotente**: ogni fase controlla l'esistenza degli output prima di rieseguire.

```
GitHub (AkomaNtosoBulkData)
    │
    ▼ senato_pilot.py (list-dir / download_url)
data/Leg{N}/{AttoID}/
    ├── ddlpres/*.akn.xml  ──► parser_ddl.py ──► ddlpres/*.json
    ├── ddlcomm/*.akn.xml  ──► parser_ddl.py ──► ddlcomm/*.json
    ├── ddlmess/*.akn.xml  ──► parser_ddl.py ──► ddlmess/*.json
    └── emendc/*.akn.xml   ──► parser_emendamenti.py ──► emendc/*.json

data/Leg{N}/Anagrafica/
    └── senatori_19.json   ──► flatten_anagrafica.py ──► senatori_19_flattened.csv

                consolidate_atto.py
    (DDL json + emendc json + senatori_19.json)
                    │
                    ▼
    {AttoID}_consolidated.json   (schema: schema.json)
                    │
                    ▼ flatten_custom.py
    flattened_custom/
        ├── t_atti.csv
        ├── t_articoli.csv
        └── t_emendamenti.csv
                    │
                    ▼ init_duckdb.py
    data/iter_legis.duckdb
        ├── t_atti
        ├── t_articoli
        ├── t_emendamenti
        └── t_senatori
```

## Schema dei dati

Il file `schema.json` descrive la struttura del JSON consolidato intermedio. Le tabelle relazionali finali (`README_DATASET.md`) sono:

- **t_atti** — un record per atto legislativo
- **t_articoli** — un record per articolo × versione DDL (`ddlpres`, `ddlcomm`, `ddlmess`)
- **t_emendamenti** — un record per emendamento unico
- **t_proponenti** — un record per emendamento × firmatario (join: `emendamento_id`)
- **t_senatori** — denormalizzata per appartenenza a gruppo parlamentare (una riga per periodo)

Join principale: `t_articoli.numero_articolo` ↔ `t_emendamenti.articolo_target` (filtrare su `versione = 'ddlpres'`).

## Fasi del PRD

| Fase | Stato | Script |
|------|-------|--------|
| 1 – DDL Parsing | Completata | `parser_ddl.py`, `sync_atto.py` |
| 2 – Amendment Parsing | In corso | `parser_emendamenti.py`, `consolidate_atto.py` |
| 3 – Political Mapping | Parziale (anagrafica gruppi) | `parser_anagrafica.py`, `consolidate_atto.py` |
| 4 – Metrics & Similarity | Non iniziata | `analyze_polars.py` (stub) |

## Convenzioni

- Tutti gli script accettano argomenti CLI (`argparse`); eseguire con `uv run script/<nome>.py --help`.
- La gerarchia dei dati rispecchia quella del repository Senato: `data/Leg{N}/{AttoID}/{tipo}/`.
- L'encoding UTF-8 dei file XML del Senato può contenere artefatti di doppia codifica; `flatten_custom.py:fix_encoding()` li normalizza.
- Il namespace Akoma Ntoso usato è `http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03` (prefisso `an`).
- `senato_pilot.py` usa `gh` CLI se disponibile, altrimenti cade su `urllib` diretto.
- Per esplorare/debuggare file JSON da shell usare `jq`, non `python3 -c`.
