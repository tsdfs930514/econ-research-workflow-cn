---
description: "已发表复现包中高级 Stata 模式的参考文档"
user_invocable: false
---

# 来自已发表论文的高级 Stata 模式

> **参考文档** — 当遇到来自已发表论文的高级 Stata 模式时，Claude 应查阅本文件。这不是独立技能，不应被直接调用。

这些模式提取自已发表的复现包（Acemoglu et al. 2019 JPE 等），涵盖超越标准 FE/RE/GMM/IV 管道的高级估计技术。

---

## 面板数据模式

### 多维聚类

部分论文在两个维度上聚类标准误（如企业 + 时间）：
```stata
reghdfe Y X CONTROLS, absorb(UNIT TIME) vce(cluster CLUSTER1 CLUSTER2)
```

### 自定义 ado 程序

已发表的复现包通常定义自定义程序（如 `program define vareffects`、`program define helm` 用于 Helmert 变换）。这些程序必须在调用之前包含在 do 文件中。常见模式：
- **脉冲响应计算**：通过 `nlcom` 迭代计算累积效应（Acemoglu et al. 2019）
- **前向正交偏差**：自定义 Helmert 变换 `h_var = w * (var - forward_mean)`，其中 `w = sqrt(n/(n+1))`
- **最小距离估计量**：逐年 k-class 估计，配合 bootstrap 标准误（HHK 估计量）

### 多阶滞后的动态面板

使用 `L(1/N).var` 语法表示 N > 1 阶滞后时：
- 始终检验高阶滞后的联合显著性：`test l5.y l6.y l7.y l8.y`
- 比较 1、2、4、8 阶滞后模型以检验主系数的敏感性
- 报告长期效应：`shortrun / (1 - sum_of_lag_coefficients)`

### 通过 nlcom 链计算脉冲响应函数 (Acemoglu et al. 2019)

在含有滞后因变量的动态面板模型（`y_t = a*y_{t-1} + ... + b*X_t + e_t`）中，短期效应为 `b`，但 T 年后的累积效应通过滞后结构传播。已发表论文通过链式 `nlcom` 调用来计算。

**模式**：估计完成后，重命名系数，然后迭代计算累积效应：

```stata
* --- 在 4 阶滞后的 FE 或 GMM 估计之后 ---
* 首先：将短期系数和滞后系数作为命名标量发布
nlcom (shortrun: _b[dem]) ///
     (lag1: _b[L.y]) (lag2: _b[L2.y]) (lag3: _b[L3.y]) (lag4: _b[L4.y]), post

* 然后调用 vareffects 程序计算累积效应
vareffects
estimates store e3_add   // 存储：effect25, longrun, persistence
```

**`vareffects` 程序**（在 do 文件顶部定义）：
```stata
global limit = 25  // 计算转换后 N 年的效应

capture program drop vareffects
program define vareffects, eclass
* 递推关系：effect_j = sum_{k=1}^{4} effect_{j-k} * lag_k + shortrun
* effect_1 = shortrun
* effect_2 = effect_1 * lag1 + shortrun
* effect_3 = effect_2 * lag1 + effect_1 * lag2 + shortrun
* effect_4 = effect_3 * lag1 + effect_2 * lag2 + effect_1 * lag3 + shortrun
* effect_j (j>=5) = effect_{j-1}*lag1 + effect_{j-2}*lag2 + effect_{j-3}*lag3 + effect_{j-4}*lag4 + shortrun

quietly: nlcom (effect1: _b[shortrun]) ///
      (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

quietly: nlcom (effect2: _b[effect1]*_b[lag1]+_b[shortrun]) ///
      (effect1: _b[effect1]) (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

quietly: nlcom (effect3: _b[effect2]*_b[lag1]+_b[effect1]*_b[lag2]+_b[shortrun]) ///
      (effect2: _b[effect2]) (effect1: _b[effect1]) (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

quietly: nlcom (effect4: _b[effect3]*_b[lag1]+_b[effect2]*_b[lag2]+_b[effect1]*_b[lag3]+_b[shortrun]) ///
      (effect3: _b[effect3]) (effect2: _b[effect2]) (effect1: _b[effect1]) ///
      (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

forvalues j=5(1)$limit {
    local j1=`j'-1
    local j2=`j'-2
    local j3=`j'-3
    local j4=`j'-4
    quietly: nlcom ///
        (effect`j': _b[effect`j1']*_b[lag1]+_b[effect`j2']*_b[lag2]+_b[effect`j3']*_b[lag3]+_b[effect`j4']*_b[lag4]+_b[shortrun]) ///
        (effect`j1': _b[effect`j1']) (effect`j2': _b[effect`j2']) ///
        (effect`j3': _b[effect`j3']) (shortrun: _b[shortrun]) ///
        (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post
}

