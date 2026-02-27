---
description: "在 Stata、Python pyfixest 和 R fixest 之间交叉验证回归结果"
user_invocable: true
---

# /cross-check — 回归结果交叉验证

当用户调用 `/cross-check` 时，按以下步骤执行：

## 步骤 1：收集信息

向用户询问：

1. **Stata .log 文件路径**（可选）— 包含回归输出的 Stata 日志文件路径
2. **Python 输出文件路径**（可选）— Python 输出或脚本路径
3. **R 输出文件路径**（可选）— R 输出或脚本路径（用于 APE 论文交叉验证）
4. **若均未提供**：要求用户提供回归设定和数据集，然后分别生成 Stata 和 Python 脚本以产生可比较的输出
5. **比较模式**：
   - `stata-python`（默认）— 比较 Stata reghdfe 与 Python pyfixest
   - `stata-r` — 比较 Stata reghdfe 与 R fixest（验证 APE 论文时使用）
   - `triple` — 三方比较：Stata vs Python vs R

## 步骤 2：解析 Stata 输出

读取 Stata .log 文件，从每个回归表格中提取以下内容：

- **系数**：各自变量的点估计
- **标准误**：系数下方括号内的数值
- **R 方**：R²、调整 R²、组内 R²（视情况而定）
- **观测值数量 (N)**
- **F 统计量**（如有报告）
- **固定效应**（如有）
- **聚类标准误**层级（如有）
- **因变量**名称
- **KP F 统计量**（IV 模型）
- **第一阶段 F 值**（IV 模型）

解析要点：
- Stata 回归输出遵循标准的表格格式
- 寻找变量名后跟系数和标准误的行
- R² 通常报告在回归表格底部
- N 以"Number of obs"形式报告
- 标准误可能标注为"Robust"、"Cluster"等

## 步骤 3：解析 Python 输出

如提供了 Python 脚本/输出，提取相同的统计量。如需生成新的 Python 脚本，使用 `pyfixest`：

```python
import pyfixest as pf
import pandas as pd

# 加载数据
df = pd.read_stata("<dataset path>")

# --- OLS / 面板固定效应 ---
model = pf.feols("<formula>", data=df, vcov=<vcov specification>)
print(model.summary())

# --- IV / 2SLS ---
# 语法: Y ~ exog | FEs | endog ~ instrument
model_iv = pf.feols("Y ~ controls | fe1 + fe2 | endog ~ instrument",
                     data=df, vcov={"CRV1": "cluster_var"})
print(model_iv.summary())

# --- DID 事件研究 ---
model_es = pf.feols("Y ~ i(rel_time, ref=-1) | unit + time",
                     data=df, vcov={"CRV1": "cluster_var"})
print(model_es.summary())

# 提取关键统计量
coefs = model.coef()
se = model.se()
r2 = model._r2 if hasattr(model, '_r2') else None
r2_within = model._r2_within if hasattr(model, '_r2_within') else None
n = model._N
```

## 步骤 4：解析 R 输出（APE 论文验证用）

如提供了 R 输出（来自使用 `fixest` 的 APE 论文），提取等价统计量：

```
# R fixest 输出格式:
# 系数表含 Estimate, Std. Error, t value, Pr(>|t|)
# 固定效应列于底部
# 显著性符号列于底部
```

R 到 Stata 的 `fixest` 映射关系：
| R fixest | Stata reghdfe | Python pyfixest |
|----------|---------------|-----------------|
| `feols(y ~ x \| fe1 + fe2, cluster = ~cl)` | `reghdfe y x, absorb(fe1 fe2) vce(cluster cl)` | `pf.feols("y ~ x \| fe1 + fe2", vcov={"CRV1": "cl"})` |
| `feols(y ~ x \| fe1 + fe2 \| endog ~ inst, cluster = ~cl)` | `ivreghdfe y (endog = inst), absorb(fe1 fe2) cluster(cl)` | `pf.feols("y ~ x \| fe1 + fe2 \| endog ~ inst", vcov={"CRV1": "cl"})` |
| `sunab(first_treat, time)` | `eventstudyinteract` / `csdid` | `pf.feols("y ~ sunab(g, t) \| ...")` |
| `etable()` | `esttab` | `pf.etable()` |

