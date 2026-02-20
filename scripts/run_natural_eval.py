#!/usr/bin/env python3
"""
Run natural evaluation questions against the /chat endpoint and write answers to CSV.

Usage:
  # Wide format: one row per question, columns for opus 4.6, sonnet 4.6, haiku 4.5 (answer + tool names)
  python scripts/run_natural_eval.py --wide

  # Try first 10 questions only
  python scripts/run_natural_eval.py --wide --limit 10

  # Long format: one row per (question, model)
  python scripts/run_natural_eval.py --models claude-sonnet-4-6,claude-3-5-haiku-20241022

  # Custom input/output
  python scripts/run_natural_eval.py --wide --input docs/natural_evaluation_questions.csv --output docs/natural_evaluation_results.csv
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)

# Default models for --wide: (display_label, API model_id)
# Note: claude-3-5-haiku-20241022 was retired; use claude-haiku-4-5
WIDE_DEFAULT_MODELS = [
    ("opus_4_6", "claude-opus-4-6"),
    ("sonnet_4_6", "claude-sonnet-4-6"),
    ("haiku_4_5", "claude-haiku-4-5"),
]


def load_questions(csv_path: str) -> list[str]:
    """Load questions from CSV; expects a header row with 'Question' column."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")
    questions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "Question" not in (reader.fieldnames or []):
            raise ValueError("CSV must have a 'Question' column")
        for row in reader:
            q = (row.get("Question") or "").strip()
            if q:
                questions.append(q)
    return questions


def chat_request(base_url: str, query: str, model: str | None = None, timeout: int = 120) -> dict:
    """POST to /chat and return parsed JSON. model=None uses server default."""
    url = f"{base_url.rstrip('/')}/chat"
    payload: dict = {"query": query}
    if model:
        payload["model"] = model
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def tool_calls_to_names(tool_calls: list) -> str:
    """Return comma-separated tool names from API tool_calls list."""
    if not tool_calls:
        return ""
    names = []
    for t in tool_calls:
        name = t.get("tool_name") if isinstance(t, dict) else getattr(t, "tool_name", None)
        if name:
            names.append(str(name))
    return ", ".join(names)


def run_eval_wide(
    base_url: str,
    questions: list[str],
    model_specs: list[tuple[str, str]],
    output_path: str,
    timeout: int = 120,
) -> None:
    """One row per question; columns: Question, then for each model Answer_<label>, ToolCalls_<label>."""
    fieldnames = ["Question"]
    for label, _ in model_specs:
        fieldnames.append(f"Answer_{label}")
        fieldnames.append(f"ToolCalls_{label}")
    total = len(questions) * len(model_specs)
    n = 0
    rows = []
    for question in questions:
        row: dict[str, str] = {"Question": question}
        for label, model_id in model_specs:
            n += 1
            print(f"[{n}/{total}] {label} | {question[:55]}...", flush=True)
            answer = ""
            tool_names = ""
            try:
                start = time.perf_counter()
                data = chat_request(base_url, question, model=model_id, timeout=timeout)
                answer = (data.get("response") or "").strip()
                tool_names = tool_calls_to_names(data.get("tool_calls") or [])
            except requests.exceptions.RequestException as e:
                answer = f"[Error: {e}]"
            except Exception as e:
                answer = f"[Error: {e}]"
            row[f"Answer_{label}"] = answer
            row[f"ToolCalls_{label}"] = tool_names
        rows.append(row)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output_path}")


def run_eval_long(
    base_url: str,
    questions: list[str],
    models: list[str],
    output_path: str,
    timeout: int = 120,
) -> None:
    """Call /chat for each (question, model), write long-format CSV."""
    rows = []
    total = len(questions) * len(models)
    n = 0
    for model in models:
        for question in questions:
            n += 1
            print(f"[{n}/{total}] {model or 'default'} | {question[:60]}...", flush=True)
            start = time.perf_counter()
            error_msg = ""
            response_text = ""
            tool_names = ""
            try:
                data = chat_request(base_url, question, model=model or None, timeout=timeout)
                response_text = (data.get("response") or "").strip()
                tool_names = tool_calls_to_names(data.get("tool_calls") or [])
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
            except Exception as e:
                error_msg = str(e)
            duration_ms = (time.perf_counter() - start) * 1000
            rows.append({
                "Question": question,
                "Model": model or "(server default)",
                "Answer": response_text,
                "ToolCalls": tool_names,
                "DurationMs": round(duration_ms, 0),
                "Error": error_msg,
            })
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["Question", "Model", "Answer", "ToolCalls", "DurationMs", "Error"],
            quoting=csv.QUOTE_MINIMAL,
        )
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run natural evaluation questions via /chat and write answers to CSV.",
    )
    parser.add_argument(
        "--url",
        default=os.getenv("CHAT_URL", "http://localhost:8000"),
        help="Base URL of the chat API (default: CHAT_URL or http://localhost:8000)",
    )
    parser.add_argument(
        "--wide",
        action="store_true",
        help="One row per question; columns: Question, then Answer_<model>, ToolCalls_<model> for opus_4_6, sonnet_4_6, haiku_4_5",
    )
    parser.add_argument(
        "--models",
        default="",
        help="Comma-separated model IDs for long format (ignored if --wide). Empty = use server default.",
    )
    parser.add_argument(
        "--input",
        default="docs/natural_evaluation_questions.csv",
        help="Input CSV path with 'Question' column",
    )
    parser.add_argument(
        "--output",
        default="docs/natural_evaluation_results.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Request timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=0,
        metavar="N",
        help="Run only the first N questions (e.g. --limit 10 for a quick try). 0 = all.",
    )
    args = parser.parse_args()
    questions = load_questions(args.input)
    if not questions:
        print("No questions found in input CSV.", file=sys.stderr)
        sys.exit(1)
    if args.limit and args.limit > 0:
        questions = questions[: args.limit]
        print(f"Limited to first {len(questions)} question(s).")
    if args.wide:
        model_specs = WIDE_DEFAULT_MODELS
        labels = ", ".join(l for l, _ in model_specs)
        print(f"Running {len(questions)} questions x 3 models ({labels}) -> {args.output}")
        run_eval_wide(args.url, questions, model_specs, args.output, timeout=args.timeout)
    else:
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        if not models:
            models = [""]
        print(f"Running {len(questions)} questions x {len(models)} model(s) -> {args.output}")
        run_eval_long(args.url, questions, models, args.output, timeout=args.timeout)


if __name__ == "__main__":
    main()
