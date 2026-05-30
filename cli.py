"""Command line entrypoint for course-style task execution."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from run import app as graph_app
from src.core.cli_prompts import build_prompt
from src.core.config import WORKSPACE_DIR


def _serialize(obj: Any) -> Any:
    """Best-effort serializer for graph events and state values."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_serialize(v) for v in obj]
    if hasattr(obj, "model_dump"):
        try:
            return _serialize(obj.model_dump())
        except Exception:
            return str(obj)
    if hasattr(obj, "dict"):
        try:
            return _serialize(obj.dict())
        except Exception:
            return str(obj)
    if hasattr(obj, "content"):
        payload = {"type": getattr(obj, "type", obj.__class__.__name__), "content": getattr(obj, "content", "")}
        if hasattr(obj, "name"):
            payload["name"] = getattr(obj, "name")
        if hasattr(obj, "tool_calls"):
            payload["tool_calls"] = _serialize(getattr(obj, "tool_calls"))
        if hasattr(obj, "tool_call_id"):
            payload["tool_call_id"] = getattr(obj, "tool_call_id")
        return payload
    return str(obj)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OurAI CLI")
    parser.add_argument("--task", required=True, choices=["design", "implement", "debug"], help="Task mode")
    parser.add_argument("--input", required=True, dest="input_path", help="Input file path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--lang", choices=["python", "java", "cpp"], default="python", help="Primary target language")
    parser.add_argument("--max-retries", type=int, default=3, help="Max sandbox retry count")
    parser.add_argument("--max-coder-steps", type=int, default=15, help="Max coder tool-call steps")
    parser.add_argument("--thread-id", default=None, help="Optional thread id for continuation")
    return parser


def _read_input_text(input_path: Path) -> str:
    if not input_path.exists():
        raise FileNotFoundError(f"input file not found: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"input path is not a file: {input_path}")
    return input_path.read_text(encoding="utf-8")


def _prepare_output_dir(path_str: str) -> Path:
    output_dir = Path(path_str).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    return output_dir


async def _run(args: argparse.Namespace) -> int:
    started_at = datetime.now()
    input_path = Path(args.input_path).resolve()
    output_dir = _prepare_output_dir(args.output)
    events_path = output_dir / "events.jsonl"
    meta_path = output_dir / "run_meta.json"
    final_state_path = output_dir / "final_state.json"
    report_path = output_dir / "report.md"
    snapshot_input_path = output_dir / "input_snapshot.txt"

    try:
        input_text = _read_input_text(input_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"[CLI] 参数错误: {e}")
        return 2

    thread_id = args.thread_id or str(uuid.uuid4())
    prompt = build_prompt(args.task, input_text, args.lang)
    snapshot_input_path.write_text(input_text, encoding="utf-8")

    initial_state = {
        "messages": [("user", prompt)],
        "max_retries": args.max_retries,
        "retry_count": 0,
        "max_coder_steps": args.max_coder_steps,
        "cancelled": False,
    }
    config = {"configurable": {"thread_id": thread_id}}

    run_status = "running"
    exception_text = ""

    with events_path.open("w", encoding="utf-8") as ef:
        try:
            async for event in graph_app.astream(initial_state, config=config, stream_mode="updates"):
                ef.write(json.dumps(_serialize(event), ensure_ascii=False) + "\n")
        except Exception as e:  # pragma: no cover - runtime safeguard
            run_status = "failed"
            exception_text = str(e)

    # Gather final state
    final_values: dict[str, Any] = {}
    try:
        state_snapshot = graph_app.get_state(config)
        if state_snapshot and getattr(state_snapshot, "values", None):
            final_values = _serialize(state_snapshot.values)
    except Exception as e:  # pragma: no cover - runtime safeguard
        if not exception_text:
            exception_text = f"failed to fetch final state: {e}"
        if run_status != "failed":
            run_status = "failed"

    final_state_path.write_text(
        json.dumps(final_values, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    test_result_src = Path(WORKSPACE_DIR) / ".test_result.json"
    test_result_dst = output_dir / "artifacts" / "test_result.json"
    if test_result_src.exists():
        shutil.copy2(test_result_src, test_result_dst)

    # Build report
    error_trace = ""
    if isinstance(final_values, dict):
        error_trace = str(final_values.get("error_trace", "") or "")
    if run_status != "failed":
        run_status = "success" if not error_trace else "max_retries_reached"

    finished_at = datetime.now()
    report = [
        "# OurAI CLI Report",
        "",
        f"- task: `{args.task}`",
        f"- thread_id: `{thread_id}`",
        f"- input: `{input_path}`",
        f"- output: `{output_dir}`",
        f"- status: `{run_status}`",
        f"- started_at: `{started_at.isoformat(timespec='seconds')}`",
        f"- finished_at: `{finished_at.isoformat(timespec='seconds')}`",
        "",
        "## Result",
    ]
    if run_status == "success":
        report.append("- Workflow finished without sandbox error trace.")
    elif run_status == "max_retries_reached":
        report.append("- Workflow reached retry limit or still has sandbox error trace.")
    else:
        report.append(f"- Workflow failed with exception: `{exception_text}`")

    if error_trace:
        report.extend(["", "## Error Trace", "```text", error_trace[:2000], "```"])

    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    run_meta = {
        "task": args.task,
        "lang": args.lang,
        "thread_id": thread_id,
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "status": run_status,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "max_retries": args.max_retries,
        "max_coder_steps": args.max_coder_steps,
        "exception": exception_text,
        "artifacts": {
            "events": str(events_path),
            "final_state": str(final_state_path),
            "report": str(report_path),
            "input_snapshot": str(snapshot_input_path),
            "test_result": str(test_result_dst) if test_result_dst.exists() else None,
        },
    }
    meta_path.write_text(json.dumps(run_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if run_status == "success":
        print(f"[CLI] Completed successfully. Output: {output_dir}")
        return 0
    if run_status == "max_retries_reached":
        print(f"[CLI] Completed with unresolved sandbox errors. Output: {output_dir}")
        return 3
    print(f"[CLI] Failed: {exception_text}")
    return 1


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())

