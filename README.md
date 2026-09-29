# Homework 1：代码审查 Agent

一个 Python 命令行代码助手，使用支持 Function Calling 的 LLM 分析代码、选择工具并生成中文审查报告。对应作业的“代码审查 Agent”方向。

## 无 API Key 体验

需要 Python 3.10 或以上版本，仅使用标准库，无需安装第三方包。在项目目录运行：

```powershell
python -m code_review_agent --demo --verbose
```

若 Windows 的 Python 命令为 `py`，把上述 `python` 替换为 `py -3`。

`--demo` 不需要 API Key，也不会访问网络。它使用固定的模型响应，实际调用文件读取和 AST 工具检查 `examples/buggy.py`，展示共享默认参数、动态执行、除零和裸 except 风险。它不是 LLM，不理解任意问题；真实 DeepSeek 模式见下一节。

## 接入真实 DeepSeek API

在 [DeepSeek 开放平台](https://platform.deepseek.com/)创建 API Key。复制配置示例并在本地 `.env` 中填写 Key：

```powershell
Copy-Item .env.example .env
notepad .env
python -m code_review_agent --verbose '请审查 examples/buggy.py，给出问题位置、触发条件和修复建议'
```

程序启动时自动读取当前目录中的 `.env`。该文件已被 `.gitignore` 排除。不要把真实 Key 写入 `.env.example`、源码、命令参数或提交到 GitHub。程序也兼容原有的 `LLM_API_KEY` 变量，但 `DEEPSEEK_API_KEY` 优先；PowerShell 中已经设置的环境变量优先于 `.env`。

可选配置：

```powershell
$env:LLM_BASE_URL = 'https://api.deepseek.com'
$env:LLM_MODEL = 'deepseek-flash'       # 也可使用账号可用的其他模型
$env:LLM_THINKING = 'disabled'          # enabled 或 disabled
```

默认 `disabled` 更快、费用更可控，也最适合课堂演示。设置为 `enabled` 时，程序会保留 DeepSeek 返回的 `reasoning_content` 并在后续工具请求中原样回传，但不会在终端显示这部分内容。

基础地址不要包含 `/chat/completions`，程序会自动追加。没有 Key 时程序会明确报错，不会悄悄伪装成真实模型；请显式添加 `--demo` 使用离线服务。

实现遵循 DeepSeek 官方的 [首次 API 调用](https://api-docs.deepseek.com/guides/harness)、[工具调用](https://api-docs.deepseek.com/guides/tool_calls/)和[思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)说明。读取的源码和会话会发送到 DeepSeek，请仅审查适合发送的项目。

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
| LLM 调用与 Prompt 设计 | DeepSeek Chat Completions、工具调用和中文审查系统提示 |
| 至少一个工具 | `list_files`、`read_file`、`analyze_python` |
| CLI 交互 | 单次提问、多轮聊天、报告导出 |
| 上下文记忆 | 保存完整的工具调用与结果配对 |
| 错误处理与重试 | 网络及部分 HTTP 错误最多重试 2 次，显示安全截断后的服务错误 |
| 文档与验证 | README、Design.md、标准库单元测试 |

AST 检查支持 Python 语法、可变字面量默认参数、裸 except、直接 `eval/exec` 调用、字面量零除数。它是有限的启发式检查，存在误报和漏报，不能代替执行测试或人工审查。其他语言通过读取源码交给真实 LLM 审查。

工具只读，不执行用户代码，不修改源码。默认禁止工作目录外路径、隐藏文件及常见依赖目录，解析符号链接后再次检查边界。只读取白名单扩展名的 UTF-8 文本。单文件不超过 128 KiB，读取每次最多 200 行且 16000 字符，列文件最多 200 条，AST 最多输出 100 条发现。

这不是用于对抗恶意本地进程的操作系统沙箱。若文件正被其他进程替换，路径检查和读取间仍可能存在竞态。使用稳定、可信的本地项目副本。

程序将标准输出和错误输出设置为 UTF-8，避免 DeepSeek 回答中的 emoji 或特殊字符导致旧版 Windows 控制台编码异常。

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
