# WF1 Project Finance Controller

WF1 is a Power BI based controller and decision-support solution for financial follow-up, variance analysis, forecasting, cost-driver analysis, and action planning.

The project combines ERP actual/budget data, Framsikt planning data, KOSTRA dimensions, budget organization, a Power BI semantic model, and rule-based controller logic. The objective is to answer four practical questions:

1. Where are we now?
2. What is driving the variance?
3. Where are we likely to finish the year?
4. What action is required to return to budget balance?

The design deliberately separates calculation, business rules, and presentation so that recommendations can be transparent and auditable without depending on generative AI.

---

## 1. Current project structure

The Power BI project is stored as PBIP and currently contains the report and semantic-model folders plus supporting scripts and status artifacts. The current project status file shows the main PBIP components under `pbi-rep-project.Report` and `pbi-rep-project.SemanticModel`. [^status]

```text
WF1/
├─ powerbi/
│  ├─ pbi-rep-project.pbip
│  ├─ pbi-rep-project.Report/
│  │  └─ definition/
│  │     ├─ report.json
│  │     └─ pages/
│  ├─ pbi-rep-project.SemanticModel/
│  │  └─ definition/
│  │     ├─ model.tmdl
│  │     ├─ relationships.tmdl
│  │     └─ tables/
│  │        ├─ _Measures.tmdl
│  │        ├─ dim_account.tmdl
│  │        ├─ dim_date.tmdl
│  │        ├─ dim_kostra_function.tmdl
│  │        ├─ dim_budget_organization.tmdl
│  │        ├─ fact_erp_finance.tmdl
│  │        └─ fact_framsikt_finance.tmdl
│  ├─ Get-WF1-PowerBIStatus.ps1
│  ├─ get_wf1_status_plus.ps1
│  ├─ cleanup_wf1_pbi.ps1
│  └─ reorganize_wf1_measure_folders.ps1
└─ db/
   └─ project_finance_powerbi.duckdb
```

> Note: The exact model files should be treated as the source of truth. The tree above documents the working architecture and the principal objects discussed in the project.

---

## 2. Data architecture

The reporting flow is designed around a Gold reporting layer and a Power BI oriented DuckDB database.

```text
Source data
   ↓
Cleaning / Silver
   ↓
Gold finance model
   ↓
Gold reporting transformations
   ↓
Power BI DuckDB
   ↓
Power BI semantic model
   ↓
Reports and controller decision support
```

Principal reporting entities:

- `fact_erp_finance`: ERP actual and budget data
- `fact_framsikt_finance`: Framsikt actual/budget/planning data
- `dim_date`: calendar and time intelligence
- `dim_account`: account hierarchy
- `dim_kostra_function`: KOSTRA function hierarchy
- `dim_budget_organization`: budget organization hierarchy
- `_Measures`: centralized DAX measures

The current Power BI project includes the PBIP report and semantic-model structure documented in the generated project status. [^status]

---

## 3. Budget organization

ERP finance data is enriched with a budget-organization key. This allows organizational slicing independently of account and KOSTRA dimensions.

The intended relationship is:

```text
dim_budget_organization[budget_organization_key]
                    1
                    │
                    ▼
                    *
fact_erp_finance[budget_organization_key]
```

The organization slicer can therefore be synchronized across ERP-based report pages while time filters can remain page-specific.

Example report context:

```text
Viser: 2024-08 | Helse og mestring
```

For time-series pages, the context is year-based instead:

```text
Viser: 2024 | Helse og mestring
```

---

## 4. Report-filter strategy

Not all pages should use the same time grain.

### Point-in-time / YTD pages

Examples:

- Status
- Deviation
- Diagnosis
- Ranking

These can use `dim_date[year_month]`.

### Full-year time-series pages

`11_Time` should use `dim_date[year]` and leave `year_month` unfiltered so that all months in the selected year remain available to the visual.

Recommended synchronization model:

- Budget organization: sync broadly
- Account: sync where analytically useful
- KOSTRA function: sync where analytically useful
- `year_month`: do not sync to pages requiring a full annual timeline
- `year`: use locally on annual trend/forecast pages

---

## 5. Measure architecture

Measures are centralized in `_Measures` and organized by function.

Recommended folder structure:

