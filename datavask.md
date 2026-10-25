BoMiljø.xlsx KomSkole.xlsx
manuell Framsikt-export
lavere tillit høyere tillit
│  
└──────────────┬──────────────┘
▼
01 INGESTION
│
Les uten antakelser
▼
02 PROFILING
│
Kolonner?
Datatyper?
Null?
Duplikater?
Formater?
▼
03 NORMALIZE
│
kolonnenavn
decimaltegn
whitespace
datoformat
nullverdier
▼
04 COLUMN MAP
│
Budsjett → budget
Regnskap → actual
Konto → account_id
▼
05 COLUMN POLICY
│
┌─────────────┼─────────────┐
▼ ▼ ▼
REQUIRED OPTIONAL DROP
budget kommentar avvik
actual leverandør avvik %
account ... ...
│
▼
06 TYPE CASTING
│
IDs → string
beløp → numeric
dato → datetime
│
▼
07 VALIDATION
Pydantic +
business rules
│
┌─────────┴──────────┐
▼ ▼
PASS FAIL
│ │
▼ ▼
CURATED QUARANTINE
Parquet + audit log