R 到 Stata 的 `lfe::felm()` 映射关系（金融/会计论文常用）：
| R lfe::felm | Stata reghdfe | Python pyfixest |
|-------------|---------------|-----------------|
| `felm(y ~ x \| fe1 + fe2 \| 0 \| cl1 + cl2)` | `reghdfe y x, absorb(fe1 fe2) vce(cluster cl1 cl2)` | `pf.feols("y ~ x \| fe1 + fe2", vcov={"CRV1": "cl1"})` （注意：pyfixest 仅支持单层聚类） |
| `felm(y ~ x \| fe1 + fe2 \| endog ~ inst \| cl)` | `ivreghdfe y (endog = inst), absorb(fe1 fe2) cluster(cl)` | 与 fixest IV 语法相同 |

**felm() 四部分公式**: `y ~ X | FEs | IVs | Clusters`
- 第 1 部分：`y ~ X` — 因变量和外生回归量
- 第 2 部分：`| fe1 + fe2 + fe3` — 吸收的固定效应（加法形式，非交互形式）
- 第 3 部分：`| endog ~ inst` 或 `| 0` — 工具变量（0 表示无）
- 第 4 部分：`| cluster1 + cluster2` — 聚类标准误变量

**多层聚类（lfe/multiwayvcov）**：
```r
library(lfe)
# 在 felm 中直接使用双层聚类:
model <- felm(y ~ x | fe1 + fe2 | 0 | cusip + date, data=df)

# 替代方案：lm + multiwayvcov:
library(multiwayvcov)
lm_model <- lm(y ~ x + factor(fe1), data=df)
vcov_2way <- cluster.vcov(lm_model, cbind(df$cusip, df$date))
```

**在 Python 中加载 .sas7bdat 数据**（适用于含 SAS 数据的复现包）：
```python
df = pd.read_sas("data/raw/file.sas7bdat", format="sas7bdat", encoding="latin-1")
```

## 步骤 5：比较结果

创建如下结构的比较表格：

### 双向比较（Stata vs Python）：

```
============================================================
交叉验证报告：Stata vs Python
============================================================
变量            | Stata      | Python     | 相对差异   | 状态
----------------|------------|------------|------------|-------
x1 (系数)       | 0.1234     | 0.1234     | 0.000%     | 通过
x1 (标准误)     | 0.0456     | 0.0457     | 0.022%     | 通过
x2 (系数)       | -0.5678    | -0.5679    | 0.002%     | 通过
x2 (标准误)     | 0.1234     | 0.1236     | 0.016%     | 通过
R 方            | 0.4567     | 0.4567     | 0.000      | 通过
N               | 10000      | 10000      | 0          | 通过
F 统计量        | 45.67      | 45.65      | 0.044%     | 通过
============================================================
```

### 三方比较（Stata vs Python vs R）：

```
============================================================
交叉验证报告：Stata vs Python vs R
============================================================
变量         | Stata      | Python     | R          | 最大差异 | 状态
-------------|------------|------------|------------|----------|-------
x1 (系数)    | 0.1234     | 0.1234     | 0.1234     | 0.000%   | 通过
x1 (标准误)  | 0.0456     | 0.0457     | 0.0456     | 0.022%   | 通过
...
============================================================
```

### 比较阈值

适用以下阈值判断通过/未通过：

| 统计量           | 阈值                       | 类型     |
|------------------|---------------------------|----------|
| 系数             | 相对差异 < 0.1%            | 相对     |
| 标准误           | 相对差异 < 0.5%            | 相对     |
| R 方             | 绝对差异 < 0.001           | 绝对     |
| N（观测值）       | 必须完全一致               | 精确     |
| F 统计量          | 相对差异 < 1%              | 相对     |
| KP F 统计量       | 相对差异 < 1%              | 相对     |

### 相对差异公式

```
rel_diff = |val_a - val_b| / max(|val_a|, |val_b|) * 100
```

对于非常接近零的值（< 1e-6），改用绝对差异。

## 步骤 6：通过代理诊断差异

如有任何比较未通过，使用 Task 工具调用 `cross-checker` 代理进行独立诊断。提供：
- Stata 日志文件路径及解析后的统计量
- Python 输出文件路径及解析后的统计量
- 步骤 5 中显示未通过项目的比较表格
- 两个平台使用的标准误类型、固定效应设定和聚类方式

代理将返回每项差异的详细诊断，包括具体原因和建议修复方案。将其结论整合至以下诊断指南中。

