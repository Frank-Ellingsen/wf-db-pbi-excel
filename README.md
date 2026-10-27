# WF1 Project Finance Controller (`pbi-rep-project-rapport`)

WF1 is a Power BI based controller and decision-support solution for municipal/project financial follow-up (KOSTRA), variance analysis, EAC/EOY forecasting, cost-driver analysis, data quality assurance (DQA), and What-If action simulation.

The project combines multi-file fact data (`fact_data`), KOSTRA function and chart-of-accounts dimensions (`dim_kostra_funksjon`, `dim_kostra_kontoplan`), organizational responsibility units (`dim_ansvar`), calendar intelligence (`dim_date`), What-If simulation parameters, and centralized DAX controller logic (`_Måltall`). The objective is to answer four practical controller questions:

1. **Where are we now?** (YTD budget vs. actuals, consumption %, and RAG status)
2. **What is driving the variance?** (Cost-driver decomposition, agency/temporary labor & overtime tracking, Pareto 80/20, and root-cause drilldown)
3. **Where are we likely to finish the year?** (Linear EAC/EOY run-rate forecast, remaining budget frame, and Tufte S-Curve trajectory)
4. **What action is required to return to budget balance?** (Required monthly run rate for zero balance and What-If scenario simulation on primary cost drivers and budget reallocation)

The design adheres to Edward Tufte's **Data-Ink Ratio** principles and Financial Times (FT) visual vocabulary standards, separating calculation, business rules, and presentation so that controller recommendations remain transparent and auditable.

---

## 1. Current Project Structure

The primary Power BI project is stored in the workspace root as `pbi-rep-project-rapport.pbip` (PBIR v4.0 / TMDL semantic model), alongside the legacy DuckDB sandbox under `powerbi/`.

```text
WF1/
├─ pbi-rep-project-rapport.pbip
├─ pbi-rep-project-rapport.Report/
│  ├─ definition.pbir
│  └─ definition/
│     ├─ report.json
│     ├─ version.json
│     └─ pages/
│        ├─ pages.json
│        ├─ qa03_filkontroll/                 (DQA 0: Fil- og Ingestion-kontroll)
│        ├─ qa01_dekning_og_kompletthet/      (DQA 1: Dekning & Kompletthet)
│        ├─ p01_executive_summary/            (01. Hovedrapport)
│        ├─ p02_trend_og_tidsserie/           (03.Tidserie-innsikt)
│        ├─ p04_avvik_og_drivere/             (04.Rotårsak)
│        ├─ 787cb8c3ce10a1326f82/             (041.Decomposition Tree)
│        ├─ p03_tufte_scurve_og_prognose/     (05. Månedlig Avvik og Prognose)
│        ├─ p_ft01_deviation/                 (FT 01: Deviation (Avviksanalyser))
│        ├─ p05_pareto_og_korrelasjon/        (06. Avvik-drivere)
│        └─ p06_scenario_simulering/          (07. What-If Scenario og Balanse)
├─ pbi-rep-project-rapport.SemanticModel/
│  ├─ definition.pbism
│  └─ definition/
│     ├─ database.tmdl                        (compatibilityLevel: 1606)
│     ├─ model.tmdl
│     ├─ expressions.tmdl                     (Folder ingestion helper queries)
│     ├─ relationships.tmdl
│     ├─ cultures/
│     │  └─ en-US.tmdl
│     └─ tables/
│        ├─ _Måltall.tmdl                     (66 centralized DAX measures)
│        ├─ _Valg_Maltall.tmdl                (Dynamic metric selector)
│        ├─ dim_ansvar.tmdl                   (Responsibility & organizational units)
│        ├─ dim_date.tmdl                     (Calendar & time intelligence)
│        ├─ dim_kostra_funksjon.tmdl          (KOSTRA function & service area hierarchy)
│        ├─ dim_kostra_kontoplan.tmdl         (6-digit account & KOSTRA art hierarchy)
│        ├─ dim_oppdatering.tmdl              (Model refresh timestamp)
│        ├─ fact_data.tmdl                    (Consolidated monthly budget & actuals)
│        ├─ Kutt_Hoveddrivere_Pct.tmdl        (What-If parameter: 0–30% driver cut)
│        └─ Omdisponering_Pct.tmdl            (What-If parameter: 0–100% reallocation)
└─ powerbi/
   ├─ Get-WF1-PowerBIStatus.ps1
   ├─ get_wf1_status_plus.ps1
   ├─ cleanup_wf1_pbi.ps1
   └─ reorganize_wf1_measure_folders.ps1
```

