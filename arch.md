Tydelig data contract før data får slippe inn i curated/Parquet-laget, og samtidig skilt hardt mellom kildedata og beregnede KPI-er.

Pydantic Models er laget nettopp for å definere modeller med felt, datatyper og constraints, og validere data mot disse kravene.

1. Prinsippet jeg ville brukt

   RAW FILE
   │
   ▼
   Column mapping
   │
   ▼
   Cleaning
   │
   ▼
   PYDANTIC / DATA CONTRACT
   │
   ├── Required columns?
   ├── Correct datatypes?
   ├── Valid values?
   ├── Null problems?
   ├── Duplicate keys?
   └── Business rules?
   │
   ▼
   CANONICAL DATA
   │
   ▼
   PARQUET / DUCKDB
   │
   ├──────────────┐
   ▼ ▼
   POWER BI PYTHON
   DAX Forecast/ML

Og særlig:

Ikke importer beregnede KPI-er fra kilden dersom de deterministisk kan beregnes fra autoritative grunnlagsdata.

2. Eksempel: budsjett/regnskap

Hvis inputfilen inneholder:

Prosjekt
År
Måned
Konto
Budsjett
Regnskap
Avvik
Avvik %

ville jeg ikke tatt med:

Avvik
Avvik %

Inn i canonical modellen.

Behold:

prosjekt_id
dato
konto_id
budsjett
regnskap

Deretter beregner du:

Avvik = Budsjett - Regnskap

 

og:

Avvik % = Avvik / Budsjett

Det gir én definisjon av avvik, i stedet for at forskjellige Excel-filer kan komme med forskjellige beregninger.

Siden du tidligere har ønsket negativt avvik = grønt og positivt = rødt, er definisjonen Budsjett - Regnskap viktig å låse fast. Med denne definisjonen betyr negativt tall at regnskapet er høyere enn budsjettet. Hvis du faktisk vil at negativt skal være gunstig, må fortegnslogikken defineres annerledes. Dette bør stå eksplisitt i data contract/business semantics.

3. Jeg ville definert et minimumsskjema

Eksempelvis for en prosjektøkonomisk faktatabell:

Python
from datetime import date
from decimal import Decimal

 
from pydantic import BaseModel, ConfigDict, Field

 

 
class FinanceRecord(BaseModel):

 
model_config = ConfigDict(extra="forbid")

 
project_id: str
date: date
account_id: str

 
budget: Decimal
actual: Decimal

 
currency: str = Field(min_length=3, max_length=3)

Da sier modellen:

Disse feltene er kontrakten.

Pydantic kan også konfigureres til å avvise ekstra felter med extra="forbid".

Men jeg ville faktisk ikke brukt extra="forbid" direkte på råfilen, fordi ERP- og Excel-eksporter ofte har masse kolonner du ikke trenger.

4. Jeg ville heller introdusert whitelist

Dette er enda bedre:

Python
REQUIRED_COLUMNS = {
"project_id",
"date",
"account_id",
"budget",
"actual",
"currency",
}

 
OPTIONAL_COLUMNS = {
"supplier_id",
"contract_id",
"wbs_id",
"description",
}

 
DROP_COLUMNS = {
"variance",
"variance_pct",
"avvik",
"avvik_prosent",
}

Pipeline:

Excel/CSV
↓
100 kolonner
↓
COLUMN MAPPING
↓
DROP DERIVED/IRRELEVANT COLUMNS
↓
30 relevante kolonner
↓
VALIDATION
↓
CANONICAL SCHEMA
↓
PARQUET

Dermed gjør det ingenting om ERP-systemet plutselig legger til:

Created by
Posting description 2
User
System status
Print code
Technical ID

De kommer simpelthen ikke videre.

5. Enda viktigere: column mapping

Virkeligheten blir fort:

Budsjett
Budget
BUDGET
Budsjett beløp
Bud
Belop_Budsjett

Jeg ville derfor hatt én mapping:

Python
COLUMN_MAP = {
"prosjekt": "project_id",
"prosjektnr": "project_id",
"project": "project_id",

 
"konto": "account_id",
"kontonr": "account_id",

 
"budsjett": "budget",
"budget": "budget",

 
"regnskap": "actual",
"actual": "actual",
}

Da blir pipeline mye mer robust mot nye filer.

6. Deretter Pydantic

Altså:

INPUT FILE
│
▼
Normalize column names
│
▼
Map aliases
│
▼
Select canonical columns
│
▼
Clean values
│
▼
Pydantic validation
│
▼
Business validation
│
▼
Parquet

Det er et viktig skille.

Pydantic er ikke datavasken.

Pydantic er først og fremst kontrakten som sier:

Etter datavask skal dataene oppfylle disse kravene.

7. Jeg ville også hatt business validation

Pydantic alene er ikke nok.

For eksempel kan følgende være gyldig datatype:

budget = -999999999999

men fortsatt være mistenkelig business-messig.

Derfor:

Structural validation

✓ column exists
✓ decimal really is decimal
✓ date really is date
✓ currency is string
Business validation

