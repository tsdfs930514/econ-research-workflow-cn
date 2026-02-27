/*==============================================================================
  Install required packages for DID analysis
==============================================================================*/

version 18
clear all
set more off

ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install boottest, replace
ssc install coefplot, replace
ssc install csdid, replace
ssc install drdid, replace
ssc install bacondecomp, replace

di "DID packages installed successfully"
