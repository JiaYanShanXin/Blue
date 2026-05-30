"""Prompt templates for CLI task modes."""

from __future__ import annotations

from typing import Literal

TaskType = Literal["design", "implement", "debug"]


def build_prompt(task: TaskType, input_text: str, lang: str | None = None) -> str:
    """Build a task-specific prompt from CLI arguments."""
    normalized_lang = (lang or "python").strip().lower()

    if task == "design":
        return f"""你是软件架构与设计专家。请根据输入内容完成分析与设计。

【输入内容】
{input_text}

【输出要求】
1. 给出系统分析（模块职责、关键流程、主要数据对象）。
2. 生成至少两种设计图，使用 Mermaid 或 PlantUML 文本格式：
   - 必选两种：类图 / 活动图 / 状态机图。
3. 给出实现建议（技术栈与分层建议）。
4. 在最后用【目标文件】列出建议生成或修改的文件路径（每行一个）。
"""

    if task == "debug":
        return f"""你是资深调试工程师。请定位并修复错误，并验证修复有效。

【输入内容】
{input_text}

【修复要求】
1. 先定位错误位置与根因（简要解释）。
2. 修改代码并补充或修正测试。
3. 运行测试并根据结果继续修复，直到通过或达到最大重试。
4. 在最后用【目标文件】列出本次涉及的文件路径（每行一个）。
"""

    # default: implement
    return f"""你是软件工程实现专家。请基于输入需求实现代码并完成测试闭环。

【输入内容】
{input_text}

【实现要求】
1. 使用 {normalized_lang} 完成功能实现（如涉及多语言，以该语言为主）。
2. 生成或修改对应测试用例。
3. 运行测试并汇总结果；若失败则自动修复后再次测试。
4. 在最后用【目标文件】列出本次涉及的文件路径（每行一个）。
"""

