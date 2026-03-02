---
description: "浏览 CSMAR 数据库并通过 Python API 获取中国股票市场与会计数据"
user_invocable: true
---

# /fetch-csmar — CSMAR 数据获取

当用户调用 `/fetch-csmar` 时，按以下步骤执行：

## 步骤 1：确定模式

询问用户需要哪种模式：

| 模式 | 说明 |
|------|------|
| **browse** | 列出 CSMAR 中可用的数据库和表 |
| **query** | 按列/条件筛选获取数据（自动分页） |
| **download** | 将整张表下载为 CSV（适用于超大数据集） |
| **count** | 统计符合条件的行数（下载前先确认规模） |

## 步骤 2：收集参数

根据模式收集以下信息：

- **browse**：无需参数（列出所有数据库），或提供数据库名称以列出其中的表
- **query**：`table_name`（必填）、`columns`（可选——列名列表）、`condition`（可选——类 SQL 筛选条件）、`start_date` / `end_date`（可选）、`target_dir`（默认：`data/raw/`）
- **download**：`table_name`（必填）、`target_dir`（默认：`data/raw/`）
- **count**：`table_name`（必填）、`condition`（可选）

## 步骤 3：加载凭证并登录

按以下优先级加载 CSMAR 凭证：
1. 环境变量：`CSMAR_ACCOUNT` 和 `CSMAR_PASSWORD`
2. 项目根目录的 `personal-memory.md`（查找 CSMAR API Credentials 部分）

```python
import os

# 优先级 1：环境变量
account = os.environ.get("CSMAR_ACCOUNT")
password = os.environ.get("CSMAR_PASSWORD")

# 优先级 2：personal-memory.md（如环境变量未设置则手动解析）
if not account or not password:
    import re
    memory_path = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), "personal-memory.md")
    if os.path.exists(memory_path):
        with open(memory_path, "r", encoding="utf-8") as f:
            content = f.read()
        m_account = re.search(r"\*\*Account\*\*:\s*`([^`]+)`", content)
        m_password = re.search(r"\*\*Password\*\*:\s*`([^`]+)`", content)
        if m_account:
            account = m_account.group(1)
        if m_password:
            password = m_password.group(1)

if not account or not password:
    raise RuntimeError("未找到 CSMAR 凭证。请设置 CSMAR_ACCOUNT 和 CSMAR_PASSWORD 环境变量，或在 personal-memory.md 中填写。")

from csmarapi import CsmarService

csmar = CsmarService()
csmar.login(account, password)
```

## 步骤 4：执行所选模式

### browse 模式

```python
# 列出所有数据库
databases = csmar.getListDatabaseInfo()
print(databases)

# 列出特定数据库中的表
tables = csmar.getListTableInfo(database_name="<database>")
print(tables)

# 列出特定表的列
columns = csmar.getListColumnInfo(table_name="<table>")
print(columns)
```

### query 模式（自动分页）

CSMAR API 每次请求限制 200,000 行。使用 `BATCH_SIZE = 190000` 确保安全。

```python
import pandas as pd
import hashlib
from datetime import datetime

BATCH_SIZE = 190000
table_name = "<table_name>"
columns = "<col1,col2,...>"  # 逗号分隔，或 "" 表示所有列
condition = "<condition>"     # 如 "Stkcd = '000001'" 或 ""

all_data = []
page = 1

while True:
    result = csmar.query(
        tableName=table_name,
        columns=columns if columns else "",
        condition=condition if condition else "",
        limit=f"{(page-1)*BATCH_SIZE},{BATCH_SIZE}"
    )

    if result is None or len(result) == 0:
        break

    all_data.append(result)
    print(f"  第 {page} 页: 获取 {len(result)} 行")

    if len(result) < BATCH_SIZE:
        break

    page += 1

    # 安全提示：数据集过大时警告
    if page > 11:  # 超过 200 万行
        print("警告: 数据集超过 200 万行。建议改用 download 模式。")
        break

df = pd.concat(all_data, ignore_index=True)
print(f"共获取 {len(df)} 行")
```

### download 模式

```python
# 适用于超大表——使用服务器端导出
result = csmar.download(tableName=table_name)
# 直接保存
```

### count 模式

```python
count = csmar.count(
    tableName=table_name,
    condition=condition if condition else ""
)
print(f"行数: {count}")
```

## 步骤 5：保存至 data/raw/

使用标准化文件命名：`csmar_{tablename}_{qualifier}_{YYYYMMDD}.csv`

```python
from datetime import datetime

today = datetime.now().strftime("%Y%m%d")
qualifier = condition.replace(" ", "").replace("'", "")[:30] if condition else "full"
filename = f"csmar_{table_name}_{qualifier}_{today}.csv"
target_dir = "<target_dir>"  # 默认: "data/raw/"

os.makedirs(target_dir, exist_ok=True)
filepath = os.path.join(target_dir, filename)

# 使用 utf-8-sig 编码保存，确保 Excel 打开中文不乱码
df.to_csv(filepath, index=False, encoding="utf-8-sig")
print(f"已保存: {filepath}")

# 计算 MD5
md5 = hashlib.md5(open(filepath, "rb").read()).hexdigest()
print(f"MD5: {md5}")
```

## 步骤 6：在 REPLICATION.md 中记录数据来源

将数据下载记录追加到 REPLICATION.md：

```python
replication_path = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), "REPLICATION.md")

