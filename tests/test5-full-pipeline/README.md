# Test 5: Full Pipeline Integration Test

Tests the complete workflow: data generation -> cleaning -> descriptive stats -> DID analysis -> table export -> cross-validation.

## How to Run

1. `python generate_data.py` (creates raw data)
2. Open Stata, run `v1/code/stata/master.do`
3. `python v1/code/python/01_cross_validate.py`

## Expected Results

- TWFE treatment coefficient near -50
- Pre-trend F-test insignificant
- Stata-Python coefficient match < 0.1%
