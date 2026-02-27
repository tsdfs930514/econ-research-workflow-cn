/*==============================================================================
  Install required packages for IV analysis
  NOTE: ranktest MUST be installed before ivreg2/ivreghdfe
  The "struct ms_vcvorthog undefined" error is caused by missing ranktest.
==============================================================================*/

version 18
clear all
set more off

* ranktest must come first — ivreg2 and ivreghdfe depend on it
ssc install ranktest, replace
ssc install ivreg2, replace
ssc install reghdfe, replace
ssc install ftools, replace
ssc install ivreghdfe, replace
ssc install estout, replace
ssc install coefplot, replace

* Verify installation
which ranktest
which ivreg2
which ivreghdfe

di "IV packages installed successfully (dependency order: ranktest -> ivreg2 -> ivreghdfe)"
