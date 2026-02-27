---
description: "使用 pdflatex/bibtex 管道编译 LaTeX 论文并检查错误"
user_invocable: true
---

# /compile-latex — LaTeX 编译管道

当用户调用 `/compile-latex` 时，通过完整的 pdflatex + bibtex 管道编译 .tex 文件。

## 步骤 1：确定目标

- 如果用户指定了文件：使用该文件（如 `/compile-latex v1/paper/main_en.tex`）
- 如果未指定：在当前版本的 `paper/` 目录中查找 `.tex` 文件
  - 如果找到多个，询问编译哪一个
  - 常见目标：`main_cn.tex`、`main_en.tex`

## 步骤 2：编译

从包含 .tex 文件的目录运行标准 4 遍编译：

```bash
cd /path/to/paper/directory
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

使用 `-interaction=nonstopmode` 使编译在遇到错误时继续（以便收集所有问题）。

## 步骤 3：检查错误

读取 pdflatex 生成的 `.log` 文件并检查：

### 错误（必须修复）
- `! LaTeX Error:` — 包错误、未定义命令
- `! Missing` — 缺少分隔符
- `! Undefined control sequence` — 命令拼写错误
- `! File not found` — 缺少输入文件或图形

### 警告（应该修复）
- `LaTeX Warning: Reference .* undefined` — 断裂的 `\ref{}` 或 `\cite{}`
- `LaTeX Warning: Label .* multiply defined` — 重复标签
- `Overfull \\hbox` — 行超出页边距（超过 10pt 时报告）
- `Package natbib Warning: Citation .* undefined` — 缺少参考文献条目

### 信息（相关时报告）
- 输出 PDF 的页数
- 参考文献是否成功构建
- 警告总数

## 步骤 4：报告结果

```
main_en.tex 编译报告
═══════════════════════════════════

  状态：     成功（有警告）
  输出：     v1/paper/main_en.pdf
  页数：     24

  错误：     0
  警告：     3
    - 未定义引用：fig:event_study（第 142 行）
    - Overfull hbox (12.3pt)，第 256 行
    - 引用 "smith2024" 未定义

  需要处理：
    1. 在图形章节中为 fig:event_study 添加标签
    2. 检查第 256 行是否有需要改写的长文本
    3. 在 references.bib 中添加 smith2024 条目
```

## 步骤 5：处理缺少的包

如果编译因 `! LaTeX Error: File 'package.sty' not found` 失败：

- TeX Live：建议 `tlmgr install <package>`
- MiKTeX：建议打开 MiKTeX Console 安装缺少的包
- 清楚报告具体的包名称

## 注意事项

- 对于中文论文（`main_cn.tex`），如果使用 `ctex` 配合系统字体，可能需要 `xelatex` 替代 `pdflatex`。检查 documentclass 并在适当时建议使用 `xelatex`。
- 如果 `bibtex` 报告 "I found no \citation commands"，参考文献部分可能已被注释掉——这在早期草稿中是正常的。
