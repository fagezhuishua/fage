# 指纹分析 AI 智能体（ai_agent.py）操作手册

> 版本：基于当前源码  
> 技术栈：Python 3 + OpenAI API + 本地指纹库 + 在线查询 + 命令行交互

---

## 一、功能概述

`ai_agent.py` 是一款面向网络安全场景的 **命令行 AI 智能体**，专门用于自动化分析 TLS/SSL 指纹（JA3/JA4）、IP 地址、User-Agent 等数据，并能够生成结构化报告、自动生成 ACL 封禁规则、辅助修改代码。

### 核心功能

| 功能 | 说明 |
|------|------|
| 指纹文件分析 | 支持 `.txt`、`.xlsx`、`.docx` 格式的批量指纹导入与分析 |
| 单条指纹深度分析 | 对单个 JA3/JA4/IP/UA 进行本地库、在线库、风险分析 |
| 本地指纹库匹配 | 内置 JA3/JA4 指纹库，识别常见工具、爬虫、恶意指纹 |
| 在线指纹库查询 | 查询 ja3er.com、FoxIO JA4+ 等公开数据源 |
| IP 归属地查询 | 批量查询 IP 的地理位置、ISP、代理/VPN/云主机属性 |
| 威胁评级与建议 | 自动判定风险等级并给出安全处置建议 |
| 报告生成 | 输出 `.xlsx`、`.csv`、`.txt` 格式的分析报告 |
| ACL 规则生成 | 根据 URL 扩展名、UA 关键字、JA4 指纹生成 Squid 风格 ACL 规则 |
| 代码辅助 | 读取、修改项目代码文件 |
| Python 脚本执行 | 可直接执行工作目录内的 Python 脚本 |
| 多轮对话 | 基于 LLM 的 Agent，支持工具调用链和上下文记忆 |

---

## 二、运行环境

### 2.1 必需依赖

```bash
pip install openai requests
```

### 2.2 可选依赖

| 依赖 | 用途 | 缺少时的影响 |
|------|------|-------------|
| `pandas` | 生成 Excel/CSV 报告 | 报告生成功能不可用 |
| `openpyxl` | Excel 文件读写 | `.xlsx` 报告不可用 |
| `python-docx` | 读取 Word 指纹文件 | `.docx` 文件导入不可用 |

推荐全部安装：

```bash
pip install pandas openpyxl python-docx
```

### 2.3 环境变量配置

程序通过环境变量配置 LLM API：

| 环境变量 | 必填 | 默认值 | 说明 |
|----------|------|--------|------|
| `OPENAI_API_KEY` | 是（非 localhost） | 代码中硬编码值 | API 密钥 |
| `OPENAI_BASE_URL` | 否 | `https://api.deepseek.com` | API 基础地址 |
| `OPENAI_MODEL` | 否 | `deepseek-chat` | 模型名称 |

#### DeepSeek 配置示例（CMD）

```cmd
set OPENAI_API_KEY=sk-你的密钥
set OPENAI_BASE_URL=https://api.deepseek.com
set OPENAI_MODEL=deepseek-chat
```

#### OpenAI 官方配置示例

```cmd
set OPENAI_API_KEY=sk-你的密钥
set OPENAI_BASE_URL=https://api.openai.com
set OPENAI_MODEL=gpt-4o
```

### 2.4 运行方式

```bash
python ai_agent.py
```

---

## 三、系统架构

```
┌─────────────────────────────────────────────┐
│              命令行交互层（main）              │
│  （快捷指令 / 自然语言 / 脚本执行 / ACL生成）   │
├─────────────────────────────────────────────┤
│              FingerprintAgent                │
│  （记忆模块 Memory + 工具注册中心 ToolRegistry）│
├─────────────────────────────────────────────┤
│              工具函数层                       │
│  analyze_file / check_fingerprint            │
│  generate_excel_report / smart_report        │
│  read_code / modify_code / list_files        │
│  generate_acl_rule                            │
├─────────────────────────────────────────────┤
│              核心分析模块                     │
│  FingerprintImporter / FingerprintParser     │
│  ThreatAnalyzer / FingerprintCorrector       │
│  OnlineFingerDB / GeoLocator                 │
├─────────────────────────────────────────────┤
│              数据层                           │
│  JA3_FINGERPRINT_DB / JA4_FINGERPRINT_DB     │
│  FINGERPRINT_TO_IP_UA                        │
└─────────────────────────────────────────────┘
```

---

