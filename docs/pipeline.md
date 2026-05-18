# Pipeline

La pipeline trasforma file XML Akoma Ntoso del Senato Italiano in un database relazionale analizzabile. È **sequenziale** e **idempotente**: ogni fase controlla se l'output esiste già prima di rieseguire.

## Prerequisiti

```bash
git clone https://github.com/aborruso/iter-legis
cd iter-legis
uv sync   # crea .venv e installa duckdb, polars, pyarrow
```

Serve anche la [gh CLI](https://cli.github.com/) per il download dei dati dal repo Senato.

---

## Fasi

### Fase 0 — Esplorazione del repository Senato

Prima di scaricare, si può esplorare cosa è disponibile nel [repo AKN del Senato](https://github.com/SenatoDellaRepubblica/AkomaNtosoBulkData):

```bash
# Lista degli atti disponibili
uv run script/senato_pilot.py list-atti --limit 20

# Atti con più sottocartelle (più ricchi di dati)
uv run script/senato_pilot.py find-rich-atti --min-dirs 3 --limit 20

# Ispezione di un singolo atto
uv run script/senato_pilot.py inspect-atto Atto00055193

# Lista file in una sottocartella remota
uv run script/senato_pilot.py list-dir Leg19/Atto00055193/emendc
```

---

### Fase 1 — Download e parsing DDL

Scarica i file XML e li converte in JSON strutturato.

```bash
# Download + parsing in un solo passaggio (raccomandato)
uv run script/sync_atto.py Atto00055193 --leg 19
```

`sync_atto.py` scarica tutte le sottocartelle dell'atto (`ddlpres`, `ddlcomm`, `ddlmess`, `emendc`) e lancia automaticamente i parser.

**Output:**

```
data/Leg19/Atto00055193/
    ddlpres/*.akn.xml  →  ddlpres/*.json
    ddlcomm/*.akn.xml  →  ddlcomm/*.json
    ddlmess/*.akn.xml  →  ddlmess/*.json
    emendc/*.akn.xml   →  emendc/*.json
```

**Parsing manuale** (se si vuole processare un singolo file):

```bash
uv run script/parser_ddl.py data/Leg19/Atto00055193/ddlpres/<file>.akn.xml \
  --output data/Leg19/Atto00055193/ddlpres/<file>.json

uv run script/parser_emendamenti.py data/Leg19/Atto00055193/emendc/<file>.akn.xml \
  --output data/Leg19/Atto00055193/emendc/<file>.json
```

---

### Fase 2 — Anagrafica senatori

Converte il file RDF dell'anagrafica Senato in JSON, poi in CSV.

```bash
uv run script/parser_anagrafica.py <file_rdf> \
  --output data/Leg19/Anagrafica/senatori_19.json

uv run script/flatten_anagrafica.py
# Output: data/Leg19/Anagrafica/senatori_19_flattened.csv
```

Il file RDF dell'anagrafica si scarica dall'[Open Data del Senato](http://dati.senato.it/).

---

### Fase 3 — Consolidamento

Unisce DDL + emendamenti + anagrafica, arricchendo ogni emendamento con il gruppo parlamentare del proponente **alla data di presentazione**.

```bash
uv run script/consolidate_atto.py Atto00055193 --leg 19
# Output: data/Leg19/Atto00055193/Atto00055193_consolidated.json
```

Lo schema del JSON prodotto è descritto in [`schema.json`](../schema.json).

---

### Fase 4 — Flattening in CSV relazionali

Trasforma il JSON consolidato in tre tabelle CSV joinabili.

```bash
uv run script/flatten_custom.py \
  data/Leg19/Atto00055193/Atto00055193_consolidated.json \
  --out data/Leg19/Atto00055193/flattened_custom
```

**Output:**

| File | Contenuto |
|------|-----------|
| `t_atti.csv` | Un record per atto |
| `t_firmatari_atto.csv` | Un record per atto × firmatario del DDL (primo + cofirmatari) |
| `t_articoli.csv` | Un record per articolo × versione DDL |
| `t_emendamenti.csv` | Un record per emendamento unico |
| `t_proponenti.csv` | Un record per emendamento × firmatario |

Per lo schema dettagliato dei campi vedi [`README_DATASET.md`](../README_DATASET.md).

---

### Fase 5 — Caricamento DuckDB

Aggrega tutti gli atti già appiattiti in un unico database.

```bash
uv run script/init_duckdb.py
# Output: data/iter_legis.duckdb
```

Lo script scansiona ricorsivamente `data/` cercando cartelle `flattened_custom/` e carica tutti i CSV trovati, più l'anagrafica senatori.

**Verifica:**

```bash
duckdb -c "SELECT 'atti' as t, count(*) FROM t_atti
           UNION ALL SELECT 'articoli', count(*) FROM t_articoli
           UNION ALL SELECT 'emendamenti', count(*) FROM t_emendamenti
           UNION ALL SELECT 'senatori', count(*) FROM t_senatori;" \
  data/iter_legis.duckdb
```

---

### Fase 6 — Analisi (stub)

Calcola metriche di complessità e correlazione frammentazione-complessità.

```bash
uv run script/analyze_polars.py
# Richiede: data/iter_legis.duckdb
```

Produce tre output su stdout:
1. Conteggio parole per articolo × versione
2. Crescita testuale tra `ddlpres` e `ddlmess`
3. Correlazione emendamenti per articolo × delta parole

---

## Struttura completa dei dati

```
data/
  Leg{N}/
    Anagrafica/
      senatori_19.json          ← parser_anagrafica.py
      senatori_19_flattened.csv ← flatten_anagrafica.py
    {AttoID}/
      ddlpres/*.akn.xml         ← originali Senato
      ddlpres/*.json            ← parser_ddl.py
      ddlcomm/*.akn.xml
      ddlcomm/*.json
      ddlmess/*.akn.xml
      ddlmess/*.json
      emendc/*.akn.xml
      emendc/*.json             ← parser_emendamenti.py
      {AttoID}_consolidated.json ← consolidate_atto.py
      flattened_custom/
        t_atti.csv              ← flatten_custom.py
        t_firmatari_atto.csv
        t_articoli.csv
        t_emendamenti.csv
        t_proponenti.csv
  iter_legis.duckdb     ← init_duckdb.py
```