* 最后：计算长期效应和持续性
quietly: nlcom (effect$limit: _b[effect$limit]) ///
      (longrun: _b[shortrun]/(1-_b[lag1]-_b[lag2]-_b[lag3]-_b[lag4])) ///
      (shortrun: _b[shortrun]) ///
      (persistence: _b[lag1]+_b[lag2]+_b[lag3]+_b[lag4]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post
ereturn display
end
```

**`vareffects` 的关键输出**：`effect25`（25 年累积效应）、`longrun`（稳态效应 = shortrun / (1 - persistence)）、`persistence`（滞后系数之和）。

**跨估计量使用**：同一个 `vareffects` 程序在 FE、GMM、IV 和 HHK 估计之后调用——为每种方法分别存储 `_add` 估计结果：
```stata
* FE
xtreg y l(1/4).y dem yy*, fe vce(cluster wbcode2)
estimates store e3
nlcom (shortrun: _b[dem]) (lag1: _b[L.y]) (lag2: _b[L2.y]) (lag3: _b[L3.y]) (lag4: _b[L4.y]), post
vareffects
estimates store e3_add

* GMM
xtabond2 y l(1/4).y dem yy*, gmmstyle(y, laglimits(2 .)) gmmstyle(dem, laglimits(1 .)) ///
    ivstyle(yy*, p) noleveleq robust nodiffsargan
estimates store e3gmm
nlcom (shortrun: _b[dem]) (lag1: _b[L.y]) (lag2: _b[L2.y]) (lag3: _b[L3.y]) (lag4: _b[L4.y]), post
vareffects
estimates store e3gmm_add
```

**对于 8 阶滞后模型**：定义单独的 `vareffects8` 程序，将递推扩展到 8 阶滞后：`effect_j = sum_{k=1}^{8} effect_{j-k} * lag_k + shortrun`。结构相同，但追踪 8 个滞后系数。

### Helmert / 前向正交偏差 — 完整实现

Helmert 变换替代一阶差分来消除固定效应。与 `y_t - y_{t-1}` 不同，它计算 `w * (y_t - forward_mean_t)`，其中 `forward_mean_t` 是该个体所有未来观测值的均值，`w = sqrt(n/(n+1))`。这保持了变换后误差项的正交性（对 GMM 有效性很重要）。

**`xtabond2` 内置选项**：使用 `orthogonal` 选项：
```stata
xtabond2 y l(1/4).y dem yy*, ///
    gmmstyle(y, laglimits(2 .)) gmmstyle(dem, laglimits(1 .)) ///
    ivstyle(yy*, p) noleveleq robust orthogonal
```

**自定义 `helm` 程序**（当需要显式的 Helmert 变换数据时，如用于 HHK 估计量）：
```stata
capture program drop helm
program define helm
* 对变量列表进行 Helmert 变换
* 要求数据集中有 id 和 year 变量
* 用法：helm var1 var2 var3 ...
* 输出：h_var1, h_var2, h_var3 ...
qui while "`1'"~="" {
    gsort id -year                      // 在个体内按年份降序排列
    tempvar one sum n m w
    gen `one' = 1 if `1' ~= .          // 非缺失值指示变量
    qui by id: gen `sum' = sum(`1') - `1'  // 排除当前值的累计和
    qui by id: gen `n' = sum(`one') - 1    // 未来观测值的计数
    replace `n' = . if `n' <= 0         // 最后一个观测没有未来值
    gen `m' = `sum' / `n'               // 前向均值
    gen `w' = sqrt(`n' / (`n' + 1))     // Helmert 权重
    capture gen h_`1' = `w' * (`1' - `m')  // 变换后的变量
    sort id year
    mac shift                           // 移到列表中的下一个变量
}
end
```