entry = f"""
### {table_name}

- **数据来源**: CSMAR（国泰安）
- **表名**: `{table_name}`
- **列**: {columns if columns else "全部"}
- **筛选条件**: {condition if condition else "无"}
- **下载时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- **行数**: {len(df)}
- **文件**: `{filepath}`
- **MD5**: `{md5}`
"""

with open(replication_path, "a", encoding="utf-8") as f:
    f.write(entry)

print(f"数据来源信息已追加到 REPLICATION.md")
```

## 步骤 7：验证并输出摘要

```python
# 验证文件
df_check = pd.read_csv(filepath, encoding="utf-8-sig", nrows=5)
print(f"\n文件验证——前 5 行:")
print(df_check.to_string())
print(f"\n数据维度: {df.shape}")
print(f"列名: {list(df.columns)}")
```

输出最终摘要：

```
CSMAR 数据获取完成！

  模式:      query
  表名:      <table_name>
  列:        <columns 或 "全部">
  筛选条件:  <condition 或 "无">
  行数:      <N>
  保存至:    <filepath>
  MD5:       <md5>
  数据来源:  已追加到 REPLICATION.md
```

## 常用 CSMAR 表参考

| 表名 | 说明 |
|------|------|
| `TRD_Dalyr` | 日个股回报率 (Daily stock returns) |
| `TRD_Mnth` | 月个股回报率 (Monthly stock returns) |
| `FS_Comins` | 利润表 (Income statement) |
| `FS_Combas` | 资产负债表 (Balance sheet) |
| `FS_Comscfd` | 现金流量表 (Cash flow statement) |
| `CG_Board` | 董事会 (Board of directors) |
| `TRD_Index` | 市场指数回报 (Market index returns) |
| `STK_MKT_Dalyr` | 日市场交易数据 (Daily market trading data) |
| `CG_Ycomp` | 高管薪酬 (Executive compensation) |
| `CG_ShareHolder` | 股权结构 (Shareholder structure) |

## 故障排除

- **登录失败**: 检查环境变量或 `personal-memory.md` 中的凭证。CSMAR 账号可能过期。
- **结果为空**: 先用 `browse` 模式确认表名和列名是否正确。
- **超时**: 大查询可能超时。先用 `count` 模式确认数据量，再分页查询或改用 `download` 模式。
- **编码问题**: 保存含中文字符的 CSV 文件时务必使用 `utf-8-sig` 编码。
