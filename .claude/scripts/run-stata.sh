#!/bin/bash
# Stata 执行封装脚本 — 已通过 permissions.allow 自动批准
# 用法: bash .claude/scripts/run-stata.sh <project_dir> <do_file>
#
# 示例:
#   bash .claude/scripts/run-stata.sh \
#     "F:/Learning/econ-research-workflow/tests/test1-did/v1" \
#     "code/stata/01_did_analysis.do"

set -e

if [ $# -lt 2 ]; then
    echo "用法: bash run-stata.sh <project_dir> <do_file>"
    exit 1
fi

PROJECT_DIR="$1"
DO_FILE="$2"

cd "$PROJECT_DIR"
"D:/Stata18/StataMP-64.exe" -e do "$DO_FILE"

# --- 内联日志检查（替代封装脚本调用的 PostToolUse 钩子）---
DO_BASENAME=$(basename "$DO_FILE" .do)
LOG_FILE="${DO_BASENAME}.log"

if [ ! -f "$LOG_FILE" ]; then
    # 备选：检查 output/logs/
    LOG_FILE="output/logs/${DO_BASENAME}.log"
fi

if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -c 'r([0-9][0-9]*)' "$LOG_FILE" 2>/dev/null || true)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "=== [Stata 日志检查] 在 $LOG_FILE 中发现错误 ==="
        grep 'r([0-9][0-9]*)' "$LOG_FILE"
        echo "=== 共计: $ERROR_COUNT 个错误 ==="
    else
        echo "[Stata 日志检查] 通过: $LOG_FILE 中无 r(xxx) 错误"
    fi
else
    echo "[Stata 日志检查] 警告: 未找到 $DO_FILE 对应的 .log 文件"
fi
