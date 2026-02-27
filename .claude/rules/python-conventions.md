---
paths:
  - "**/*.py"
---

# Python 代码规范 (Python Code Conventions)

以下规范适用于本项目中的所有 Python 脚本。

## 文件头模板

每个 .py 文件**必须**以如下 docstring 文件头开始：

```python
"""
Project:      [Project Name]
Version:      [vN]
Script:       [filename.py]
Purpose:      [简要说明]
Author:       [Name]
Created:      [Date]
Dependencies: [packages]
"""
```

## 回归分析

所有回归**必须**使用 `pyfixest` 的 `feols()` 语法：

```python
import pyfixest as pf

# 带聚类标准误的 OLS
model = pf.feols("y ~ x1 + x2 | firmid + year", data=df, vcov={"CRV1": "firmid"})
model.summary()
```

**不得**使用 `statsmodels` 或 `linearmodels` 进行标准回归任务。`pyfixest` 是默认选择，以保持与 Stata 的语法一致性。

## 数据操作

- 使用 `pandas` 进行标准数据操作。
- 当性能要求较高时，对大型数据集使用 `polars`。

```python
import pandas as pd

df = pd.read_stata("data/clean/panel_cleaned.dta")
```

## 输出与 Stata 对齐

回归输出格式须与 Stata `esttab` 格式对齐：
- 系数和标准误的小数位数一致（默认各 3 位）
- 相同的星号标注：`*** p<0.01, ** p<0.05, * p<0.10`
- 标准误以括号形式显示在系数下方

这确保了 Stata 与 Python 结果之间的交叉验证简单直接。

```python
# 导出与 Stata 格式匹配的表格
model.to_latex("output/tables/results_python.tex", digits=3)
```

## 文件路径

所有文件路径**必须**使用 `pathlib.Path`。禁止使用原始字符串拼接：

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

## 日志记录

使用 Python 的 `logging` 模块。日志输出保存到 `output/logs/`：

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

## 随机种子

在任何随机化操作之前**必须**设置随机种子以确保可复现性：

```python
import numpy as np
import random

np.random.seed(12345)
random.seed(12345)
```

如使用 PyTorch 或 TensorFlow，也需相应设置其随机种子。

## 虚拟环境

- 所有依赖项记录在 `requirements.txt` 中。
- 锁定精确版本以确保可复现性。
- 每添加新包时更新 `requirements.txt`。

```
pandas==2.1.0
pyfixest==0.18.0
polars==0.20.0
numpy==1.26.0
matplotlib==3.8.0
```
