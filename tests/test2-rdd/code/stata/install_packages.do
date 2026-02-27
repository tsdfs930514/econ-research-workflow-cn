/*==============================================================================
  Install required packages for RDD analysis
==============================================================================*/

version 18
clear all
set more off

* Install rdrobust suite
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace

* Install rddensity
net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace

* Install rdlocrand
net install rdlocrand, from(https://raw.githubusercontent.com/rdpackages/rdlocrand/master/stata) replace

di "Packages installed successfully"