---

## 2. Data Architecture & Semantic Model

`pbi-rep-project-rapport.SemanticModel` ingests structured KOSTRA CSV files via Power Query (M) from `C:\Users\frank\Desktop\Kom\powerbi_kostra_datamodell\`:

```text
CSV Folder Source (faktatabeller/*.csv) + Dimension CSVs (dimensjoner/*.csv)
   ↓
Power Query (M) Transformations & Type Enforcement (expressions.tmdl + table partitions)
   ↓
Star Schema Semantic Model (fact_data + 4 core dimensions + What-If & utility tables)
   ↓
Centralized DAX Controller Logic (_Måltall)
   ↓
10 Tufte / FT-styled Power BI Report Pages (1920×1080)
```

### Semantic Model Tables

| Table | Type | Source / Partition | Key Columns & Purpose |
| :--- | :--- | :--- | :--- |
| `fact_data` | Fact | `Folder.Files("...\faktatabeller")` | `Source.Name`, `Dato`, `KOSTRA_Funksjonsgruppe_Kode`, `Kontokode_6Siffer`, `Ansvar_Kode`, `Sektor`, `Budsjett`, `Regnskap` |
| `dim_date` | Dimension (Time) | `dimensjoner\dim_date.csv` | `Dato` (Key), `Ar`, `Maned_Nummer`, `month`, `Maned_Navn`, `Uke`, `Start of month`, `Start of year`, `yyyy-mm` |
| `dim_ansvar` | Dimension | `dimensjoner\dim_ansvar.csv` | `Ansvar_Kode` (Key), `Enhet_Navn`, `Ansvar_Navn`, `Omrade_Kode`, `Omrade_Navn`, `Omrade_Kode_Navn`, `Ansvar_Kode_Navn`, `Er_Aktiv` |
| `dim_kostra_funksjon` | Dimension | `dimensjoner\dim_kostra_funksjon.csv` | `KOSTRA_Funksjonsgruppe_Kode` (Key), `KOSTRA_Funksjonsgruppe_Navn`, `Funksjonsgruppe_Kode_Navn`, `KOSTRA_Funksjon_ID`, `KOSTRA_Funksjon_Navn`, `Tjenesteomrade_Kode_Navn`, `Hovedfunksjon_Kode_Navn`, `Regnskapsregel_Beskrivelse` |
| `dim_kostra_kontoplan` | Dimension | `dimensjoner\dim_kostra_kontoplan.csv` | `Kontokode_6Siffer` (Key), `Kontonavn`, `Konto_Kode_Navn`, `KOSTRA_Art_4Siffer`, `KOSTRA_Art_4Siffer_Navn`, `KOSTRA_Art_3Siffer`, `Hovedgruppe_Kode_Navn`, `Hovedkategori_Kode_Navn`, `Kontoklasse_Kode_Navn`, `Er_Aktiv` |
| `_Måltall` | Measure Table | Calculated / Compressed row | Hosts 66 DAX measures across 11 functional display folders |
| `_Valg_Maltall` | Selector Table | In-memory `#table` | Dynamic metric selector (`1: Regnskap`, `2: Budsjett`, `3: Avvik Kr`, `4: Avvik YTD %`) |
| `Kutt_Hoveddrivere_Pct` | What-If Parameter | `0..30` (`0%` to `30%`, step `1%`) | Parameter column + `Kutt_Hoveddrivere_Pct Value` measure (default `10.0%`) |
| `Omdisponering_Pct` | What-If Parameter | `0..20 * 0.05` (`0%` to `100%`, step `5%`) | Parameter column + `Omdisponering_Pct Value` measure (default `50.0%`) |
| `dim_oppdatering` | Metadata | `DateTime.LocalNow()` | Single-column table (`Sist_Oppdatert`) tracking the latest data refresh |

---

## 3. Model Relationships

All relationships follow a clean single-direction (`many-to-one`) star schema into `fact_data`:

```text
dim_date[Dato] (1) ───────────────────────────────────► (*) fact_data[Dato]
dim_ansvar[Ansvar_Kode] (1) ──────────────────────────► (*) fact_data[Ansvar_Kode]
dim_kostra_funksjon[KOSTRA_Funksjonsgruppe_Kode] (1) ─► (*) fact_data[KOSTRA_Funksjonsgruppe_Kode]
dim_kostra_kontoplan[Kontokode_6Siffer] (1) ──────────► (*) fact_data[Kontokode_6Siffer]
```

---

## 4. Measure Architecture (`_Måltall`)

Implicit measures are discouraged (`discourageImplicitMeasures`). All 66 primary controller measures reside in `_Måltall` and are organized into 11 numbered display folders:

```text
_Måltall
├─ 01. Kjerne
├─ 02. MoM & Trend
├─ 03. YTD
├─ 04. Prognose & EOY
├─ 05. RAG & Formatering
├─ 06. Driveranalyse
├─ 07. Dynamisk Tekst
├─ 08. What-If Simulering
├─ 09. Tufte S-Curve
├─ 10. FT Visuals
└─ 11. DQA Kontroller
```

### Summary of Measures by Display Folder

#### `01. Kjerne` (Core Financials)
- `Sum Regnskap` = `SUM('fact_data'[Regnskap])`
- `Sum Budsjett` = `SUM('fact_data'[Budsjett])`
- `Årsbudsjett` = Full-year budget across `ALL('dim_date')` for selected `VALUES('dim_date'[Ar])`
- `Avvik Kr` = `[Sum Budsjett] - [Sum Regnskap]` *(Positive = favorable/mindreforbruk, Negative = unfavorable/merforbruk)*
- `Forbruk %` = `DIVIDE([Sum Regnskap], [Sum Budsjett], 0)`
- `Avvik %` = `DIVIDE([Avvik Kr], [Sum Budsjett], 0)`
- `abs Avvik`, `abs Avvik %`, `Max avvik %` (`1.2`), `Target Avvik %` (`1`)

#### `02. MoM & Trend` (Month-over-Month & Rolling Trends)
- `Regnskap PM` / `Budsjett PM` (`DATEADD('dim_date'[Dato], -1, MONTH)`)
- `Regnskap MoM Endring Kr` / `Regnskap MoM Endring %`
- `Regnskap 3M Moving Average` (3-month rolling average via `DATESINPERIOD`)
- `Regnskap Base 100` (Indexed consumption where January = `100.0`)

#### `03. YTD` (Year-to-Date)
- `Regnskap YTD` = `TOTALYTD([Sum Regnskap], 'dim_date'[Dato])`
- `Budsjett YTD` = `TOTALYTD([Sum Budsjett], 'dim_date'[Dato])`
- `Avvik YTD Kr` = `[Budsjett YTD] - [Regnskap YTD]`
- `Avvik YTD %` = `DIVIDE([Avvik YTD Kr], [Budsjett YTD], 0)`

#### `04. Prognose & EOY` (EAC / Year-End Forecasting)
- `Budsjett Resten av Året` (Remaining budget from `MAX('dim_date'[Dato]) + 1` to `ENDOFYEAR`)
- `EOY Estimat Lineær` (`ERP EOY Run Rate`) = `[Regnskap YTD] + [Budsjett Resten av Året]`
- `EOY Estimert Avvik Kr` (`EOY Run Rate Avvik`) = `[Årsbudsjett] - [EOY Estimat Lineær]`
- `EOY Estimert Avvik %` = `DIVIDE([EOY Estimert Avvik Kr], [Årsbudsjett], 0)`
- `EOY Årsbudsjett` = `[Årsbudsjett]`
- `Bullet Target 80%` / `Bullet Target 110%`

#### `05. RAG & Formatering` (Conditional Formatting & Status)
- `RAG Farge Avvik`:
  - `< -5.0%` (`Avvik YTD %`): `#D13438` (Muted Red — Significant overspend > 5%)
  - `-5.0%` to `0.0%`: `#FFB900` (Muted Amber — Minor overspend 0–5%)
  - `>= +5.0%`: `#0078D4` (Steel Blue — Significant underspend > 5%)
  - `0.0%` to `+5.0%`: `#107C41` (Forest Green — On track / favorable)
- `RAG Ikon Avvik` (`🔴`, `🟡`, `🔵`, `🟢`)
- `Status Indikator` (Descriptive RAG status text)
- `Avvik Bar Farge` (`#D13438` if `Avvik Kr < 0`, else `#107C41`)

#### `06. Driveranalyse` (Cost Drivers & Pareto)
- `Merforbruk Kr` (`Overforbruk Kr`, `ERP Negativ Kostnadsdriver`) = `IF([Avvik Kr] < 0, ABS([Avvik Kr]), 0)`
- `Mindreforbruk Kr` = `IF([Avvik Kr] > 0, [Avvik Kr], 0)`
- `Pct Bidrag til Totalt Merforbruk` (`Pct Bidrag til Totalt Overforbruk`, `ERP Negativ Driver Andel %`)
- `Pct Bidrag til Total Regnskap`
- `Rangering Merforbruk` (`Rangering Overforbruk`) = Dense `RANKX` across `dim_kostra_kontoplan[Konto_Kode_Navn]`
- `ERP Pareto Kumulativ %` = Cumulative share of total overspend across ranked accounts
- `Kostnad Vikarer Kr` = Actuals on accounts `102000`, `102013`, `127040`
- `Kostnad Overtid Kr` = Actuals on account `104000`
- `ERP Største Kostnadsdriver` / `ERP Største Kostnadsdriver Beløp`

#### `07. Dynamisk Tekst` (Selection Context & Controller Narratives)
- Selection context measures: `Txt Valgt År`, `Txt Valgt Måned`, `Txt Valgt Område`, `Txt Valgt Ansvar`, `Txt Valgt Tjeneste og Funksjon`
- Dynamic headers: `Txt Master Selection Header`, `Dynamisk Rapporttittel`, `Dynamisk Rapportittel Komplett`
- Automated narratives: `Story Executive Summary`, `Story Time Narrative`, `Story Forecast Narrative`, `Story Root Cause Detail`, `Forecast Action Summary`

#### `08. What-If Simulering` (Action & Scenario Modeling)
- `Simulert Kutt Hoveddrivere Kr` = 50% reduction in overspend on temporary staff & overtime (`102013`, `102000`, `104000`)
- `Simulert Frigjort Mindreforbruk Kr` = 20% reallocation of favorable variance on regular payroll (`101000`, `109000`)
- `Simulert Totale Tiltak Kr` = `[Simulert Kutt Hoveddrivere Kr] + [Simulert Frigjort Mindreforbruk Kr]`
- `Simulert EOY Avvik Etter Tiltak Kr` = `[EOY Estimert Avvik Kr] + [Simulert Totale Tiltak Kr]`
- `Simulert EOY Status Indikator` (`🟢 I Balanse / Overskudd`, `🟡 Nær Balanse`, `🔴 Fortsatt Underskudd`)
- `ERP Driver Tiltaksbehov Måned`, `ERP Driver Tiltaksbehov Restår`, `ERP Driver Tiltaksgrad %`

#### `09. Tufte S-Curve` (Cumulative Trajectory & Run-Rate Targets)
- `Avvik Akkumulert S-Curve` = `TOTALYTD([Avvik Kr], 'dim_date'[Dato])`
- `ERP Actual Historical` (Actuals up to `LASTDATE('fact_data'[Dato])`)
- `ERP Forecast Trend` (3M moving average projected for dates after `LASTDATE('fact_data'[Dato])`)
- `ERP Resterende Ramme` = `[Budsjett Resten av Året]`
- `ERP Nødvendig Månedlig Nivå` = `DIVIDE([Budsjett Resten av Året], 4, 0)`

#### `10. FT Visuals` (Financial Times Visual Vocabulary Measures)
- `FT_Dev_Diverging_Avvik_Kr`, `FT_Corr_Scatter_Size`
- `FT_Time_Cumulative_Actual`, `FT_Time_Cumulative_Budget`, `FT_Time_Cumulative_EAC`
- `FT_Time_Diverging_Deficit`, `FT_Time_Diverging_Surplus`, `FT_Time_Stepped_Budget`
- `Corr Regnskap vs Budsjett` (Pearson $r$ across months), `Correlation Strength`

#### `11. DQA Kontroller` (Data Quality & Ingestion Auditing)
- Coverage & completeness: `QA Har Regnskap`, `QA Har Budsjett`, `QA Dekningsstatus Indikator`, `QA Dekningsgrad %`
- Referential integrity (orphan key checks): `QA Umappede Kontokoder Antall`, `QA Umappede Kontokoder Regnskap Kr`, `QA Umappede Ansvar Antall`, `QA Umappede Funksjoner Antall`, `QA Nøkkelstatus Sammendrag`
- File ingestion & anomaly detection: `QA Antall Filer Importert`, `QA Antall Rader Per Fil`, `QA Duplikatsjekk Filnavn`, `QA Ubudsjetterte Kostnader Kr`, `QA Ubudsjetterte Poster Antall`, `QA Ekstreme MoM Endringer`, `QA Negativt Regnskap Antall`, `QA Sist Oppdatert`

---

## 5. Report Pages (`pbi-rep-project-rapport.Report`)

All 10 report pages are configured at **1920 × 1080** (`FitToPage`) using the `Fluent2-CY26SU10` base theme and follow Tufte's high data-ink ratio design standards:

| Order | Page Folder ID | Display Name | Primary Analytical Role |
| :---: | :--- | :--- | :--- |
| 1 | `qa03_filkontroll` | **DQA 0: Fil- og Ingestion-kontroll (Folder Metadata)** | Audits imported CSV files (`Source.Name`), row counts per file, duplicate period/sector checks, and refresh timestamp (`QA Sist Oppdatert`). |
| 2 | `qa01_dekning_og_kompletthet` | **DQA 1: Dekning & Kompletthet (Data Coverage)** | Validates referential integrity (`QA Nøkkelstatus Sammendrag`), unmapped accounts/units/functions, unbudgeted costs, and data coverage %. |
| 3 | `p01_executive_summary` | **01. Hovedrapport** *(Active Page)* | Executive YTD overview: KPI cards, dynamic selection header, executive narrative, and variance breakdown by area/service. |
| 4 | `p02_trend_og_tidsserie` | **03.Tidserie-innsikt** | Monthly actual vs. budget evolution, 3-month rolling average (`Regnskap 3M Moving Average`), MoM changes, and Base-100 indexing. |
| 5 | `p04_avvik_og_drivere` | **04.Rotårsak** | Root-cause variance analysis across organizational units (`dim_ansvar`), KOSTRA functions, and accounts, tracking agency labor and overtime. |
| 6 | `787cb8c3ce10a1326f82` | **041.Decomposition Tree** | Interactive drilldown of variances across Area → Unit → Service Area → Function Group → Account Class → Account. |
| 7 | `p03_tufte_scurve_og_prognose` | **05. Månedlig Avvik og Prognose** | Tufte S-Curve (`FT_Time_Cumulative_Actual` vs. `FT_Time_Cumulative_Budget`), EOY linear forecast, and required monthly run-rate target. |
| 8 | `p_ft01_deviation` | **FT 01: Deviation (Avviksanalyser)** | Diverging variance bars (`FT_Dev_Diverging_Avvik_Kr`, surplus vs. deficit) styled according to the FT Visual Vocabulary. |
| 9 | `p05_pareto_og_korrelasjon` | **06. Avvik-drivere** | Account-level overspend ranking (`Rangering Merforbruk`), Pareto cumulative curve (`ERP Pareto Kumulativ %`), and budget-vs-actual correlation ($r$). |
| 10 | `p06_scenario_simulering` | **07. What-If Scenario og Balanse** | Interactive controller simulation combining driver cuts (`Kutt_Hoveddrivere_Pct`) and payroll reallocation (`Omdisponering_Pct`) to close the EOY gap. |

---

## 6. Utilities & Status Scripts (`powerbi/`)

The PowerShell scripts in `powerbi/` support automated inspection and maintenance of the PBIP project:

- **`powerbi/Get-WF1-PowerBIStatus.ps1`**: Scans `C:\Users\frank\Desktop\WF1` for `.pbip`, `.Report`, and `.SemanticModel` folders, outputting page inventory, visual counts by type, TMDL table definitions, relationships, and DAX measure inventory.
- **`powerbi/get_wf1_status_plus.ps1`**: Generates a comprehensive diagnostic dump (`WF1_STATUS_PLUS.txt`) of the report tree, TMDL definitions, `_Måltall` measures, visual bindings, slicer configurations, and JSON validation checks.
- **`powerbi/cleanup_wf1_pbi.ps1`**: Backs up the report definition and removes duplicate single-field slicers on a target page while validating all `visual.json` files.
- **`powerbi/reorganize_wf1_measure_folders.ps1`**: Utility script for batch-updating `displayFolder` metadata in TMDL measure tables with automatic timestamped backups.

### Safe TMDL / PBIR Editing Workflow

1. Close Power BI Desktop before making direct edits to `.tmdl` or `visual.json` files.
2. Create a backup of the target file or folder before editing.
3. Keep table headers (`table _Måltall`) and partition blocks (`partition _Måltall = m`) intact.
4. Run `powerbi/Get-WF1-PowerBIStatus.ps1` or `powerbi/get_wf1_status_plus.ps1` to verify JSON and TMDL integrity.
5. Reopen `pbi-rep-project-rapport.pbip` in Power BI Desktop to verify visuals and measures.
