# 一分钟演示脚本

1. 0–10 秒：介绍“这是 Python 代码审查 Agent，包含模型决策、工具调用、上下文记忆”。
2. 10–20 秒：打开 `examples/buggy.py`，展示需要审查的代码。
3. 20–40 秒：运行 `python -m code_review_agent --demo --verbose`，说明当前是离线模拟模型，文件读取和 AST 分析是真实执行。
4. 40–50 秒：展示工具调用轨迹及带行号的报告，指出可变默认参数和除零问题。
5. 50–60 秒：展示 `python -m unittest discover -s tests -v` 结果，以及 README 和 Design.md。

若已配置真实模型，可将第 3 步换成 `python -m code_review_agent --verbose`，输入“审查 examples/buggy.py”，再追问“请解释可变默认参数为什么有问题”。录屏时隐藏 API Key。
