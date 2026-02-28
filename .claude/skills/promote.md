---
description: "将 explore/ 沙盒中的探索性文件提升至主 vN/ 流水线，含重新编号和质量检查"
user_invocable: true
---

# /promote — 将探索性结果提升至主流水线

将 `explore/` 沙盒中的文件提升至主 `vN/` 流水线，应用完整质量标准。

## 激活

当用户运行 `/promote` 时，应指定：
- **来源**：`explore/` 中要提升的文件（如 `explore/code/alt_spec.do`）
- **目标**：版本目录中的目标位置（如 `v1/code/stata/`）

如果未提供参数，提示用户指定来源和目标。

## 步骤

### 1. 识别来源文件

列出 `explore/` 中的文件，如果未指定则询问用户要提升哪些：

```
explore/ 中的文件：
  explore/code/alt_spec_EXPLORATORY.do
  explore/code/new_outcome_EXPLORATORY.py
  explore/output/alt_results.tex

要提升哪些文件？（指定路径或输入 "all"）
```

### 2. 复制并重命名

对每个来源文件：

1. 从 `explore/` 复制到目标 `vN/` 位置
2. 如果存在 `_EXPLORATORY` 后缀则去除
3. 重新编号以适应 `vN/code/` 的序列：
   - 检查已有的编号脚本（如 `01_`、`02_`、...、`06_`）
   - 分配下一个可用编号
   - 示例：`alt_spec_EXPLORATORY.do` → `07_alt_spec.do`

### 3. 升级至完整标准

复制后，对提升的文件应用完整流水线标准：

- 添加完整文件头（如果是简化版）
- 添加规范的日志记录（`cap log close` / `log using` / `log close`）
- 如果缺少变量标签则添加
- 确保包含 `set seed 12345`
- 如果回归缺少 `vce(cluster ...)` 则添加

### 4. 质量检查

对提升的文件运行 `/score` 以验证是否符合主流水线标准：

- 如果评分 >= 80：提升成功，通知用户
- 如果评分 < 80：警告用户并列出需要修复的具体问题

```
提升完成：
  explore/code/alt_spec_EXPLORATORY.do → v1/code/stata/07_alt_spec.do
  质量评分：85/100

  或

  质量评分：72/100
  问题：
    - 缺少交叉验证脚本
    - 生成的变量缺少变量标签
  请对 v1/code/stata/07_alt_spec.do 运行 /adversarial-review 进行处理。
```

### 5. 清理（可选）

询问用户是否要从 `explore/` 中删除已提升的源文件：

```
是否删除 explore/ 中已提升的文件？(y/n)
```

## 注意事项

- 在未经确认的情况下，不覆盖 `vN/` 中的已有文件
- 在用户确认删除之前，保留 `explore/` 中的原始探索性文件
- 如果提升的是 Python 交叉验证脚本，将其放置在 `vN/code/python/`
- 如果向序列中添加了新的 Stata 脚本，更新 `master.do`
