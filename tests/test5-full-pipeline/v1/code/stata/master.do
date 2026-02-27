/*==============================================================================
  Test 5: Full Pipeline - Master Script
  Runs all analysis scripts in order
==============================================================================*/
version 18
clear all
set more off
set seed 12345

* Set paths
global root "."
global code "$root/code/stata"
global data "$root/data"
global raw "$data/raw"
global clean "$data/clean"
global temp "$data/temp"
global output "$root/output"
global tables "$output/tables"
global figures "$output/figures"
global logs "$output/logs"

* Create output directories
cap mkdir "$output"
cap mkdir "$tables"
cap mkdir "$figures"
cap mkdir "$logs"
cap mkdir "$clean"
cap mkdir "$temp"

* Run scripts in order
do "$code/01_clean_data.do"
do "$code/02_desc_stats.do"
do "$code/03_did_main.do"
do "$code/04_tables_export.do"

* Verify outputs exist
cap confirm file "$clean/panel_cleaned.dta"
if _rc == 0 di "OK: panel_cleaned.dta exists"
else di "MISSING: panel_cleaned.dta"

cap confirm file "$tables/tab_desc_stats.tex"
if _rc == 0 di "OK: tab_desc_stats.tex exists"
else di "MISSING: tab_desc_stats.tex"

cap confirm file "$tables/tab_did_main.tex"
if _rc == 0 di "OK: tab_did_main.tex exists"
else di "MISSING: tab_did_main.tex"

di "Master.do completed"