**在 HHK 估计量中的使用**：`helm` 程序应用于残差化后的变量（已剔除外生协变量的影响）：
```stata
* 剔除协变量影响，然后进行 Helmert 变换
quietly: gen id = panel_id
reg y_var covariates if tsample == 1
predict y_res if tsample == 1, resid
helm y_res
rename h_y_res h_y
```

### HHK 最小距离估计量 (Hahn-Hausman-Kuersteiner)

HHK 估计量是一种偏差纠正的面板估计量，对 Helmert 变换后的数据逐年进行 k-class IV 回归，然后通过逆方差加权汇总结果。它解决了 Nickell 偏差问题，无需 GMM 式的矩条件。

**算法**：
1. 从所有变量（包括工具变量）中剔除外生协变量
2. 对残差化变量进行 Helmert 变换
3. 构造 GMM 式的滞后工具变量（缺失值替换为 0）
4. 对每个年份 `t`：
   a. 对该年的 Helmert 变换数据运行 `ivreg2`
   b. 计算 k-class 参数：`lambda = 1 + e(sargandf) / e(N)`
   c. 使用 `k(lambda)` 选项重新运行 `ivreg2`
   d. 提取系数 `b` 和方差 `V`
   e. 累加：`Num += N_t * inv(V) * b'`，`Den += N_t * inv(V)`
5. 汇总：`b_HHK = inv(Den) * Num`，`V_HHK = inv(Den) * Num2 * inv(Den)`
6. 通过 `ereturn post b V` 发布结果

### 基于分位数中心化的交互异质性

检验处理效应是否随某一特征（如初始 GDP）变化时，以参考分位数为中心：

```stata
* 以初始 GDP 的第 25 百分位数为中心
summarize gdp1960 if dem == 0, detail
gen inter = dem * (gdp1960 - r(p25))

* 含交互异质性的 IV（两个均为内生变量）
xtivreg2 y l(1/4).y ///
    (dem inter = l(1/4).demreg l(1/4).intereg) yy*, ///
    fe cluster(wbcode2) r partial(yy*)
```

**解释**：`dem` 的系数是在 GDP 第 25 百分位处的效应。`inter` 的系数是初始 GDP 每增加一个单位对处理效应的边际影响。以分位数（而非 0 或均值）为中心，使 `dem` 系数具有自然的经济学解释。

### 自定义估计量的矩阵运算

高级 Stata 程序直接操纵矩阵进行自定义汇总：

```stata
* 初始化累加器矩阵
matrix def Num1 = J(k, 1, 0)     // k*1 零向量（b 的分子）
matrix def Num2 = J(k, k, 0)     // k*k 零矩阵（V 的分子）
matrix def Den1 = J(k, k, 0)     // k*k 零矩阵（分母）

* 逐年累加
matrix b = e(b)
matrix V = e(V)
matrix Num1 = Num1 + N_t * inv(V) * b'
matrix Den1 = Den1 + N_t * inv(V)

* 汇总结果
matrix est = inv(Den1) * Num1
matrix var = inv(Den1) * Num2 * inv(Den1)
matrix b = est'
matrix V = var

* 命名并发布
mat colnames b = dem L.y L2.y L3.y L4.y
mat colnames V = dem L.y L2.y L3.y L4.y
mat rownames V = dem L.y L2.y L3.y L4.y
ereturn post b V, obs(N_total) depname("Dep var") esample(sample_indicator)
```

