---
paths:
  - "**/code/**"
  - "**/output/**"
---

# 计量经济学标准 (Econometrics Standards)

以下标准约束本项目中的所有实证分析。每一项回归、检验和输出都必须遵守。

---

## 双重差分法 (DID) 标准

1. **平行趋势假设 (Parallel Trends)**: 估计**之前**必须检验。绘制处理组和控制组的处理前趋势图。
2. **事件研究图 (Event Study)**: 报告包含处理前系数的事件研究。所有处理前系数应统计上不显著且接近零。
3. **联合平行趋势检验 (Joint Pre-trend Test)**: 对所有处理前先行项进行正式联合 F 检验。在图注中报告 F 统计量和 p 值。
4. **异质性处理效应 (Heterogeneous Treatment Effects)**: 使用稳健 DID 估计量检验：
   - `csdid`（Callaway & Sant'Anna, 2021）——组-时间平均处理效应
   - `did_multiplegt`（de Chaisemartin & D'Haultfoeuille, 2020）——异质性稳健估计
   - `did_imputation`（Borusyak, Jaravel & Spiess, 2024）——基于插补的估计
   - `eventstudyinteract`（Sun & Abraham, 2021）——交互加权事件研究
5. **TWFE 与稳健估计量**: 同时报告传统 TWFE 和至少一种稳健 DID 估计量。讨论差异。
6. **Goodman-Bacon 分解**: 运行 `bacondecomp` 诊断异质性处理效应导致的 TWFE 偏误。
7. **渐进处理 (Staggered Adoption)**: 若处理时间跨单位有差异，必须明确讨论渐进处理问题，并使用适当的估计量（不得仅依赖 TWFE）。
8. **HonestDiD 敏感性分析**: 应用 Rambachan-Roth 敏感性分析，检验平行趋势违反可能对结果产生多大影响。

---

## 合成双重差分法 (SDID) 标准

1. **适用场景**: 当处理单位较少、控制单位较多且平行趋势存疑时优先使用。
2. **比较表格**: 在比较表中同时报告 SDID、传统 DiD 和纯合成控制法的结果。
3. **单位权重**: 分析权重是否集中在少数控制单位上（脆弱性问题）还是分散分布。
4. **时间权重**: 检查时间权重是否强调接近处理时点的处理前期（预期行为）。
5. **推断**: 报告 jackknife 标准误、bootstrap 标准误和安慰剂 p 值。如结果不一致须说明。
6. **逐一剔除分析 (Leave-one-unit-out)**: 检查剔除单个控制单位后结果的敏感性。

---

## 工具变量 / 两阶段最小二乘法 (IV/2SLS) 标准

1. **第一阶段 (First Stage)**: 在专门的表格中单独报告第一阶段回归结果。
2. **第一阶段 F 统计量**: 必须超过 10（经验法则）。
3. **Lee et al. (2022) tF**: 使用 tF 临界值检验弱工具变量时，优先要求 F > 23。
4. **Kleibergen-Paap rk Wald F 统计量**: 在非 i.i.d. 误差（异方差或聚类）情况下报告。
5. **偏 R 方 (Partial R-squared)**: 在第一阶段表格中报告排除工具变量的偏 R 方。
6. **过度识别检验**: 当工具变量数量超过内生变量数量时报告 Hansen J 统计量。讨论拒绝的含义。
7. **排除性约束 (Exclusion Restriction)**: 对工具变量有效性进行论述。解释为何工具变量**仅通过**内生变量影响结果。
8. **弱工具变量稳健推断**: 当 F 统计量处于边界值（10-23）时，考虑使用 Anderson-Rubin (AR) 检验进行对弱工具变量稳健的推断。
9. **LIML 比较**: 同时报告 LIML 估计值和 2SLS。两者差异大表明弱工具变量问题。
10. **逐一剔除分析 (LOSO)**: 检查是否有单个聚类驱动结果。
11. **Oster 界 (Oster Bounds)**: 报告 Oster (2019) delta 以评估不可观测变量选择偏误。

---

## 断点回归设计 (RDD) 标准

