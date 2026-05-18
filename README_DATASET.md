# Dataset Documentation

Questo documento descrive la struttura del dataset tabellare generato per l'analisi della complessità legislativa e della frammentazione politica.

## 1. Architettura dei Dati (Schema ER)

Le tabelle CSV sono progettate per essere **relazionali** e facilmente joinabili in Excel, R, Stata o Python (pandas).

```mermaid
erDiagram
    T_ATTI ||--o{ T_ARTICOLI : "contiene"
    T_ATTI ||--o{ T_EMENDAMENTI : "riceve"
    T_ATTI ||--o{ T_FIRMATARI_ATTO : "presentato da"
    T_ARTICOLI ||--o{ T_EMENDAMENTI : "e' bersaglio di"
    T_EMENDAMENTI ||--o{ T_PROPONENTI : "ha"

    T_ATTI {
        string atto_id PK "ID Univoco Atto (es. Atto00055193)"
        string legislatura "Numero Legislatura"
    }

    T_FIRMATARI_ATTO {
        string atto_id FK "Riferimento all'Atto"
        string nome "Nome del firmatario"
        string genere "Genere (M/F)"
        boolean primo_firmatario "True se primo firmatario"
    }

    T_ARTICOLI {
        string atto_id FK "Riferimento all'Atto"
        string articolo_id PK "ID interno Akoma Ntoso"
        string numero_articolo "Numero dell'articolo (es. 1, 2, ...)"
        string titolo "Titolo dell'articolo pulito"
        string versione "Versione del testo (ddlpres, ddlcomm, ddlmess)"
        string testo_integrale "Testo completo dei commi uniti"
    }

    T_EMENDAMENTI {
        string atto_id FK "Riferimento all'Atto"
        string emendamento_id PK "URI univoca del Senato"
        string numero_emendamento "Codice emendamento (es. 3.1)"
        string articolo_target FK "Numero articolo bersaglio (join con T_ARTICOLI.numero_articolo)"
        date data "Data di presentazione"
        string testo_emendamento "Testo della modifica proposta"
    }

    T_PROPONENTI {
        string emendamento_id FK "Riferimento all'Emendamento"
        string proponente_id "ID Senatore (Open Data)"
        string proponente_nome "Nome completo"
        string proponente_gruppo "Gruppo politico alla data dell'emendamento"
        string proponente_genere "Genere (M/F)"
    }
```

## 2. Come eseguire i Join

### Join Atto → Firmatari
`T_ATTI.atto_id` ↔ `T_FIRMATARI_ATTO.atto_id`

Un atto con N firmatari ha N righe in `T_FIRMATARI_ATTO`. Il campo `primo_firmatario = true` identifica il primo firmatario; le righe restanti sono cofirmatari.

### Join Articoli → Emendamenti
Per analizzare quali emendamenti hanno colpito un articolo specifico:
- `T_ARTICOLI.numero_articolo` ↔ `T_EMENDAMENTI.articolo_target`
- Filtrare `versione = 'ddlpres'` in `T_ARTICOLI` per usare il testo di partenza come base.

### Join Emendamenti → Proponenti
`T_EMENDAMENTI.emendamento_id` ↔ `T_PROPONENTI.emendamento_id`

Un emendamento con N firmatari ha N righe in `T_PROPONENTI`, tutte con lo stesso `emendamento_id`.

### Esempio (SQL / DuckDB)
```sql
-- Quanti emendamenti per gruppo politico, per articolo?
SELECT e.articolo_target, p.proponente_gruppo, COUNT(DISTINCT e.emendamento_id) AS n
FROM t_emendamenti e
JOIN t_proponenti p ON e.emendamento_id = p.emendamento_id
GROUP BY e.articolo_target, p.proponente_gruppo
ORDER BY e.articolo_target, n DESC;
```

## 3. Processo di Trasformazione (Audit Log)

1. **Parsing XML:** Estrazione gerarchica da standard Akoma Ntoso (Senato).
2. **Mapping Politico:** Incrocio con Open Data Senato (RDF) per recuperare l'appartenenza ai gruppi parlamentari storicizzata.
3. **Encoding Fix:** Rimozione di artefatti UTF-8 (es. `Ã ` → `à`) e normalizzazione spazi.
4. **Flattening:** Trasformazione da JSON nidificato a CSV relazionale tramite `flatten_custom.py`.

## 4. Posizione dei file

```
data/Leg19/{ATTO_ID}/flattened_custom/
    t_atti.csv
    t_firmatari_atto.csv
    t_articoli.csv
    t_emendamenti.csv
    t_proponenti.csv
```