此模式允许任何自定义估计量"看起来像"标准 Stata 估计命令，兼容 `eststo`、`esttab`、`nlcom` 等。

---

## IV 特定模式

### 使用 xtivreg2 的面板 IV

当 `ivreghdfe` 不可用或需要面板特定 IV 功能时，使用 `xtivreg2`：
```stata
* 面板 IV，内置 FE（无需生成虚拟变量）
xtivreg2 Y CONTROLS (ENDOG = INSTRUMENTS) YEAR_DUMMIES, ///
    fe cluster(UNIT_VAR) r partial(YEAR_DUMMIES)
```
与 `ivreghdfe` 的主要区别：
- `xtivreg2` 有原生的 `fe` 选项用于面板固定效应
- 使用 `partial()` 剔除高维控制变量（如年份虚拟变量）以提高速度
- 直接报告 `widstat`（KP F）、`jp`（Hansen J p 值）
- 安装方式：`ssc install xtivreg2`

### absorb() 中的交互固定效应

对于含交互固定效应的模型（如年份 x 市辖区）：
```stata
* ivreghdfe 语法
ivreghdfe Y CONTROLS (ENDOG = IV), absorb(FE1 FE2#FE3) cluster(CLUSTER)
* 示例：absorb(market_c year#mun_c) 表示市场固定效应 + 年份*市辖区固定效应

* reghdfe 语法（相同模式）
reghdfe Y CONTROLS, absorb(FE1 i.FE2#i.FE3) vce(cluster CLUSTER)
```

### Shift-Share / Bartik IV

当工具变量是 shift-share（Bartik）构造时：
1. 报告有效 F 统计量（Montiel Olea-Pflueger）而非仅 KP F
2. 考虑 Adao, Kolesar, Morales (2019) 暴露稳健标准误：
   ```stata
   * 在行业 + 地区两个维度上聚类（适用于 shift-share 标准误）
   reghdfe Y TREAT CONTROLS, absorb(FE) vce(cluster SECTOR REGION)
   ```
3. 报告 Rotemberg 权重分解，评估哪些行业/冲击驱动了识别

### savefirst 选项

存储并检查第一阶段估计：
```stata
* ivreghdfe
ivreghdfe Y CONTROLS (ENDOG = IV), absorb(FE) cluster(CLUSTER) first savefirst
* 通过以下命令访问已保存的估计：estimates restore _ivreghdfe_ENDOG

* ivreg2
ivreg2 Y CONTROLS (ENDOG = IV), cluster(CLUSTER) first ffirst savefirst
```

### 多个内生变量

当对多个内生变量进行工具变量估计时（如民主 + 空间滞后）：
```stata
xtivreg2 Y CONTROLS (ENDOG1 ENDOG2 = IV1 IV2 IV3 IV4), ///
    fe cluster(UNIT) r partial(YEAR_DUMMIES)
```
要求工具变量数量 >= 内生变量数量。

### 带交互项的多个内生变量

当处理变量及其与调节变量的交互项均为内生时，使用对应的交互工具变量进行估计：
```stata
* 构造工具变量交互项（使用相同的调节变量）
gen inter = dem * (gdp1960 - reference_value)
gen intereg = demreg * (gdp1960 - reference_value)

* IV：对 (dem, inter) 使用 (demreg, intereg) 的滞后作为工具变量
xtivreg2 y l(1/4).y ///
    (dem inter = l(1/4).demreg l(1/4).intereg) yy*, ///
    fe cluster(wbcode2) r partial(yy*)
```