```text
01 Base
02 Variance
03 Status
04 Time Intelligence
05 Context & Totals
06 Share & Contribution
07 Ranking
08 Forecast & Prediction
   ├─ Base
   ├─ Series
   ├─ EOY
   └─ Gauge
09 Balance & Action
   ├─ Current
   └─ Legacy
10 Cost Drivers
   ├─ Base
   ├─ Ranking
   ├─ Contribution
   ├─ Pareto
   ├─ Action
   └─ Top Driver
11 Correlation
   ├─ Measures
   ├─ Interpretation
   └─ Quality
12 Data Quality
13 RAG
14 Conditional Formatting
15 Selection Context
16 Titles & Labels
17 Storytelling Commentary
90 Sandbox
```

### Format convention

Numeric format strings should not embed color names such as `[Red]`.

Use numeric formatting for representation:

```text
#,##0.00;-#,##0.00
0.0%;-0.0%
```

Use dedicated color measures such as RAG color measures for conditional formatting.

---

## 6. Core financial measures

The model includes core ERP and Framsikt measures for:

- actuals
- budget
- variance
- variance percentage
- budget consumption
- YTD
- previous month
- MoM change
- prior year
- YoY change
- running values
- rolling three-month average

The project also contains context, contribution, ranking, data-quality, RAG, conditional-formatting, title and narrative measures. The current semantic-model status confirms these functional measure groups are part of the model. [^status]

---

## 7. Forecasting framework

Forecasting is intentionally divided into multiple perspectives rather than presenting one forecast as absolute truth.

### YTD run rate

```text
ERP EOY Run Rate
```

Conceptually:

```text
Actual YTD / elapsed months × 12
```

### Recent run rate

```text
ERP Forecast Monthly Rate
ERP Forecast EOY
```

Conceptually:

```text
Actual YTD
+
remaining months × recent monthly run rate
```

### Trend forecast

```text
ERP Forecast Trend
```

This gives a trend-based alternative for the remaining periods.

### Forecast variance

```text
ERP Forecast EOY Avvik
ERP Forecast EOY Avvik %
ERP Forecast EOY Forbruk %
```

The forecast page should therefore communicate:

```text
Actual YTD
   ↓
Forecast EOY
   ↓
EOY variance
   ↓
Required action
```

---

## 8. Balance and action logic

The controller logic calculates how much financial room remains and what monthly cost level is required to reach year-end balance.

Key concepts:

```text
Annual budget
-
Actual YTD
=
Remaining budget capacity
```

```text
Remaining budget capacity
/
Months remaining
=
Required monthly level
```

```text
Forecast monthly rate
-
Required monthly level
=
Monthly action requirement
```

Core measures include:

- `ERP Akkumulert Avvik YTD`
- `ERP Tillatt Regnskap Resten Av Året`
- `ERP Nødvendig Månedlig Nivå`
- `ERP Månedlig Tiltaksbehov`
- `ERP Månedlig Tiltaksbehov %`
- `ERP Total Tiltaksbehov`

This converts a forecast from a passive prediction into an actionable controller metric.

---

## 9. Cost-driver analysis

Negative budget variance is decomposed by account to identify the drivers of overspending.

Core concepts:

- negative cost driver amount
- contribution to total unfavorable variance
- rank
- cumulative Pareto percentage
- indicative action allocation
- largest driver

Recommended measures:

```text
ERP Negativ Kostnadsdriver
ERP Total Negativ Kostnadsdriver
ERP Negativ Driver Rank
ERP Negativ Driver Andel %
ERP Pareto Kumulativ Driver
ERP Pareto Kumulativ %
ERP Pareto 80 %
ERP Driver Tiltaksbehov Måned
ERP Driver Tiltaksbehov Restår
ERP Driver Tiltaksgrad %
ERP Største Kostnadsdriver
ERP Største Kostnadsdriver Beløp
```

### Pareto visual

Use a line and clustered-column visual:

- Category: account
- Column: negative cost driver
- Line: cumulative driver percentage
- Optional reference: 80%

The purpose is prioritization, not an assumption that real data must follow an exact 80/20 distribution.

### Top-5 driver table

Recommended columns:

```text
Account
Rank
Negative YTD variance
Share of negative variance
Indicative action/month
Action remaining year
```

Apply a visual filter:

```text
ERP Negativ Driver Rank <= 5
```

---

## 10. Controllability and governance mapping

The next model extension is a governed action-mapping dimension rather than hardcoded DAX assumptions.