✓ Project exists
✓ Account exists
✓ Date inside accounting period
✓ Currency allowed
✓ Project + account mapping valid
✓ No unexpected duplicates
✓ Period isn't closed
Reconciliation

Source ERP total:

 
123,456,789

 
↓ cleaning

 
Canonical total:

 
123,456,789

 
Difference:

 
0

Denne siste kontrollen er ekstremt viktig.

8. Audit-tabellen kan registrere datavasken

Eksempel:

run_id
source_file
loaded_at
rows_source
rows_accepted
rows_rejected
columns_source
columns_retained
columns_dropped
source_amount
curated_amount
difference
status

 

Og en egen feil-tabell:

validation_errors

 
run_id
row_id
column
value
rule
error

Eksempel:

R102
Row 4582
account_id
"ABC"
ACCOUNT_MUST_EXIST
Unknown account

Dette gir deg veldig god transparens.

9. Beregnede kolonner bør katalogiseres separat

Her ville jeg etablert noe slikt:

Source columns

budget
actual
commitment
progress
quantity
price
Derived metrics

variance
variance_pct
remaining_budget
commitment_ratio
CPI
SPI
EAC
ETC
Predictive metrics

predicted_eac
overrun_probability
p50_eac
p80_eac
AI assessments

risk_explanation
recommendation

Dermed får du fire helt forskjellige datatyper:

SOURCE
↓
DERIVED
↓
PREDICTED
↓
AI INTERPRETED

Dette er også veldig bra for audit.

10. Jeg ville heller ikke lagret Avvik i Parquet-filen

Hvis:

Avvik = Budsjett - Regnskap

er 100 % deterministisk, trenger curated-data i utgangspunktet bare:

budget
actual

Power BI kan beregne:

DAX
Avvik :=
[Budsjett] - [Regnskap]

Excel kan gjøre tilsvarende.

Python:

Python
df["variance"] = df["budget"] - df["actual"]

Men her kommer et viktig governance-prinsipp:

Det er ikke nok at alle kan beregne det. De må beregne det med samme definisjon.

Derfor trenger vi en metric catalog.

11. Metric catalog

Dette synes jeg absolutt bør inn i modellen din.

For eksempel:

YAML
metrics:

 
variance:
label: "Avvik"
definition: "Budsjett minus regnskap"
formula: "budget - actual"
unit: "NOK"
source: "calculated"

 
variance_pct:
label: "Avvik %"
definition: "Avvik delt på budsjett"
formula: "variance / budget"
source: "calculated"

Da kan Power BI, Python, Excel og dokumentasjonen bygge på samme business-definisjon.

12. Minimum viable finance schema

Hvis jeg skulle laget første versjon for prosjektet ditt, ville jeg sannsynligvis startet rundt:

project_id
period
account_id
cost_center_id
wbs_id

 
budget
actual
commitment

 
currency
source_system

 
source_file
source_row_id

 
loaded_at
run_id

Noen kan være optional avhengig av datasettet.

Jeg ville altså ikke startet med 50 KPI-kolonner.

13. Dette reduserer datamodellen dramatisk

I stedet for:

Budsjett
Regnskap
Avvik
Avvik %
Gjenværende
Forecast
Forecast avvik
Forecast avvik %
Forbruk %
...

lagrer du primært autoritative facts:

Budget
Actual
Commitment
Forecast

 

og lar semantic layer produsere:

Variance
Variance %
Remaining
Forecast Variance
Forecast Variance %
Commitment Ratio
...

Det gir en mye renere modell.

Jeg ville derfor gjort datavask-pipelinen til inngangsporten for hele project-finance-ai

INPUT FILE
│
┌──────▼──────┐
│ PROFILING │
└──────┬──────┘
│
┌──────▼──────┐
│ NORMALIZE │
│ + MAP │
└──────┬──────┘
│
┌──────▼──────┐
│ SELECT │
│ COLUMNS │
└──────┬──────┘
│
┌──────▼──────┐
│ CLEAN │
└──────┬──────┘
│
┌──────▼──────┐
│ PYDANTIC │
│ CONTRACT │
└──────┬──────┘
│
┌──────▼──────┐
│ BUSINESS │
│ VALIDATION │
└──────┬──────┘
│
┌────────┴────────┐
▼ ▼
VALID INVALID
│ │
▼ ▼
PARQUET QUARANTINE
│ + ERROR LOG
▼
DUCKDB
│
┌──────┼────────┐
▼ ▼ ▼
Python Power BI Excel

Det er denne versjonen jeg ville bygget.

Og med tanke på det du allerede har jobbet med rundt dynamisk datavask, DuckDB, Power BI og audit, ville jeg gjort neste steg til en generisk finance_data_validator i Python: den oppdager CSV/Excel/Parquet, profilerer filen, mapper alternative kolonnenavn, fjerner eksplisitt uønskede/derived kolonner som Avvik, validerer minimumsskjema med Pydantic, gjør reconciliation, sender feilrader til quarantine og skriver godkjente data til standardisert Parquet sammen med en audit-logg. Det ville gitt deg en solid inngangsport som resten av Power BI/Python/Excel/Copilot-arkitekturen kan stole på.

Sources
