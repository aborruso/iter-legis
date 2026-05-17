# Sperti Legislative Analytics

Pipeline ETL per analizzare la relazione tra frammentazione politica e complessità legislativa nei processi del Senato Italiano (standard Akoma Ntoso).

## Prerequisiti

- [Python ≥ 3.11](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — gestore di pacchetti Python
- [gh CLI](https://cli.github.com/) — per scaricare i dati dal repository Senato (opzionale, ma consigliato)

## Setup

```bash
git clone <url-repo>
cd sperti
uv sync
```

`uv sync` crea automaticamente il virtualenv e installa le dipendenze (`duckdb`, `polars`).

## Esecuzione della pipeline

La pipeline è sequenziale e idempotente. Ogni fase può essere eseguita singolarmente.

### 1. Esplora gli atti disponibili

```bash
uv run script/senato_pilot.py list-atti --limit 10
uv run script/senato_pilot.py find-rich-atti --min-dirs 3 --limit 20
```

### 2. Scarica e processa un atto

```bash
# Download + parsing DDL + parsing emendamenti in un solo passaggio
uv run script/sync_atto.py Atto00055193 --leg 19
```

### 3. Consolida (unisce DDL, emendamenti e dati politici)

```bash
uv run script/consolidate_atto.py Atto00055193 --leg 19
# Output: data/Leg19/Atto00055193/Atto00055193_consolidated.json
```

### 4. Appiattisci in CSV relazionali

```bash
uv run script/flatten_custom.py \
  data/Leg19/Atto00055193/Atto00055193_consolidated.json \
  --out data/Leg19/Atto00055193/flattened_custom
```

### 5. Carica in DuckDB (aggrega tutti gli atti)

```bash
uv run script/init_duckdb.py
# Output: data/sperti_legislative.duckdb
```

### Verifica rapida

```bash
duckdb -c "SELECT count(*) FROM t_emendamenti" data/sperti_legislative.duckdb
```

## Struttura dei dati

```
data/Leg{N}/{AttoID}/
    ├── ddlpres/*.akn.xml      # XML originali (DDL presentato)
    ├── ddlcomm/*.akn.xml      # XML originali (testo commissione)
    ├── emendc/*.akn.xml       # XML originali (emendamenti)
    └── flattened_custom/
        ├── t_atti.csv
        ├── t_articoli.csv
        └── t_emendamenti.csv

data/Leg{N}/Anagrafica/
    └── senatori_19.json       # Anagrafica senatori (da Open Data Senato)

data/sperti_legislative.duckdb # Database aggregato finale
```

Per la documentazione del dataset e le istruzioni sui join, vedi [`README_DATASET.md`](README_DATASET.md).
