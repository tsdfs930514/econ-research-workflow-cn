/*==============================================================================
  Install required packages for full pipeline
==============================================================================*/
version 18
clear all
set more off

ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install boottest, replace
ssc install coefplot, replace

di "Packages installed successfully"
