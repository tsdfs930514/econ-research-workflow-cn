# Bash 命令规范

## 禁止链式命令

**永远不要**使用 `&&`、`||` 或 `;` 在单次 Bash 调用中串联多个命令。

### 原因

1. **权限绕过**：链式命令作为单个字符串匹配。`Bash(python *)` 无法匹配 `cd /path && python script.py`（因为字符串以 `cd` 开头），导致整个权限系统失效。
2. **错误可见性**：命令串联时，中间步骤的失败可能被吞没。分开调用可以获得每个命令清晰的退出码。
3. **钩子准确性**：PostToolUse 钩子（如 `stata-log-check.py`、`raw-data-guard.py`）每次工具调用只运行一次。串联命令会隐藏是哪个命令触发了问题。

### 禁止的模式

```bash
# 错误 — 用 && 串联
cd /path && python script.py

# 错误 — 用 || 串联
ls dir/ 2>/dev/null || echo "missing"

# 错误 — 用 ; 串联
mkdir -p output; python run.py

# 错误 — 子 shell 技巧
(cd data && rm *.csv)
```

### 要求的模式

对每个独立命令使用**单独的 Bash 工具调用**：

```bash
# 调用 1
cd /path

# 调用 2
python script.py
```

如果需要检查条件（如目录是否存在），使用能直接完成检查的单个命令：

```bash
# 正确 — 单个命令，无串联
ls dir/

# 正确 — 使用内置测试
test -d dir/ && echo exists   # 例外：简单的 test-then-echo 允许
```

### 有限例外

仅在以下情况允许 `&&` 串联：
- 第一个命令是 `cd`，第二个是实际工作命令，且
- 该操作**必须**从该目录运行（如 `cd project && make`）

即便如此，也应优先使用绝对路径以避免 `cd`。

## 优先使用绝对路径

使用绝对路径代替先 `cd` 再执行：

```bash
# 正确
python "F:/Learning/project/v1/code/python/01_clean.py"

# 错误
cd "F:/Learning/project/v1/code/python" && python 01_clean.py
```

## 标准错误输出

不要用 `2>/dev/null` 抑制 stderr。错误应当可见：

```bash
# 错误
ls output/ 2>/dev/null

# 正确
ls output/
```
