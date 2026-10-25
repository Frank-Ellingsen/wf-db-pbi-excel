# WF1 Visual Sandbox Pack

Target project: `C:\Users\frank\Desktop\WF1\powerbi\pbi-rep-project`

## Purpose
A paste-ready planning pack for building the Power BI Visual Sandbox on the validated WF1 semantic model.
The pack deliberately does not overwrite PBIR visual JSON because the current report has only one existing blank/minimal page and no source visual definitions to safely clone.

## Recommended report pages
00_Control
10_Status
11_Time
12_Deviation
20_Diagnosis
21_Ranking
22_Distribution
23_Correlation
30_Forecast_Experimental
31_EOY_Experimental
40_Prescription_Experimental
41_ZeroBalance_Experimental
42_Scenario_Experimental
50_DataQuality
80_NativeLab
90_PythonLab

## Global rule
Use dimension fields for axes/slicers and `_Measures` measures for values. Do not use raw numeric fact columns directly in visuals unless the visual is explicitly a data-quality diagnostic.

## Semantic spine
YYYY-MM -> Budsjett -> Regnskap -> Avvik -> Avvik % -> RAG
Avvik = Budsjett - Regnskap. Positive = mindreforbruk. Negative = merforbruk.

## Build order
1. 00_Control
2. 10_Status
3. 11_Time
4. 12_Deviation
5. 20_Diagnosis
6. 21_Ranking / 23_Correlation
7. 50_DataQuality
8. Forecast/EOY/Prescription after business validation
9. Python only where native Power BI is insufficient