## 四、功能模块介绍

### 4.1 配置模块

- 从环境变量读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。
- 若未设置 `OPENAI_API_KEY` 且非 localhost，程序启动时会提示并退出。
- 支持 DeepSeek、OpenAI 及兼容 OpenAI API 格式的第三方服务。

### 4.2 指纹导入模块（FingerprintImporter）

支持从以下文件导入指纹数据：

| 格式 | 说明 |
|------|------|
| `.txt` | 每行一条记录，支持 `\|`、`\t`、`;`、`,` 分隔字段 |
| `.xlsx` / `.xls` | 读取所有单元格，每行拼接为一条记录 |
| `.docx` | 读取段落和表格内容 |

导入结果格式：

```python
{"raw": "原始行", "fields": ["字段1", "字段2", ...]}
```

### 4.3 指纹解析模块（FingerprintParser）

自动识别字段类型：

| 类型 | 识别规则 | 示例 |
|------|---------|------|
| `ipv4` / `ipv6` | 合法 IP 地址 | `192.168.1.1` |
| `ja3_hash` | 32 位十六进制 MD5 | `e3eaa2d6c2c087ee2914d4b0e4d43998` |
| `ja3_raw` | 5 段数字/连字符组合 | `769,47-53-5-10,...,0` |
| `ja4` | `t/q/s` 开头 + 两段哈希 | `t13d371100_db35923f8641_55dab1a219fb` |
| `ua` | 包含 Mozilla/Chrome/curl 等关键字 | `Mozilla/5.0 ...` |
| `unknown` | 无法识别 | - |

### 4.4 本地指纹库

#### JA3 指纹库（JA3_FINGERPRINT_DB）

内置数百条已知 JA3 哈希，分类包括：

- `tool`：工具类指纹（curl、wget、Python requests、Java HttpClient、Go HTTP 等）
- `crawler`：爬虫类指纹（YisouSpider、Scrapy 等）
- `anomaly`：异常/未知指纹
- `malicious`：恶意指纹

#### JA4 指纹库（JA4_FINGERPRINT_DB）

内置常见 JA4 指纹，结构与 JA3 库类似。

#### 指纹到 IP/UA 映射（FINGERPRINT_TO_IP_UA）

用于关联已知指纹与典型 IP、User-Agent。

### 4.5 在线指纹库查询（OnlineFingerDB）

#### JA3 在线查询

- 数据源：`https://ja3er.com/json/{hash}`
- 超时：8 秒
- 结果缓存，避免重复查询
- 根据返回的 User-Agent 自动分类为 tool/crawler/anomaly

#### JA4 在线/智能分析

- 尝试查询 FoxIO JA4+ GitHub 文档
- 结合 JA4 格式解析、启发式推断、本地库模糊匹配
- 输出协议、TLS 版本、SNI、密码套件数、扩展数等技术细节

### 4.6 IP 归属地查询（GeoLocator）

- 数据源：`http://ip-api.com/batch`
- 支持批量查询，每批最多 100 个 IP
- 查询频率限制：最小间隔 50ms
- 返回：国家、地区、城市、ISP、代理/VPN、云主机、移动网络属性

### 4.7 威胁分析模块（ThreatAnalyzer）

根据指纹类型综合分析风险等级：

| 风险等级 | 说明 |
|----------|------|
| `malicious` | 恶意指纹 |
| `crawler` | 爬虫类 |
| `tool` | 工具类 |
| `anomaly` | 异常指纹 |
| `proxy_vpn` | 代理/VPN |
| `cloud_hosting` | 云主机 |
| `mobile` | 移动网络 |
| `safe` | 安全 |

风险判定优先级：`malicious > anomaly > crawler > tool > proxy_vpn > cloud_hosting > mobile > safe`

每种等级对应具体的处置建议（中文/英文）。

### 4.8 指纹纠正模块（FingerprintCorrector）

- 去除 JA3 hash 中的空格、连字符
- 标准化 JA3 raw 和 JA4 格式
- 规范化 User-Agent 空白
- 标准化 IP 地址格式
- 返回纠正后的值和注意事项

### 4.9 工具注册中心（ToolRegistry）

统一管理 Agent 可调用的工具：

| 工具名 | 功能 |
|--------|------|
| `analyze_file` | 分析指纹文件 |
| `generate_excel_report` | 生成 Excel/CSV/TXT 报告 |
| `smart_report` | 智能生成报告（自然语言驱动） |
| `check_fingerprint` | 单条指纹深度分析 |
| `read_code` | 读取代码文件 |
| `modify_code` | 修改代码文件 |
| `list_files` | 列出目录文件 |
| `generate_acl_rule` | 生成 ACL 封禁规则 |