对于作为额外内生变量的空间滞后：
```stata
* 两个内生变量：民主 + GDP 的空间滞后
xtivreg2 y l(1/4).y (dem y_w = l(1/4).instrument l(1/4).y_w) yy*, ///
    fe cluster(wbcode2) r partial(yy*)

* 四个内生变量：民主 + GDP 和民主的空间滞后
xtivreg2 y l(1/4).y ///
    (dem l(0/4).y_w dem_w = l(1/4).instrument l(1/5).y_w l(1/4).dem_w) yy*, ///
    fe cluster(wbcode2) r partial(yy*)
```

---

## 共享模式（面板 + IV）

### 通过 ivreg2 的 k-class 估计

k-class 估计量嵌套了 OLS (k=0)、2SLS (k=1)、LIML (k=lambda_min) 和偏差纠正的 Fuller 估计量。HHK 最小距离估计量使用 `k = 1 + (degree_of_overid / N)`：

```stata
* 第一遍：获取过度识别的自由度
ivreg2 h_y (h_x = instruments) if year == 2000, noid noconstant
local lambda = 1 + e(sargandf) / e(N)

* 第二遍：k-class 估计
ivreg2 h_y (h_x = instruments) if year == 2000, ///
    k(`lambda') nocollin coviv noid noconstant
```

**关键 ivreg2 k-class 选项**：
- `k(scalar)`：k 参数值
- `nocollin`：跳过共线性检查（提高速度）
- `coviv`：使用 IV 式方差估计量
- `noid`：抑制欠识别检验
- `noconstant`：省略常数项（如当数据已进行 Helmert 变换时）

### 通过 spmat 构造空间滞后

构造空间滞后变量作为工具变量或控制变量：
```stata
cap ssc install spmat
cap ssc install spmack

