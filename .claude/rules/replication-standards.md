---
paths:
  - "**/REPLICATION.md"
  - "**/master.do"
  - "**/docs/**"
---

# 复现标准 (Replication Standards)

遵循 AEA 数据编辑器指南和 TOP5 期刊最佳实践的可复现研究标准。

---

## 数据溯源 (Data Provenance)

### 数据可用性声明

每个复现包必须包含清晰的声明：
- 哪些数据是公开可用的及其获取方式
- 哪些数据有访问限制及其申请方式
- 哪些数据是保密的、无法共享

### 数据文档

对 `data/raw/` 中的每个原始数据文件，在 REPLICATION.md 中记录：

| 要素 | 说明 |
|---------|-------------|
| **文件名** | `data/raw/` 中的确切文件名 |
| **来源** | 原始数据提供者（如 NBER、Census、企业网站） |
| **获取日期** | 文件的下载时间 |
| **DOI/URL** | 持久性标识符或直接下载链接 |
| **许可证** | 使用限制（公共领域、仅限学术使用等） |
| **MD5/SHA256** | 文件哈希值，用于验证完整性 |
| **大小** | 文件大小（用于规划存储） |

### 数据处理文档

创建 `data_dictionary.md`，记录：
- 变量名称和说明
- 计量单位
- 编码方案（如 1=男、2=女）
- 缺失值编码
- 已知的数据质量问题

---

## 代码组织

### 目录结构

```
vN/
├── code/
│   ├── stata/
│   │   ├── master.do           # 入口脚本——运行全部程序
│   │   ├── 01_clean_data.do    # 数据准备
│   │   ├── 02_desc_stats.do    # 描述性统计
│   │   ├── 03_main_analysis.do # 主要结果
│   │   ├── 04_robustness.do    # 稳健性检验
│   │   └── 05_tables_figures.do # 输出生成
│   └── python/
│       └── cross_validation.py  # 验证 Stata 结果
├── data/
│   ├── raw/                    # 原始数据（只读）
│   └── clean/                  # 处理后数据
├── output/
│   ├── tables/                 # LaTeX 表格
│   ├── figures/                # PDF 图表
│   └── logs/                   # 执行日志
└── REPLICATION.md              # 复现说明
```

### 主控脚本模式 (Master Script Pattern)

`master.do` 文件必须：
1. 通过全局宏设置所有路径
2. 如不存在则创建输出目录
3. 安装所需包（注释形式，附安装说明）
4. 按正确顺序运行所有脚本
5. 验证预期输出已生成

详见 `init-project.md` 的完整模板。

### 脚本编号

使用数字前缀表示执行顺序：
- `01_` — 数据清洗与准备
- `02_` — 描述性统计
- `03_` — 主要分析
- `04_` — 稳健性检验
- `05_` — 表格与图表导出
- `06_` — 交叉验证（Python）

---

## 软件环境

### Stata 要求

在 REPLICATION.md 中记录：
- Stata 版本（如 "Stata 18/MP"）
- 所需安装包及安装命令
- 大致运行时间

```stata
* 所需 Stata 安装包：
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
* ...（完整列表见 econometrics-standards.md）
```

### Python 要求

创建 `requirements.txt`：

```
pandas==2.1.0
pyfixest==0.18.0
numpy==1.26.0
matplotlib==3.8.0
```

### 版本锁定

关键包须锁定精确版本以确保可复现性。仅在测试后更新版本。

---

## 输出验证

### 表格-脚本映射

在 REPLICATION.md 中创建表格，将每个输出映射到其生成脚本：

| 表格/图表 | 脚本 | 输出文件 | 脚本中的行号 |
|-------------|--------|-------------|----------------|
| 表 1 | `02_desc_stats.do` | `output/tables/tab_descriptive.tex` | 第 45 行 |
| 表 2 | `03_main_analysis.do` | `output/tables/tab_main_results.tex` | 第 78 行 |
| 图 1 | `05_tables_figures.do` | `output/figures/fig_event_study.pdf` | 第 120 行 |

### 输出校验和

对关键输出，记录 MD5 哈希值以检测意外变更：

```bash
md5sum output/tables/*.tex output/figures/*.pdf > output_checksums.txt
```

---

## 跨平台兼容性

### 路径处理

在 Stata 中使用正斜杠（兼容所有平台）：
```stata
save "data/clean/panel.dta", replace  ✓
save "data\clean\panel.dta", replace  ✗
```

### 随机种子

始终设置种子以确保可复现性：
```stata
set seed 12345
```

### 排序

当结果依赖排序顺序时（如 `by` 操作），须显式排序：
```stata
sort panel_id year
by panel_id: gen lag_y = y[_n-1]
```

---

## 保密数据处理

### 数据无法共享时

如果数据为保密数据：
1. 提供模拟真实数据结构的合成数据
2. 详细记录获取真实数据的方式
3. 提供可同时在真实数据和合成数据上运行的代码
4. 在 README 中明确说明："本复现包使用合成数据。真实数据可在[条件]下获取。"

### 合成数据生成

使用 Stata 的 `syn` 包或 Python 的 `synthpop` 生成合成数据，保留：
- 变量分布
- 相关结构
- 面板结构（如适用）

**不得**保留：
- 精确值（以保护保密性）
- 可能识别个人身份的罕见组合

---

## README 模板

每个复现包应包含顶层 README.md：

```markdown
# "[论文标题]" 复现包

## 作者
[作者姓名]

## 论文摘要
[2-3 句摘要]

## 数据可用性
[哪些数据是公开/受限/保密的]

## 计算环境要求
- Stata 18/MP（必需）
- Python 3.10+，需安装 requirements.txt 中列出的包（可选，用于交叉验证）

## 运行时间
在[机器描述]上大约 [X] 分钟

## 使用说明
1. 安装所需 Stata 包（见 code/stata/master.do 文件头）
2. 将原始数据文件放入 data/raw/（数据来源见 REPLICATION.md）
3. 运行 code/stata/master.do
4. 检查 output/logs/ 中是否有错误

## 输出
论文中的所有表格和图表生成在 output/tables/ 和 output/figures/ 中

## 联系方式
[通讯作者邮箱]
```

---

## 质量检查清单

提交复现包前，验证以下各项：

- [ ] 所有原始数据已记录来源和获取日期
- [ ] master.do 从头到尾运行无错误
- [ ] 所有预期输出文件已生成
- [ ] 输出文件与论文中的表格/图表一致
- [ ] README.md 和 REPLICATION.md 内容完整
- [ ] 代码有注释且遵循命名规范
- [ ] 所有随机操作均已设置种子
- [ ] 代码中无绝对路径（使用全局宏）
- [ ] 代码中无密码或 API 密钥
- [ ] 数据字典记录了所有变量
- [ ] 如真实数据保密，已提供合成数据

---

## AEA 数据编辑器最佳实践

遵循美国经济学会 (AEA) 数据编辑器指南：

1. **一键运行全部**: 单个主控脚本应能复现所有结果。
2. **清晰分离**: 原始数据不得被修改；所有输出写入 clean/temp 文件夹。
3. **最少人工干预**: 不得要求"取消注释此行"或"先运行第 1-3 节"之类的操作。
4. **完整文档**: 每个数据来源、每个假设、每个转换操作均须记录。
5. **干净环境测试**: 提交前在全新计算机上测试复现包。