### 4.10 记忆模块（Memory）

- 保留最近 7 条对话消息
- 用于 LLM 上下文理解和追问处理
- 可通过 `clear` 指令清空

### 4.11 LLM 调用模块

- 使用 `openai` 库调用聊天补全 API
- 支持重试机制（最多 2 次）
- 对 401/404/429 等错误给出明确提示
- 温度参数 0.2，保证分析结果稳定

### 4.12 命令行交互层（main）

提供快捷指令和自然语言两种交互方式。

---

## 五、操作流程

### 5.1 启动程序

```bash
python ai_agent.py
```

启动后会显示欢迎界面和快捷指令列表。

### 5.2 快捷指令

| 指令 | 用法 | 说明 |
|------|------|------|
| `analyze` | `analyze <文件路径>` | 分析指纹文件 |
| `report` | `report <文件路径> [输出路径]` | 分析并生成报告 |
| `check` | `check <指纹值> [IP] [UA]` | 单条指纹深度分析 |
| `read` | `read <文件路径> [行号]` | 读取代码文件 |
| `modify` | `modify <文件路径>` | 交互式修改代码 |
| `ls` | `ls [目录]` | 列出文件 |
| `clear` | `clear` | 清空对话记忆 |
| `exit` / `quit` | `exit` | 退出程序 |

### 5.3 分析指纹文件

```
👤 你: analyze fingerprints.txt
```

或直接自然语言：

```
👤 你: 帮我分析 fingerprints.txt 文件
```

### 5.4 生成报告

```
👤 你: report fingerprints.txt report.xlsx
```

或自然语言：

```
👤 你: 生成报告，源文件是 fingerprints.txt，输出到 d:/report/result.xlsx
```

### 5.5 单条指纹分析

```
👤 你: check t13d371100_db35923f8641_55dab1a219fb
```

或自然语言：

```
👤 你: 分析一下这个指纹 t13d371100_db35923f8641_55dab1a219fb
```

### 5.6 生成 ACL 封禁规则

```
👤 你: 生成 ACL 规则，URL 包含 apk，UA 包含 Python，指纹是 t13d4312h1_c7886603b240_d41ae481755e
```

### 5.7 读取和修改代码

读取：

```
👤 你: read test.py
```

修改：

```
👤 你: modify test.py
```

按提示输入旧代码片段和新代码片段。

### 5.8 执行 Python 脚本

```
👤 你: 执行 iponly.py
👤 你: 后台运行 gamestest.py
```

> 执行前会要求确认（除非包含「直接」「-y」「自动」等关键词）。

### 5.9 自然语言对话

可以直接用自然语言与 Agent 交流，例如：

```
👤 你: 这个文件里有多少条恶意指纹？
👤 你: 总结一下刚才的分析结果
👤 你: 把 report.xlsx 转换成 csv 格式
```

---

## 六、报告格式说明

### 6.1 Excel/CSV 报告字段

| 字段 | 说明 |
|------|------|
| 序号 | 记录编号 |
| 原始内容 | 文件中的原始行 |
| 指纹值 | 识别出的指纹值 |
| 识别类型 | ipv4/ipv6/ja3_hash/ja3_raw/ja4/ua/unknown |
| 归属地区 | IP 查询结果（仅 IP 类型） |
| 风险类别 | 安全/工具/爬虫/异常/恶意等 |
| 风险详情 | 具体风险原因 |
| 建议和措施 | 处置建议 |
| 纠正后 | 规范化后的指纹值 |
| 关联IP | 同条记录中关联的 IP |
| 关联UA | 同条记录中关联的 UA |

### 6.2 TXT 报告

每条记录以 `-----` 分隔，包含所有字段的键值对。

---

## 七、ACL 规则生成说明

生成的 ACL 规则采用 Squid 风格语法，包含：

```
acl url_apk url_regex -i ^https?://[^/]+/.*\.apk(\?|$);
acl UAs browser -i Python;
acl ssl_finger_d41ae481755e ngxvar_regex $ssl_fingerprint_ja4 -i .*_d41ae481755e$;
aclif url_apk ssl_finger_d41ae481755e !UAs{
    http_access deny;
    http_access_deny_status_kv status_e=444;
}
```