* 构造逆距离空间权重矩阵（逐年）
forvalues j = 1960(1)2010 {
    preserve
    keep if year == `j'
    keep if cen_lon != . & cen_lat != . & y != . & dem != .
    keep wbcode2 cen_lon cen_lat y dem year
    sort wbcode2

    * 根据坐标创建空间权重矩阵
    spmat idistance dmat cen_lon cen_lat, id(wbcode2) dfunction(dhaversine) norm(row) replace

    * 计算空间滞后
    spmat lag y_w dmat y        // GDP 的空间滞后
    spmat lag dem_w dmat dem    // 民主的空间滞后

    keep y_w dem_w wbcode2 year
    tempfile m
    save `m', replace
    restore
    merge 1:1 wbcode2 year using `m', update
    drop _m
}
```

### 面板结构的 Bootstrap 推断

对于解析标准误较复杂的 IV 或自定义估计量，使用聚类 bootstrap：

```stata
* 生成 bootstrap 面板 ID 变量
gen newcl = wbcode2
tsset newcl year

* 对整个估计过程进行 bootstrap
bootstrap _b, seed(12345) reps(100) cluster(wbcode2) idcluster(newcl): ///
    custom_estimator y (dem L1.y L2.y L3.y L4.y) (y dem) (demreg) (yy*)

estimates store e_boot
```

**面板数据 bootstrap 关键选项**：
- `cluster(panelvar)`：重抽样整个面板（保持个体内时间序列）
- `idcluster(newvar)`：面板 bootstrap 必需——为每次 bootstrap 抽样创建新的连续 ID（因为有放回抽样会产生重复的面板 ID）
- `reps(N)`：探索阶段用 100，发表质量用 500-1000
- `seed(N)`：始终设定以确保可重复性

**HHK 特定 bootstrap**：
```stata
gen newcl = wbcode2
tsset newcl year

bootstrap _b, seed(12345) reps(100) cluster(wbcode2) idcluster(newcl): ///
    hhkBS y (dem L1.y L2.y L3.y L4.y) (y dem) (demreg) (yy*), ///
    ydeep(1960) ystart(1964) yfinal(2009) truncate(4)
estimates store e3md
```

**`hhkBS` 程序参数**（括号分组）：
```
hhkBS yvar (sequentially_exogenous) (gmm_instruments) (gmm_truncated) (exogenous_covariates), options
```
- 第 1 组 `(dem L1.y ... L4.y)`：序贯外生回归变量（处理变量 + 滞后因变量）
- 第 2 组 `(y dem)`：用作 GMM 式工具变量的变量（滞后 2 期以上的水平值）
- 第 3 组 `(demreg)`：截断的 GMM 工具变量（最多滞后 `truncate` 期）
- 第 4 组 `(yy*)`：外生协变量（在变换前剔除）

Bootstrap 之后，使用 `nlcom` 从 bootstrap 系数导出脉冲响应函数（标准误将通过 delta 方法正确传播）。

### 一致样本模式：`gen samp = e(sample)`

通过保存估计样本确保不同规范使用一致的样本：

```stata
* 规范 1 — 保存其样本指示变量
xtivreg2 y l(1/4).y (dem = l.instrument) yy*, fe cluster(wbcode2) r partial(yy*)
gen samp1 = e(sample)

* 规范 2 — 保存其样本
xtivreg2 y l(1/4).y (dem = l(1/4).instrument) yy*, fe cluster(wbcode2) r partial(yy*)
gen samp2 = e(sample)

* 规范 1 的第一阶段 — 限制在相同的样本上
xtreg dem l(1/4).y l.instrument yy* if samp1 == 1, fe cluster(wbcode2)
```

当不同的工具变量集产生不同的估计样本时（不同的滞后导致不同的缺失模式），这一点至关重要。始终在用于 2SLS 的精确样本上报告第一阶段结果。当样本可能不同时，在每个规范后使用 `gen sampN = e(sample)`。

---

## 通过局部宏捕获 SDID 结果 (Issue #24)

`sdid` 命令 (Clarke et al. 2023) 将结果存储在 `e(ATT)` 和 `e(se)` 中，但这些与 `ereturn post` + `estimates store` 不兼容。`ereturn post b V` 模式会清除 e-class 环境，导致 r(301) 错误。替代方案是在 `sdid` 成功后立即将结果捕获到局部宏中：

```stata
* 初始化结果局部宏
local sdid_att = .
local sdid_se  = .
local sdid_ok  = 0

* 运行 SDID，使用 bootstrap VCE（jackknife 在交错处理下会失败，Issue #25）
cap noisily sdid Y unit time treat, vce(bootstrap) method(sdid) seed(12345) reps(200)

* 成功运行后立即捕获结果（在任何 ereturn/estimates 命令之前）
if _rc == 0 {
    local sdid_att = e(ATT)
    local sdid_se  = e(se)
    local sdid_N   = e(N)
    local sdid_ok  = 1
}

* 对 DID 和 SC 方法重复
cap noisily sdid Y unit time treat, vce(bootstrap) method(did) seed(12345) reps(200)
if _rc == 0 {
    local did_att = e(ATT)
    local did_se  = e(se)
    local did_ok  = 1
}

* 从局部宏（而非 estimates store）构建 LaTeX 表格
file open _tab using "output/tables/tab_sdid.tex", write replace
file write _tab "\begin{tabular}{lccc}" _n
file write _tab " & SDID & DID & SC \\\\" _n
if `sdid_ok' {
    file write _tab "ATT & " %9.4f (`sdid_att') " & ... \\\\" _n
}
file close _tab
```

**SDID 关键规则：**
1. 始终在 `sdid` 调用外层使用 `cap noisily`
2. 在任何其他命令之前将 `e(ATT)` 和 `e(se)` 捕获到局部宏中
3. 在 `sdid` 之后永远不要使用 `ereturn post` 或 `estimates store`
4. 通过 `file write` 使用局部宏构建表格
5. 默认使用 `vce(bootstrap)`；`vce(jackknife)` 要求每个处理期至少有 2 个处理单位