如有任何比较未通过，提供诊断指南：

### 差异的常见原因

1. **标准误类型不匹配**
   - Stata 默认：常规 OLS 标准误
   - Stata `robust`：HC1（Eicker-Huber-White）
   - Stata `cluster`：CRV1（聚类稳健方差，含小样本校正）
   - Python `pyfixest` 使用 `vcov="hetero"` 时：HC1
   - Python `pyfixest` 使用 `vcov={"CRV1": "var"}` 时：与 Stata `cluster` 一致
   - R `fixest` 使用 `cluster = ~var` 时：CRV1（与 Stata 一致）
   - **修复**：确保所有平台使用相同的标准误类型。

2. **自由度调整**
   - Stata 默认对聚类标准误使用小样本校正
   - pyfixest CRV1 同样使用小样本校正（应当一致）
   - R fixest 默认：使用小样本校正
   - 检查：G/(G-1) * (N-1)/(N-k) 调整，其中 G = 聚类数

3. **固定效应处理方式**
   - Stata `reghdfe`：基于 LSMR 的迭代去均值
   - pyfixest：与 `reghdfe` 相同的算法（迭代去均值）
   - R `fixest`：C++ 实现的去均值
   - **修复**：在 Stata 中使用 `reghdfe`，在 pyfixest 和 R fixest 中使用 `feols` 以保持一致性

4. **浮点精度**
   - 微小差异（< 0.01%）属于浮点运算的正常现象
   - 迭代算法的收敛标准不同

5. **样本差异**
   - 缺失值处理方式可能不同
   - Stata 会删除回归变量中含任何缺失值的观测
   - Python 可能需要对相关列显式调用 `dropna()`
   - R `fixest` 默认删除缺失值
   - **修复**：先检查 N。若 N 不同，说明样本不同。

6. **单例固定效应**
   - `reghdfe` 默认删除单例组
   - pyfixest 同样默认删除单例
   - R `fixest` 默认删除单例（`fixef.rm = "singleton"`）
   - 检查各平台的单例删除行为是否一致

7. **R 特有问题：`sunab()` vs Stata `csdid`**
   - R `fixest::sunab()` 实现 Sun-Abraham (2021) 交互加权估计量
   - 不能直接与 `csdid`（Callaway-Sant'Anna）比较
   - 应将 Sun-Abraham 与 Stata 的 `eventstudyinteract` 比较

### 建议诊断步骤

当差异超出阈值时：

1. 首先检查 N 是否一致。若不一致，排查样本构建过程。
2. 若 N 一致但标准误不同，检查标准误类型（稳健/聚类/常规）。
3. 若系数不同，检查变量定义和转换方式。
4. 尝试在两个平台上均使用常规（非稳健）标准误，以定位差异来源。
5. 检查可能被不同程序删除的共线变量。
6. 对于 IV：先比较第一阶段系数是否一致，再比较 2SLS。

## 步骤 7：生成报告

将交叉验证报告保存为文本文件，可选保存为 LaTeX 表格：

```
output/tables/tab_cross_check_<timestamp>.tex
output/logs/cross_check_report_<timestamp>.txt
```

输出总体结果：

```
交叉验证结果：通过（所有统计量均在容差范围内）
  Stata 日志:  output/logs/<stata_log>.log
  Python 日志: output/logs/<python_log>.log
  比较项目:    <N> 个系数, <N> 个标准误, R², N
```

或

```
交叉验证结果：未通过
  - x1 标准误：相对差异 2.3%（阈值：0.5%）
  - 可能原因：标准误类型不匹配（Stata 使用聚类标准误，Python 使用稳健标准误）
  - 建议修复：在 pyfixest 中将 vcov 改为 {"CRV1": "cluster_var"}
```

## 批量交叉验证模式

对整篇论文（多张表格）进行交叉验证时，使用批量模式：

```
交叉验证汇总
========================
表格 1（主要结果）:     通过（最大差异: 0.003%）
表格 2（第一阶段）:     通过（最大差异: 0.012%）
表格 3（稳健性）:       通过（最大差异: 0.008%）
表格 4（异质性）:       未通过（第 3 列标准误不匹配）
表格 A1（平衡性）:      通过（最大差异: 0.001%）
========================
总计: 4/5 通过, 1 未通过
```
