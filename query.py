#!/usr/bin/env python3
"""
Query the LLM wiki using a **local** Ollama model. Automatically loads `AGENTS.md`
and wiki markdown so you do not need to `@`-mention them in Cursor.

Prerequisites (macOS):
  brew install ollama
  ollama serve   # usually runs as a login item / background service
  ollama pull llama3.2   # or mistral, qwen2.5, etc.

Examples:
  ./query.py "What does the wiki say about the VvE water line?"
  ./query.py --interactive
  ./query.py --raw-grep "jaarrekening" "Summarize 2025 utilities from matching raw files."
  OLLAMA_MODEL=mistral ./query.py "One-shot question"

Env:
  OLLAMA_HOST              default http://127.0.0.1:11434
  OLLAMA_MODEL             default llama3.2
  WIKI_CONTEXT_MAX_CHARS   cap for bundled wiki text (default 150000)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def read_text(path: Path, max_chars: int | None = None) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + f"\n\n[…truncated, file was {len(text)} chars…]\n"
    return text


def load_agents(root: Path) -> str:
    p = root / "AGENTS.md"
    if not p.is_file():
        return "(AGENTS.md not found — answer carefully and cite files.)\n"
    return read_text(p)


def load_wiki_context(root: Path, max_total: int) -> str:
    wiki = root / "wiki"
    if not wiki.is_dir():
        return "(No wiki/ directory.)\n"
    parts: list[str] = []
    total = 0
    for path in sorted(wiki.rglob("*.md")):
        chunk = f"\n\n--- {path.relative_to(root)} ---\n"
        body = read_text(path)
        if total + len(chunk) + len(body) > max_total:
            parts.append(
                f"\n\n--- further wiki files omitted (cap {max_total} chars) ---\n"
            )
            break
        parts.append(chunk + body)
        total += len(chunk) + len(body)
    return "".join(parts) if parts else "(No markdown files under wiki/.)\n"


def raw_grep_snippets(root: Path, pattern: str, max_lines: int = 80) -> str:
    raw = root / "raw"
    if not raw.is_dir():
        return "(No raw/ directory.)\n"
    rg = shutil.which("rg")
    if not rg:
        return (
            "(Install ripgrep (`brew install ripgrep`) to use --raw-grep, "
            "or pass specific files manually.)\n"
        )
    try:
        proc = subprocess.run(
            [
                rg,
                "--no-heading",
                "--line-number",
                "--max-count",
                str(max_lines),
                "-C",
                "1",
                pattern,
                str(raw),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "(rg timed out.)\n"
    out = (proc.stdout or "").strip()
    if not out:
        return f"(No matches for pattern {pattern!r} under raw/.)\n"
    return out[:120_000]


def ollama_chat(host: str, model: str, messages: list[dict[str, str]]) -> str:
    url = f"{host.rstrip('/')}/api/chat"
    payload = json.dumps(
        {"model": model, "messages": messages, "stream": False}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Ollama HTTP {e.code}: {body[:800]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(
            f"Cannot reach Ollama at {url!r} ({e}).\n"
            "Start it with: ollama serve\n"
            "Then pull a model: ollama pull llama3.2"
        ) from e

    if "error" in data and data["error"]:
        raise SystemExit(f"Ollama error: {data['error']}")
    msg = data.get("message") or {}
    return (msg.get("content") or "").strip()


def build_messages(
    agents: str,
    wiki_ctx: str,
    raw_snippets: str | None,
    question: str,
) -> list[dict[str, str]]:
    system = (
        "You follow the repository rules in the first block below (AGENTS.md). "
        "Answer in clear English with TL;DR bullets when helpful, then details. "
        "Cite paths like `wiki/...` and `raw/...` when you rely on them. "
        "If context is insufficient, say what is missing.\n\n"
        "## AGENTS.md\n"
        f"{agents}"
    )
    user_parts = ["## Bundled wiki markdown\n", wiki_ctx]
    if raw_snippets:
        user_parts.extend(["\n## ripgrep snippets from raw/ (may be partial)\n", raw_snippets])
    user_parts.extend(["\n## Question\n", question])
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "".join(user_parts)},
    ]


def run_once(args: argparse.Namespace, root: Path) -> None:
    max_wiki = int(os.environ.get("WIKI_CONTEXT_MAX_CHARS", "150000"))
    agents = load_agents(root)
    wiki_ctx = load_wiki_context(root, max_wiki)
    raw_snip = raw_grep_snippets(root, args.raw_grep) if args.raw_grep else None
    messages = build_messages(agents, wiki_ctx, raw_snip, args.question)
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    model = args.model or os.environ.get("OLLAMA_MODEL", "llama3.2")
    print(ollama_chat(host, model, messages), end="\n")


def main() -> None:
    root = repo_root()
    p = argparse.ArgumentParser(
        description="Query wiki + AGENTS.md via local Ollama (no @AGENTS in Cursor needed)."
    )
    p.add_argument(
        "question",
        nargs="?",
        help="Question (omit for --interactive)",
    )
    p.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="REPL: repeatedly read questions from stdin",
    )
    p.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", "llama3.2"),
        help="Ollama model name (default: env OLLAMA_MODEL or llama3.2)",
    )
    p.add_argument(
        "--raw-grep",
        metavar="PATTERN",
        help="Run `rg PATTERN raw/` and attach matches as extra context (needs ripgrep)",
    )
    args = p.parse_args()

    if args.interactive:
        print("Local wiki query (Ollama). Type 'exit' or Ctrl-D to quit.\n")
        while True:
            try:
                q = input("wiki> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not q or q.lower() in {"exit", "quit"}:
                break
            args.question = q
            run_once(args, root)
        return

    if not args.question:
        p.print_help()
        sys.exit(2)
    run_once(args, root)


if __name__ == "__main__":
    main()
