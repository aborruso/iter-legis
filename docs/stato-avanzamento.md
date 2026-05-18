# Stato di avanzamento

Ultimo aggiornamento: 2026-05-17

## Cosa funziona oggi

Il database `data/iter_legis.duckdb` è popolato con 2 atti campione della XIX Legislatura e contiene:

| Tabella | Righe | Note |
|---------|-------|------|
| `t_atti` | 2 | Atto00055193, Atto00055210 |
| `t_firmatari_atto` | — | Da implementare (issue aperta) |
| `t_articoli` | 26 | Versioni ddlpres/ddlcomm/ddlmess |
| `t_emendamenti` | 914 | Un record per emendamento unico |
| `t_proponenti` | 2.342 | Un record per emendamento × firmatario |
| `t_senatori` | 299 | Con storico gruppi parlamentari |

### Pipeline completamente funzionante

- **Download** dai repo AKN del Senato (`senato_pilot.py`, `sync_atto.py`)
- **Parsing DDL** XML → JSON strutturato con articoli e commi (`parser_ddl.py`)
- **Parsing emendamenti** XML → JSON con proponenti (`parser_emendamenti.py`)
- **Mapping politico** proponente → gruppo parlamentare alla data dell'emendamento (`consolidate_atto.py`)
- **Flattening** JSON → CSV relazionali (`flatten_custom.py`)
- **Database aggregato** DuckDB con tutte le tabelle (`init_duckdb.py`)
- **Analisi base** crescita parole per articolo e correlazione con n. emendamenti (`analyze_polars.py`)

### Distribuzione emendamenti per gruppo politico (sui 2 atti campione)

| Gruppo | N. emendamenti |
|--------|---------------|
| Misto (AVS + altri) | 690 |
| PD - Italia Democratica e Progressista | 445 |
| Fratelli d'Italia | 351 |
| Lega Salvini Premier | 301 |
| MoVimento 5 Stelle | 164 |
| Forza Italia | 128 |
| Per le Autonomie | 97 |
| Italia Viva | 95 |
| Civici d'Italia - Noi Moderati | 52 |
| NULL (Relatore/Relatrice) | 19 |

---

## Gap rispetto ai requisiti della tesi

### Critico

| Dato mancante | Impatto | Opzioni |
|---|---|---|
| **Esito emendamento** (approvato/respinto/ritirato) | Non si distingue compromesso da ostruzionismo | 1. NLP su sommcomm XML; 2. Scraping senato.it |
| **Status maggioranza/opposizione** | Variabile indipendente chiave | Serve dataset governo→partiti→date |

### Importante

| Dato mancante | Note |
|---|---|
| Comma target (oltre all'articolo) | Parser estrae solo n. articolo dal codice emendamento |
| Tipo operazione (aggiunta/sostituzione/soppressione) | Nel testo XML, non estratto strutturalmente |
| Versione `ddlmess` per Atto00055210 | Il DDL non ha raggiunto la fase di trasmissione — delta parole non confrontabile |
| Titolo DDL, tipo iniziativa, policy area | Non presenti nell'AKN XML |

### Fase 4 non ancora applicata sistematicamente

`analyze_polars.py` funziona su 2 atti ma produce analisi preliminari. Mancano:
- Indici di leggibilità (Gulpease o equivalenti)
- Conteggio riferimenti normativi
- Clustering/similarità testuale tra emendamenti

---

## Decisioni aperte

1. **Come recuperare l'esito degli emendamenti?**
   - Opzione A: regex/NLP sui `sommcomm` XML (pattern semi-strutturato)
   - Opzione B: scraping della scheda DDL su `senato.it`
   - Opzione C: accettare il dato mancante per questa fase

2. **Scalare a quanti atti?**
   - Attualmente: 2 atti campione
   - Necessario per analisi statistica significativa: almeno 20-30 atti

3. **Come modellare il mapping maggioranza/opposizione?**
   - Richiede una tabella `governi` con date, partiti e flag coalizione
   - Fonte: SPARQL Camera/Senato o costruzione manuale

---

## Note tecniche

- `Misto` non è un bug: i senatori AVS (Cucchi, De Cristofaro, Magni, Floridia) sono nel gruppo Misto perché AVS non raggiunge la soglia per un gruppo autonomo al Senato
- I 19 NULL su `proponente_gruppo` sono tutti Relatore/Relatrice (ruolo commissione, non senatore individuale)
- Atto00055210 non ha `ddlmess` — è un DDL che non ha completato l'iter bicamerale