Proposed source/master table:

```text
cost_driver_action_mapping
```

Recommended structure:

| Field                          | Purpose                                   |
| ------------------------------ | ----------------------------------------- |
| `account_code`                 | join key to account dimension             |
| `account_name`                 | readable label                            |
| `driver_category`              | cost-driver category                      |
| `controllability`              | HIGH / MEDIUM / LOW                       |
| `binding_type`                 | rule/binding classification               |
| `action_horizon`               | expected realization horizon              |
| `max_action_factor`            | governed maximum realizability assumption |
| `action_category`              | standardized action type                  |
| `recommended_action`           | standard non-AI action text               |
| `requires_management_approval` | governance flag                           |
| `requires_political_decision`  | governance flag                           |
| `requires_legal_review`        | governance flag                           |
| `active`                       | active/inactive mapping                   |
| `valid_from`                   | start of validity                         |
| `valid_to`                     | end of validity                           |
| `source_reference`             | source or governing reference             |
| `mapping_note`                 | rationale/documentation                   |

Suggested `binding_type` domain:

```text
OPERATIONAL
CONTRACT
TARIFF
LEGAL
POLITICAL
STATUTORY_SERVICE
FINANCIAL
UNKNOWN
```

These are project governance categories, not legal classifications.

### Design principle

A large cost driver is not automatically a feasible short-term saving.

The model should distinguish:

```text
Financial importance
        ×
Controllability
        ×
Binding
        ×
Action horizon
        ↓
Realizable action
```

Large, low-controllability items can still have high decision priority because escalation may be required.

---

## 11. Planned realizable-action measures

After `dim_cost_driver_action` is created and related to `dim_account`, the model can safely add:

```text
ERP Realiserbar Tiltaksfaktor
ERP Driver Handlingsstatus
ERP Driver Teoretisk Tiltak Restår
ERP Driver Realiserbart Tiltak Restår
ERP Driver Realiserbart Tiltak Måned
ERP Realiserbart Tiltak Totalt
ERP Realiserbart Tiltak Måned Totalt
ERP Tiltaksgap
ERP Tiltaksgap %
ERP Tiltaksdekning %
ERP Tiltaksdekning Capped %
ERP Udekket Tiltaksbehov Måned
ERP Tiltaksstatus
ERP Tiltaksstatus Color
ERP Driver Prioritet
ERP Driver Prioritet Color
ERP Tiltaksanbefaling
```

These measures should **not** be added until the mapping dimension exists. This avoids DAX dependencies on nonexistent objects.

Target decision chain:

```text
Forecast EOY
   ↓
Forecast gap
   ↓
Required action
   ↓
Cost drivers
   ↓
Controllability + binding + horizon
   ↓
Realizable actions
   ↓
Action coverage
   ↓
Action gap
   ↓
Act now / investigate / plan / monitor / escalate
```

---

## 12. Correlation analysis

Correlation is intended as exploratory driver analysis, not proof of causality.

Current analytical measures include:

```text
Corr Regnskap vs Budsjett
Corr Regnskap vs Avvik
Correlation Strength
Correlation Direction
Correlation Observations
```

Recommended visual pattern:

- Scatter: Budget vs Actual, one point per month
- Scatter: Actual vs Variance, one point per month
- Controller cards: correlation coefficient, strength, direction, observations

For account/function contribution analysis, use either:

- cross-sectional analysis at a selected month, where each point is an account/function, or
- time-series analysis for a selected account/function, where each point is a month.

Do not interpret financial-variable correlation as causal evidence.

---

## 13. Suggested report pages

### `00_Control`

Central filter/control page.

Use for global business dimensions while keeping time-grain behavior page-specific.

### `10_Status`

Executive/YTD financial status:

- budget YTD
- actual YTD
- variance YTD
- variance %
- RAG
- selected-report context

### `11_Time`

Full-year time reporting:

- year filter
- all months in selected year
- actual vs budget by month
- monthly variance
- rolling trends
- historical actual and forecast series

Do not restrict this page with a synchronized single `year_month` selection.

### Deviation / diagnosis / ranking

Use account and KOSTRA views to explain why variance exists and rank major contributors.

### Correlation

Use exploratory scatter analysis and correlation measures to investigate relationships.

### Forecast & Action

Recommended layout:

