# Fonti dei dati

## Repository AKN del Senato

**URL**: [github.com/SenatoDellaRepubblica/AkomaNtosoBulkData](https://github.com/SenatoDellaRepubblica/AkomaNtosoBulkData)  
**Licenza**: CC BY 3.0  
**Aggiornamento**: automatico ogni sera

Contiene tutti i documenti legislativi del Senato in standard [Akoma Ntoso](http://www.akomantoso.org/) (XML).

### Struttura del repository

```
Leg{N}/
  Atto{ID}/
    README.MD          ← link alla scheda DDL su senato.it e query SPARQL
    ddlpres/           ← testo presentato dal proponente
    ddlcomm/           ← testo della commissione referente
    ddlmess/           ← testo trasmesso all'altra Camera
    emend/             ← emendamenti in Assemblea
    emendc/            ← emendamenti in Commissione
    resaula/           ← resoconti stenografici di Aula
    sommcomm/          ← resoconti sommari di Commissione
```

### Namespace XML

Tutti i file usano il namespace Akoma Ntoso:

```
http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03
```

Nelle query XPath/xq usare il prefisso `an:`.

### Contenuto degli XML

**DDL** (`ddlpres`, `ddlcomm`, `ddlmess`): struttura gerarchica articoli/commi, metadati (date, firmatari), testo integrale.

**Emendamenti** (`emendc`, `emend`): numero emendamento, proponenti (con URI senatore), testo della modifica. Il campo `workflow/step/@outcome` è sempre `"presentazione"` — l'esito finale **non è presente nel file XML**.

**Resoconti sommari** (`sommcomm`): verbale testuale delle sedute di commissione. Contiene gli esiti degli emendamenti **in forma narrativa** (es. "L'emendamento 3.1 è approvato"), non strutturata.

**Resoconti di aula** (`resaula`): verbale testuale delle sedute assembleari + allegati (liste presenti).

---

## Endpoint SPARQL — Open Data Senato

**URL**: `https://dati.senato.it/sparql`  
**Prefisso ontologia**: `PREFIX osr: <http://dati.senato.it/osr/>`

### Classi principali disponibili

| Classe | Descrizione |
|--------|-------------|
| `osr:Emendamento` | Emendamento con numero, tipo, URL testo, flagCommissione |
| `osr:Votazione` | Votazione con favorevoli, contrari, presenti, tipo |
| `osr:Ddl` | Disegno di legge |
| `osr:OggettoTrattazione` | Oggetto discusso in una seduta |
| `osr:Senatore` | Senatore con dati anagrafici |
| `osr:SedutaAssemblea` | Seduta di aula |
| `osr:SedutaCommissione` | Seduta di commissione |
| `osr:IterDdl` / `osr:FaseIter` | Iter legislativo |

### Campi disponibili su `osr:Emendamento`

| Proprietà | Tipo | Descrizione |
|-----------|------|-------------|
| `osr:numero` | string | Numero emendamento (es. "3.1") |
| `osr:tipo` | string | "E" = emendamento |
| `osr:URLTesto` | URI | Link HTML sul sito Senato |
| `osr:URLTestoXml` | URI | Link al file AKN XML |
| `osr:flagCommissione` | int | 1 = commissione, 0 = aula |
| `osr:oggetto` | URI | → `OggettoTrattazione` |
| `osr:legislatura` | int | Numero legislatura |

**Assente**: nessun campo `esito` o equivalente.

### Catena per collegare votazioni a un DDL

```sparql
PREFIX osr: <http://dati.senato.it/osr/>
SELECT ?vot ?label ?favorevoli ?contrari WHERE {
  ?vot a osr:Votazione .
  ?vot osr:oggetto ?ogg .
  ?ogg osr:relativoA <http://dati.senato.it/ddl/55193> .
  ?vot <http://www.w3.org/2000/01/rdf-schema#label> ?label .
  OPTIONAL { ?vot osr:favorevoli ?favorevoli }
  OPTIONAL { ?vot osr:contrari ?contrari }
}
```

**Nota**: per DDL 55193 (Leg19) questa query restituisce solo i voti sugli **articoli** in aula e il voto finale — non i voti sui singoli emendamenti in commissione.

### Campi disponibili su `osr:Votazione`

| Proprietà | Descrizione |
|-----------|-------------|
| `osr:favorevoli` | Numero voti favorevoli |
| `osr:contrari` | Numero voti contrari |
| `osr:presenti` | Numero presenti |
| `osr:votanti` | Numero votanti |
| `osr:maggioranza` | Quorum richiesto |
| `osr:tipoVotazione` | "elettronica", "controprova", ecc. |
| `osr:seduta` | → `SedutaAssemblea` |
| `osr:oggetto` | → `OggettoTrattazione` |
| `osr:favorevole` | → URI senatore (voto nominale) |

---

## Anagrafica senatori — Open Data Senato

**URL**: `http://dati.senato.it/`  
**Formato**: RDF/Turtle

Contiene per ogni senatore: ID stabile, nome, cognome, genere, data/luogo nascita, lista storica dei gruppi parlamentari con date di ingresso/uscita.

Script di parsing: `script/parser_anagrafica.py`

---

## Limiti noti

| Dato | Disponibilità | Note |
|------|--------------|-------|
| Esito singolo emendamento | ✗ Non strutturato | Solo in testo narrativo nei `sommcomm` |
| Voti su singoli emendamenti | ✗ Non disponibile | SPARQL ha solo voti su articoli e voto finale |
| Status maggioranza/opposizione | ✗ Assente | Richiede un dataset governo→partiti→date |
| Comma target emendamento | ✓ Parziale | Estratto dal numero emendamento (es. "3.1" → art.3) |
| Tipo operazione (soppressione/sostituzione) | ✓ Nel testo | Non estratto strutturalmente dal parser |
| Titolo DDL, policy area, tipo iniziativa | ✗ Assente | Non nell'AKN XML standard |
| Votazioni nominali (singolo senatore) | ✓ Via SPARQL | `osr:favorevole` → URI senatore, solo per voti in aula |
