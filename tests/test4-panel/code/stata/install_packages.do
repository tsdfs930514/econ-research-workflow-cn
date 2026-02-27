/*==============================================================================
  Install required packages for Panel analysis
==============================================================================*/

version 18
clear all
set more off

cap ssc install reghdfe, replace
cap ssc install ftools, replace
cap ssc install estout, replace
cap ssc install xtabond2, replace
cap ssc install xtserial, replace
cap ssc install xtscc, replace
cap ssc install coefplot, replace
cap ssc install xtcsd, replace
cap ssc install xttest3, replace

di "Panel packages installed successfully"