```text
Forecast & Action
Selected year | Selected budget organization

[KPI Actual YTD]
[KPI Forecast EOY]
[KPI EOY variance]
[KPI Monthly action requirement]

[Actual → Forecast → Budget chart]    [EOY budget-consumption gauge]

[Balance / required monthly level]    [Top cost-driver Pareto]

[Top-5 driver table]

[Dynamic action summary]
```

When governed controllability mapping is added, extend the page with:

- realizable actions
- action coverage %
- action gap
- binding status
- action horizon
- escalation requirement

---

## 14. Conditional formatting conventions

Use color consistently and keep numeric format independent of color.

Suggested status palette:

```text
GREEN   #107C10
YELLOW  #FFB900
RED     #D13438
GRAY    #A19F9D
```

For tables and matrices:

- unfavorable variance: light red
- favorable variance: light green
- contribution: data bars
- priority/action status: separate governed colors

Avoid coloring every metric simply because conditional formatting is available. Color should communicate status or required attention.

---

## 15. Power BI context text

Use dynamic context cards to make hidden/synchronized filters visible to the user.

Examples:

```text
Viser: 2024-08 | Helse og mestring
```

and on annual pages:

```text
Viser: 2024 | Helse og mestring
```

Relevant measures include:

```text
Selected Report Context
Selected Status Context
Selected Time Context
Selected Forecast Context
```

---

## 16. Validation workflow

Before changing report visuals, validate the pipeline in order:

```text
Gold build
   ↓
Gold reporting build
   ↓
Power BI DuckDB build
   ↓
DuckDB validation
   ↓
Semantic model refresh
   ↓
Relationship validation
   ↓
Measure validation
   ↓
Report validation
```

For model-file edits:

1. Close Power BI Desktop before direct TMDL changes.
2. Back up the existing file.
3. Make small targeted edits.
4. Preserve table declaration and calculated partition.
5. Validate that `_Measures.tmdl` starts with `table _Measures`.
6. Validate the final calculated partition remains present.
7. Reopen the PBIP and test affected visuals.

---

## 17. Development principles

### Transparent logic over opaque recommendations

Forecasts and recommendations should be decomposable into measures and governed assumptions.

### Separate facts from assumptions

Examples of assumptions that belong in mapping/configuration data:

- controllability
- realizability factor
- action horizon
- legal/contract/political binding classification
- approval requirements

### Do not hardcode governance conclusions in DAX

DAX should evaluate rules. Master data should define the business/governance attributes used by those rules.

### Keep recommendations advisory

Examples:

- `Tiltak nå`
- `Undersøk`
- `Planlegg`
- `Overvåk`
- `Eskaler`

The report should support decisions, not claim that a cost can legally or operationally be removed solely because it has an unfavorable variance.

---

## 18. Next development steps

1. Create `cost_driver_action_mapping` master data.
2. Load it through the existing data pipeline.
3. Materialize `dim_cost_driver_action` in the Power BI DuckDB.
4. Add the relationship to `dim_account` using `account_code`.
5. Add realizable-action and action-gap DAX measures.
6. Complete the Forecast & Action page.
7. Add action-coverage gauge and binding-aware Top-5 table.
8. Validate filter behavior across organization, account, KOSTRA and year.
9. Add further operational driver data when available, such as staffing, overtime, temporary labor, absence or activity volumes.

---

## 19. Project direction

WF1 is evolving from a conventional budget-vs-actual report into a rule-based controller framework:

```text
DESCRIPTIVE
What happened?
        ↓
DIAGNOSTIC
Why did it happen?
        ↓
PREDICTIVE
Where are we heading?
        ↓
PRESCRIPTIVE
What action is required?
        ↓
GOVERNED ACTION
What can realistically be done, when, and under which constraints?
```

That final layer is particularly important: financial impact alone is not enough. Recommendations should incorporate operational controllability, time horizon, contractual constraints, tariff constraints, legal requirements, political decisions, and documented governance assumptions.

---

## 20. Status

The PBIP report/semantic-model structure and supporting Power BI project utilities are present in the current WF1 project status. [^status]

Current development focus:

```text
Forecasting
Cost-driver analysis
Pareto / Top-5 drivers
Action requirement
Controllability mapping
Realizable actions
Action-gap analysis
Governance-aware recommendations
```

---

[^status]: Source: `WF1_STATUS_PLUS.txt`, generated project-status extract from the WF1 Power BI project.
