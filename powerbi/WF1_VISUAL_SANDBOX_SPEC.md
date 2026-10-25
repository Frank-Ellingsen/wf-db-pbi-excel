# WF1 Visual Sandbox - Visual Build Specification

## 00_Control
Slicers:
- dim_date[year]
- dim_date[tertial]
- dim_date[year_month]
- dim_kostra_function[main_function_name]
- dim_kostra_function[service_area_name]
- dim_kostra_function[function_group_name]
- dim_kostra_function[kostra_function_name]
- dim_account[account_class_name]
- dim_account[main_category_name]
- dim_account[main_group_name]
- dim_account[kostra_art_name]
- dim_account[account_name]

Cards:
- [Selected YYYY-MM]
- [Selected Function]
- [Selected Account]
- [ERP Rader]
- [Framsikt Rader]
- [ERP Mapping %]
- [Framsikt Mapping %]
- [Overall Data Quality Status]

## 10_Status
Cards:
- [ERP Budsjett YTD]
- [ERP Regnskap YTD]
- [ERP Avvik YTD]
- [ERP Avvik YTD %]
- [ERP RAG Symbol] with font color = [ERP RAG Color]

KOSTRA matrix rows hierarchy:
1. dim_kostra_function[main_function_name]
2. dim_kostra_function[service_area_name]
3. dim_kostra_function[function_group_name]
4. dim_kostra_function[kostra_function_name]
Values:
- [ERP Budsjett YTD]
- [ERP Regnskap YTD]
- [ERP Avvik YTD]
- [ERP Avvik YTD %]
- [ERP RAG Symbol]
Formatting:
- Avvik: data bars using [CF ERP Avvik Bar]
- Avvik %: font/background field value [ERP RAG Color]
- RAG Symbol: font color [ERP RAG Color]

Account matrix rows hierarchy:
1. dim_account[account_class_name]
2. dim_account[main_category_name]
3. dim_account[main_group_name]
4. dim_account[kostra_art_name]
5. dim_account[account_name]
Same values/formatting as KOSTRA matrix.

## 11_Time
1. Line: axis dim_date[year_month], values [ERP Regnskap], [ERP Budsjett]
2. Combo: shared axis dim_date[year_month], column [ERP Regnskap], line [ERP Budsjett]
3. MoM diverging column: axis dim_date[year_month], value [ERP Regnskap MoM]
4. MoM % line/column: axis dim_date[year_month], value [ERP Regnskap MoM %]
5. Running line: axis dim_date[year_month], values [ERP Regnskap Running], [ERP Budsjett Running]
6. Moving average: axis dim_date[year_month], values [ERP Regnskap], [ERP Regnskap Moving Avg 3M]
7. Small multiples: axis dim_date[year_month], value [ERP Avvik], multiples dim_kostra_function[service_area_name]
8. Matrix sparklines: rows dim_kostra_function[kostra_function_name], value [ERP Regnskap], sparkline axis dim_date[date]

## 12_Deviation
1. Diverging bar: Y dim_account[account_name], X [ERP Avvik YTD]
2. Ordered bar: Y dim_kostra_function[kostra_function_name], X [ERP Absolutt Avvik]
3. Waterfall: category dim_account[main_group_name], Y [ERP Avvik]
4. Matrix: Account hierarchy + Budsjett YTD, Regnskap YTD, Avvik YTD, Avvik YTD %, RAG
5. Top variance: rank with [ERP Konto Rank Avvik]
6. Function variance: rank with [ERP Funksjon Rank Avvik]
7. Contribution: [ERP Avviksbidrag %]
8. Favorable/unfavorable: [ERP Mindreforbruk], [ERP Merforbruk]

## 20_Diagnosis
Decomposition Tree:
Analyze: [ERP Absolutt Avvik] and alternate [ERP Avvik]
Explain by:
- main_function_name
- service_area_name
- function_group_name
- kostra_function_name
- account_class_name
- main_category_name
- main_group_name
- kostra_art_name
- account_name
- fact_erp_finance[location]

Scatter diagnostic:
X [ERP Budsjett]
Y [ERP Regnskap]
Size [ERP Absolutt Avvik]
Details dim_account[account_name]
Legend dim_account[account_class_name]

## 21_Ranking
- Ordered horizontal bar by Account with [ERP Absolutt Avvik]
- Ordered horizontal bar by KOSTRA Function with [ERP Absolutt Avvik]
- Rank table with [ERP Konto Rank Avvik] / [ERP Funksjon Rank Avvik]
- Top/Bottom experiments controlled by visual Top N filters

## 22_Distribution
Native first:
- Histogram/binning experiments for ERP Avvik / Avvik %
- Scatter distribution by account/function
Python candidates later: boxplot, violin, beeswarm, density

## 23_Correlation
Scatter A: X [ERP Budsjett], Y [ERP Regnskap], Size [ERP Absolutt Avvik]
Scatter B: X [ERP Budsjettforbruk %], Y [ERP Avvik %], Size [ERP Absolutt Avvik]
Try account and KOSTRA dimensions as details/legend.

## 30_Forecast_Experimental
Cards:
- [EOY Årsbudsjett]
- [ERP EOY Run Rate]
- [EOY Run Rate Avvik]
- [EOY Run Rate Avvik %]
- [EOY RAG]
Mark page title/subtitle EXPERIMENTAL until source semantics are validated.

## 31_EOY_Experimental
Waterfall/bridge experiments around YTD -> remaining -> EOY.
Use EOY measures only as experimental analytics.

## 40_Prescription_Experimental
Cards:
- [EOY Required Correction]
- [EOY Required Correction %]
- [EOY Required Monthly Correction]
- [EOY Måneder Igjen]

## 41_ZeroBalance_Experimental
Cards:
- [EOY Årsbudsjett]
- [ERP Regnskap YTD]
- [EOY Resterende Ramme]
- [EOY Måneder Igjen]
- [EOY Zero Balance Monthly Rate]

## 42_Scenario_Experimental
Reserved for What-if parameter driven scenarios. No hard-coded scenario values in measures.

## 50_DataQuality
Cards:
- [ERP Mapping %]
- [ERP Unmapped Function IDs]
- [ERP Unmapped Function Rows]
- [ERP Unmapped Account Rows]
- [Framsikt Mapping %]
- [Framsikt Unmapped Function IDs]
- [Framsikt Unmapped Function Rows]
- [Overall Data Quality Status]
Use [Data Quality Color] for status formatting.

## 80_NativeLab
A/B testing canvas for native line, column, combo, waterfall, scatter, treemap, decomposition tree, matrix, small multiples, cards.

## 90_PythonLab
Only after native evaluation. Priority candidates:
- Violin
- Boxplot
- Beeswarm
- Calendar heatmap
- Advanced heatmap
- Forecast fan/confidence bands
- Parallel coordinates
