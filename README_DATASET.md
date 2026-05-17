# Dataset Documentation: Sperti Legislative Analytics

Questo documento descrive la struttura del dataset tabellare generato per l'analisi della complessità legislativa e della frammentazione politica.

## 1. Architettura dei Dati (Schema ER)

Le tabelle CSV sono progettate per essere **relazionali** e facilmente joinabili in Excel, R, Stata o Python (pandas).

```mermaid
erDiagram
    T_ATTI ||--o{ T_ARTICOLI : "contiene"
    T_ATTI ||--o{ T_EMENDAMENTI : "riceve"
    T_ARTICOLI ||--o{ T_EMENDAMENTI : "e' bersaglio di"

    T_ATTI {
        string atto_id PK "ID Univoco Atto (es. Atto00055193)"
        string legislatura "Numero Legislatura"
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
        string proponente_id "ID Senatore (Open Data)"
        string proponente_nome "Nome completo"
        string proponente_gruppo "Gruppo politico alla data dell'emendamento"
        string proponente_genere "Genere (M/F)"
    }
```

## 2. Come eseguire i Join

### Join Articoli -> Emendamenti
Per analizzare quali emendamenti hanno colpito un articolo specifico, usa:
*   `T_ARTICOLI.numero_articolo` <-> `T_EMENDAMENTI.articolo_target`
*   Assicurati di filtrare la `versione` in `T_ARTICOLI` (es. usa `ddlpres` come base).

### Join Emendamenti -> Anagrafica
La tabella `t_emendamenti` è già "denormalizzata" per proponente. Se un emendamento ha 5 firmatari, troverai 5 righe con lo stesso `emendamento_id` ma diversi `proponente_id`.

## 3. Processo di Trasformazione (Audit Log)

1.  **Parsing XML:** Estrazione gerarchica da standard Akoma Ntoso (Senato).
2.  **Mapping Politico:** Incrocio con Open Data Senato (RDF) per recuperare l'appartenenza ai gruppi parlamentari storicizzata.
3.  **Encoding Fix:** Rimozione di artefatti UTF-8 (es. `Ã ` -> `à`) e normalizzazione spazi.
4.  **Flattening:** Trasformazione da JSON nidificato a CSV relazionale tramite script `flatten_custom.py`.

## 4. Posizione dei file
I dati per l'atto campione si trovano in:
`data/Leg19/[ATTO_ID]/flattened_custom/`
