/*==============================================================================
  Test 5: Full Pipeline - 01 Clean Data
  Load raw data, validate, generate derived variables, save to clean/
==============================================================================*/
version 18
clear all
set more off

cap log close _all
log using "$logs/01_clean_data.log", replace name(clean)

di "============================================================"
di "01_clean_data.do: Started at $S_DATE $S_TIME"
di "============================================================"

* --------------------------------------------------------------------------
* Load raw data
* --------------------------------------------------------------------------
use "$raw/policy_panel.dta", clear

di "Raw data loaded: `c(N)' observations, `c(k)' variables"

* --------------------------------------------------------------------------
* Validate panel structure
* --------------------------------------------------------------------------
isid state_id year
di "Panel ID validated: state_id x year is unique"

assert state_id >= 1 & state_id <= 30
assert year >= 2010 & year <= 2019
assert !missing(consumption)
assert !missing(pop)
assert !missing(income)
assert !missing(unemployment)

di "Basic assertions passed"

* --------------------------------------------------------------------------
* Generate treatment cohort variable
* --------------------------------------------------------------------------
gen cohort = treat_year
replace cohort = 0 if treat_year == 0
label define cohort_lbl 0 "Never treated" 2013 "Cohort 2013" ///
    2015 "Cohort 2015" 2017 "Cohort 2017"
label values cohort cohort_lbl

tab cohort, missing

* --------------------------------------------------------------------------
* Generate time-to-treatment variable
* --------------------------------------------------------------------------
gen time_to_treat = .
replace time_to_treat = year - treat_year if treat_year > 0

tab time_to_treat, missing

* --------------------------------------------------------------------------
* Generate post indicator
* --------------------------------------------------------------------------
gen post = (year >= treat_year) & (treat_year > 0)
label define post_lbl 0 "Pre/Never" 1 "Post-treatment"
label values post post_lbl

tab post treated, missing

* --------------------------------------------------------------------------
* Generate ever-treated indicator
* --------------------------------------------------------------------------
gen ever_treated = (treat_year > 0)
label define ever_lbl 0 "Never treated" 1 "Ever treated"
label values ever_treated ever_lbl

* --------------------------------------------------------------------------
* Generate log transformations
* --------------------------------------------------------------------------
gen ln_pop = ln(pop)
gen ln_income = ln(income)
gen ln_consumption = ln(consumption)

* --------------------------------------------------------------------------
* Label all variables
* --------------------------------------------------------------------------
label var state_id        "State identifier"
label var state_name      "State name"
label var year            "Calendar year"
label var consumption     "Consumption expenditure"
label var pop             "Population"
label var income          "Household income"
label var unemployment    "Unemployment rate"
label var treat_year      "Year of policy adoption (0=never)"
label var treated         "Treatment indicator (=1 if post-adoption)"
label var cohort          "Treatment cohort"
label var time_to_treat   "Periods relative to treatment"
label var post            "Post-treatment period indicator"
label var ever_treated    "Ever-treated indicator"
label var ln_pop          "Log population"
label var ln_income       "Log household income"
label var ln_consumption  "Log consumption expenditure"

* --------------------------------------------------------------------------
* Set panel structure
* --------------------------------------------------------------------------
xtset state_id year
di "Panel structure set: state_id x year"

* --------------------------------------------------------------------------
* Final validation
* --------------------------------------------------------------------------
assert `c(N)' == 300
assert treated == post if !missing(treated)

* Check treatment timing consistency
bysort state_id: assert treat_year == treat_year[1]

* Verify never-treated states have no treatment
assert treated == 0 if treat_year == 0

di "All validations passed"

* --------------------------------------------------------------------------
* Summary
* --------------------------------------------------------------------------
di _n "--- Cleaned Data Summary ---"
di "Observations: `c(N)'"
di "Variables: `c(k)'"

tab cohort, missing
summarize consumption pop income unemployment, detail

* --------------------------------------------------------------------------
* Save
* --------------------------------------------------------------------------
compress
save "$clean/panel_cleaned.dta", replace

di "Cleaned data saved to $clean/panel_cleaned.dta"
di "01_clean_data.do: Completed at $S_DATE $S_TIME"

log close clean
