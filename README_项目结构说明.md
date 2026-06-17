# 项目目录结构说明

本目录按功能将各类小工具整理到独立的子目录中，方便管理和使用。

## 目录一览

| 目录 | 功能说明 |
|------|---------|
| `IP去重工具/` | IP 地址/CIDR 网段去重工具（iponly.py） |
| `文件查询助手/` | 本地文件批量查询工具（filefind.py） |
| `正则验证工具/` | 正则表达式实时验证工具（regex.py） |
| `翻译与方言工具/` | 多语言翻译与汉语方言语音工具（Translation-tool.py） |
| `文件类型转换工具/` | 文档/表格/图像/音频等格式转换工具（transfer.py） |
| `指纹判断工具/` | TLS/SSL 指纹分析判断工具（Fingerprint-judgment.py + fingerprint_web.py） |
| `指纹分析AI智能体/` | 基于 LLM 的指纹分析 AI Agent（ai_agent.py） |
| `开发脚本/` | 补丁脚本、测试脚本、杂项文件 |
| `kim2.6project/` | 原有子项目（未改动） |

## 使用说明

1. 每个工具目录包含：
   - 主程序源码（`.py`）
   - PyInstaller 打包配置（`.spec`，如有）
   - 用户配置文件（`.json`，运行后自动生成）
   - 使用文档/操作手册（`.md`）
   - 已打包的可执行文件（`.exe`，如有）

2. 如需重新打包某个工具，进入对应目录执行 PyInstaller：
   ```bash
   cd IP去重工具
   python -m PyInstaller IP去重工具.spec --noconfirm
   ```

3. 配置文件和运行时数据均保存在各自工具目录下，互不干扰。

## 注意事项

- `build/` 和 `dist/` 目录为 PyInstaller 构建缓存/输出，已清理。重新打包时会自动生成。
- 各工具的运行依赖请查看对应目录中的使用文档。