1. **最优带宽 (Optimal Bandwidth)**: 报告 MSE 最优（`bwselect(mserd)`）和 CER 最优（`bwselect(cerrd)`）带宽。
2. **带宽敏感性**: 至少展示 6 种带宽下的结果：最优带宽的 0.5x、0.75x、1x、1.25x、1.5x 和 2x。
3. **多项式阶数**: 检验 p=1、2 和 3。局部线性（p=1）为默认。报告对高阶多项式的敏感性。
4. **核函数敏感性**: 报告三角核（默认）、均匀核和 Epanechnikov 核的结果。
5. **操纵检验 (Manipulation Test)**: Cattaneo-Jansson-Ma (CJM, 2020) 密度检验，检测断点处的样本操纵。报告 p 值并讨论含义。
6. **安慰剂断点检验**: 在不应存在效应的替代（虚假）断点处检验（如第 25 和第 75 百分位）。
7. **协变量平衡**: 使用 `rdrobust` 逐一检验预定协变量在断点处的平衡性。
8. **RD 图**: 使用 `rdplot` 提供分箱散点图，断点两侧拟合多项式。
9. **甜甜圈 RDD (Donut Hole RDD)**: 剔除非常接近断点的观测值（如 ±0.5、±1、±2 单位），检验操纵问题。
10. **含/不含协变量**: 同时报告含协变量和不含协变量的主要规格，以评估精确度。

---

## 面板数据标准 (Panel Data Standards)

1. **Hausman 检验**: 进行 Hausman 检验以论证 FE 与 RE 的选择。报告检验统计量和 p 值。
2. **序列相关 (Serial Correlation)**: 使用 Wooldridge (2002) 面板数据自相关检验（Stata 中的 `xtserial`）。
3. **截面相关 (Cross-sectional Dependence)**: 当 T 相对于 N 较大时，使用 Pesaran (2004) CD 检验。若 CD 检验拒绝原假设，考虑使用 Driscoll-Kraay 标准误。
4. **组内 R 方 (Within R-squared)**: FE 模型报告组内 R 方（非总体 R 方）。
5. **动态面板**: 若包含因变量滞后项，考虑系统 GMM（Blundell-Bond）或差分 GMM（Arellano-Bond）。报告 AR(1)、AR(2) 检验和 Hansen J 检验。
6. **聚类标准误 (Clustering)**: 在适当层级（企业、行业、省份）聚类标准误。论证聚类层级的选择。如有疑问，在更高层级聚类。
7. **Wild Cluster Bootstrap**: 当聚类数 < 50 时使用（Roodman et al.）。

---

## 通用标准（适用于所有回归）

### 标准误
- 默认使用聚类标准误。始终指定聚类变量。
- 在表格脚注中报告聚类数量。
- 仅在聚类不适用的极少数情况下使用异方差稳健标准误。

### 多重假设检验 (Multiple Hypothesis Testing)
- 当检验多个假设（如多个结果变量）时，考虑 Bonferroni 或 FDR 校正。
- 应用多重检验校正时，同时报告未校正和校正后的 p 值。

### 系数格式
- 系数：4 位小数（TOP5 因果推断标准）
- 标准误：4 位小数，括号内显示于系数下方
- 星号：`*** p<0.01`, `** p<0.05`, `* p<0.10`

### 必报表格统计量
每张回归表格**必须**报告：
- N（观测值数量）
- R 方（FE 模型报告组内 R 方）
- 聚类数或组数
- 因变量均值（表注或脚注中）
- 第一阶段 F 统计量（IV 表格）
- 控制变量指示行
- 固定效应指示行

### Stata 示例
```stata
esttab m1 m2 m3 using "output/tables/main_results.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    scalars("N_clust Number of clusters" "r2_within Within R²") ///
    addnotes("Standard errors clustered at firm level in parentheses." ///
             "Mean of dep. var: X.XXXX." ///
             "*** p<0.01, ** p<0.05, * p<0.10.") ///
    label booktabs replace
```

---

## 各方法所需安装包

### DID
```stata
ssc install reghdfe
ssc install csdid
ssc install did_multiplegt
ssc install did_imputation
ssc install bacondecomp
ssc install eventstudyinteract
ssc install honestdid
ssc install boottest
```

### SDID
```stata
ssc install sdid
ssc install reghdfe
```

### IV
```stata
ssc install reghdfe
ssc install ivreghdfe
ssc install ivreg2
ssc install ranktest
ssc install weakiv
ssc install boottest
ssc install psacalc
```

### RDD
```stata
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace
net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace
net install rdlocrand, from(https://raw.githubusercontent.com/rdpackages/rdlocrand/master/stata) replace
net install rdmulti, from(https://raw.githubusercontent.com/rdpackages/rdmulti/master/stata) replace
```

### 面板数据
```stata
ssc install reghdfe
ssc install xtabond2
ssc install xtscc
ssc install xtserial
```