同时附带：
- 正则说明
- 测试用例
- 注意事项
- 使用示例

---

## 八、注意事项

### 8.1 API 密钥安全

- 代码中硬编码了一个默认 API 密钥，**生产环境务必通过环境变量覆盖**。
- 不要将 API 密钥提交到代码仓库。
- 使用 `.env` 文件或环境变量管理密钥。

### 8.2 网络依赖

- LLM 调用需要稳定的网络连接。
- 在线指纹库查询（ja3er.com、FoxIO）需要网络访问。
- IP 归属地查询（ip-api.com）需要网络访问。
- 若网络不稳定，在线查询会超时并回退到本地库分析。

### 8.3 文件路径

- 支持相对路径和绝对路径。
- 相对路径首先在当前工作目录查找，然后在脚本所在目录查找。
- Windows 路径中的反斜杠会被自动处理，避免 JSON 转义问题。

### 8.4 执行 Python 脚本安全

- 只能执行当前工作目录或脚本同目录下的 `.py` 文件。
- 执行前默认需要确认，防止误操作。
- 后台执行使用 `subprocess.Popen`，不阻塞对话。
- 前台执行最多等待 60 秒，超时自动终止。

### 8.5 工具调用轮次限制

- Agent 最多连续调用 5 轮工具，防止无限循环。
- 若超过限制，会提示用户重试或简化请求。

### 8.6 记忆管理

- 对话记忆最多保留 7 条消息。
- 长时间运行后建议执行 `clear` 清空记忆。
- 退出程序时会自动清空记忆。

### 8.7 在线查询频率

- JA3 在线查询有缓存机制，相同指纹不会重复查询。
- IP 批量查询有 50ms 最小间隔限制，避免触发 API 限流。

### 8.8 报告输出

- 输出目录不存在时会自动创建。
- 同名文件会直接覆盖，请提前备份。
- Excel 报告需要 `pandas` 和 `openpyxl`。

### 8.9 风险判定仅供参考

- AI 分析和威胁评级基于已知指纹库和启发式规则，**仅供参考**。
- 实际处置前请结合业务上下文、访问日志、安全策略综合判断。
- 避免直接封禁未确认的 IP 或指纹，防止误拦截。

### 8.10 本地库更新

- 内置指纹库无法自动更新，如需新增指纹，需编辑源码中的 `JA3_FINGERPRINT_DB` 和 `JA4_FINGERPRINT_DB`。
- 建议定期同步 ja3er.com、FoxIO 等公开数据源的最新指纹。

---

## 九、常见问题（FAQ）

**Q1：启动时提示「请先设置环境变量 OPENAI_API_KEY」怎么办？**

请设置环境变量：

```cmd
set OPENAI_API_KEY=sk-你的密钥
set OPENAI_BASE_URL=https://api.deepseek.com
set OPENAI_MODEL=deepseek-chat
```

**Q2：提示 API 404 错误？**

- 检查 `OPENAI_BASE_URL` 是否正确（DeepSeek 为 `https://api.deepseek.com`，末尾不要加 `/v1`）。
- 检查 `OPENAI_MODEL` 是否拼写正确（如 `deepseek-chat`、`deepseek-reasoner`）。

**Q3：在线指纹查询失败？**

可能是网络问题或目标网站不可用。程序会自动回退到本地库分析，结果可能缺少在线库的补充信息。

**Q4：为什么有些指纹被标记为 anomaly（异常）？**

- 该指纹不在本地库中。
- 在线查询未命中或超时。
- 建议进一步结合 IP、UA、访问路径分析。

**Q5：报告生成失败？**

请确认已安装：

```bash
pip install pandas openpyxl
```

**Q6：如何添加新的指纹到本地库？**

编辑 `ai_agent.py` 中的 `JA3_FINGERPRINT_DB` 或 `JA4_FINGERPRINT_DB` 字典，按现有格式添加即可。

---

## 十、目录文件说明

| 文件 | 说明 |
|------|------|
| `ai_agent.py` | 主程序源码 |
| `finger.txt` / `finger.xlsx` / `fingerprints.txt` | 示例指纹数据文件 |
| `report_*.xlsx` / `report_*.csv` / `report_*.txt` | 生成的报告文件 |

---

## 十一、依赖安装速查

```bash
# 必需
pip install openai requests

# 推荐
pip install pandas openpyxl python-docx
```

---

**文档版本**：v1.0  
**对应程序版本**：ai_agent.py 当前版本
