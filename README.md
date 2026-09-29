# Homework 1：代码审查 Agent

一个 Python 命令行代码助手，使用支持 Function Calling 的 LLM 分析代码、选择工具并生成中文审查报告。对应作业的“代码审查 Agent”方向。

## 快速体验

需要 Python 3.10 或以上版本，仅使用标准库，无需安装第三方包。在项目目录运行：

```powershell
python -m code_review_agent --demo --verbose
```

若 Windows 的 Python 命令为 `py`，把上述 `python` 替换为 `py -3`。

离线演示使用固定的模型响应，实际调用文件读取和 AST 工具检查 `examples/buggy.py`，展示共享默认参数、动态执行、除零和裸 except 风险。它不是 LLM，不理解任意问题；真实模型模式见下一节。

## 接入真实模型

使用提供 Chat Completions 和 `tools`/`tool_calls` 功能的模型服务。根据服务控制台填写完整基础地址和可用模型名。以 PowerShell 为例：

```powershell
$env:LLM_API_KEY = '替换为你的 API Key'
$env:LLM_BASE_URL = '替换为服务商的兼容接口基础地址，以 /v1 结尾'
$env:LLM_MODEL = '替换为支持工具调用的模型名'
python -m code_review_agent --verbose '请审查 examples/buggy.py，给出问题位置、触发条件和修复建议'
```

基础地址不包含 `/chat/completions`，程序自动追加该路径。不同地区的地址、Key 和模型权限可能不同，需使用同一服务区域的配置。环境变量缺失会报错，不会自动切换成演示模式。`.env.example` 仅供参考，程序不会自动加载 `.env`。

接口实现参考：[阿里云 Function Calling 官方文档](https://www.alibabacloud.com/help/en/model-studio/qwen-function-calling)。采用标准的工具描述、assistant 工具请求、带 `tool_call_id` 的 tool 结果，以及再次请求模型的循环。

读取的源码和会话会发送给你配置的模型服务。请仅选择适合发送的项目目录；API Key 不写入源码或报告。

## 使用方式

```powershell
# 多轮交互，可追问“为什么这里会共享状态？”、“给出修复后的函数”
python -m code_review_agent --verbose

# 审查其他目录，问题中的文件路径相对此目录
python -m code_review_agent --root 'C:\path\to\project' '请先列出文件，然后审查 main.py'

# 保存单次结果，防止意外覆盖：目标文件必须尚不存在
python -m code_review_agent --demo --output review.md

# 运行自动化测试
python -m unittest discover -s tests -v
```

交互命令：`/reset` 清空记忆，`/exit` 退出。Ctrl+C 取消程序。记忆仅存在于当前进程，最多保留 6 轮完整对话，超过约 80000 字符会按整轮移除早期记录。

## 功能与边界

| 作业要求 | 实现 |
| --- | --- |
| 输入、模型决策、工具调用、输出 | `ReviewAgent.ask` 的受限循环 |
| LLM 调用与 Prompt 设计 | 可配置模型接口和中文审查系统提示 |
| 至少一个工具 | `list_files`、`read_file`、`analyze_python` |
| CLI 交互 | 单次提问、多轮聊天、报告导出 |
| 上下文记忆 | 保存完整的工具调用与结果配对 |
| 错误处理与重试 | 网络及部分 HTTP 错误最多重试 2 次，工具错误返回模型 |
| 文档与验证 | README、Design.md、标准库单元测试 |

AST 检查支持 Python 语法、可变字面量默认参数、裸 except、直接 `eval/exec` 调用、字面量零除数。它是有限的启发式检查，存在误报和漏报，不能代替执行测试或人工审查。其他语言通过读取源码交给真实 LLM 审查。

工具只读，不执行用户代码，不修改源码。默认禁止工作目录外路径、隐藏文件及常见依赖目录，解析符号链接后再次检查边界。只读取白名单扩展名的 UTF-8 文本。单文件不超过 128 KiB，读取每次最多 200 行且 16000 字符，列文件最多 200 条，AST 最多输出 100 条发现。

这不是用于对抗恶意本地进程的操作系统沙箱。若文件正被其他进程替换，路径检查和读取间仍可能存在竞态。使用稳定、可信的本地项目副本。

## 文件结构

```text
code_review_agent/
  __main__.py      命令行入口
  agent.py         Prompt、Agent 循环、记忆
  llm.py           模型 HTTP 接口、重试
  tools.py         工作目录文件工具、AST 检查
  demo.py          固定离线演示响应
examples/buggy.py  故意存在缺陷的样例
tests/test_agent.py
Design.md         架构与取舍
```
