# 离线演示审查结果

固定演示：只分析 examples/buggy.py，不调用 LLM，也不理解任意问题。

- [medium] examples/buggy.py:4 可变默认参数会在多次调用间共享状态。建议：使用 None 作为默认值，在函数内部创建容器。
- [high] examples/buggy.py:10 检测到 eval 调用，外部输入可能导致代码执行。建议：核实输入来源，按数据格式使用 json.loads 等解析方式。
- [high] examples/buggy.py:15 除数为字面量 0，执行到此处会抛出异常。建议：修正除数，并处理零值输入。
- [medium] examples/buggy.py:16 裸 except 会捕获退出和中断等异常。建议：捕获具体异常类型，并保留可诊断信息。

分析方式：读取源码和 AST 静态检查，未运行被审查代码。真实语义审查请配置模型后运行。
