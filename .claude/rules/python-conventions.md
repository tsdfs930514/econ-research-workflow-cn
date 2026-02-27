---
paths:
  - "**/*.py"
---

# Python Code Conventions

These conventions apply to ALL Python scripts in this project.

## Header Template

Every .py file MUST start with this docstring header:

```python
"""
Project:      [Project Name]
Version:      [vN]
Script:       [filename.py]
Purpose:      [Brief description]
Author:       [Name]
Created:      [Date]
Dependencies: [packages]
"""
```

## Regression Analysis

Use `pyfixest` with `feols()` syntax for ALL regressions:

```python
import pyfixest as pf

# OLS with clustered SE
model = pf.feols("y ~ x1 + x2 | firmid + year", data=df, vcov={"CRV1": "firmid"})
model.summary()
```

Do NOT use `statsmodels` or `linearmodels` for standard regression tasks. `pyfixest` is the default to maintain syntax parity with Stata.

## Data Manipulation

- Use `pandas` for standard data manipulation.
- Use `polars` for large datasets where performance is critical.

```python
import pandas as pd

df = pd.read_stata("data/clean/panel_cleaned.dta")
```

## Output Alignment with Stata

Format regression output to match Stata `esttab` format:
- Same number of decimal places (3 for coefficients, 3 for standard errors)
- Same star notation: `*** p<0.01, ** p<0.05, * p<0.10`
- Standard errors in parentheses below coefficients

This ensures cross-validation between Stata and Python results is straightforward.

```python
# Export tables matching Stata format
model.to_latex("output/tables/results_python.tex", digits=3)
```

## File Paths

Use `pathlib.Path` for ALL file paths. Never use raw string concatenation for paths:

```python
from pathlib import Path

ROOT = Path(".")
DATA = ROOT / "data"
RAW = DATA / "raw"
CLEAN = DATA / "clean"
TEMP = DATA / "temp"
OUTPUT = ROOT / "output"
TABLES = OUTPUT / "tables"
FIGURES = OUTPUT / "figures"
LOGS = OUTPUT / "logs"
```

## Logging

Use Python's `logging` module. Save log output to `output/logs/`:

```python
import logging

logging.basicConfig(
    filename="output/logs/01_clean_data.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Script started")
```

## Random Seeds

Set random seeds for reproducibility before ANY randomization:

```python
import numpy as np
import random

np.random.seed(12345)
random.seed(12345)
```

If using PyTorch or TensorFlow, also set their seeds accordingly.

## Virtual Environment

- Document ALL dependencies in `requirements.txt`.
- Pin exact versions for reproducibility.
- Update `requirements.txt` whenever a new package is added.

```
pandas==2.1.0
pyfixest==0.18.0
polars==0.20.0
numpy==1.26.0
matplotlib==3.8.0
```
