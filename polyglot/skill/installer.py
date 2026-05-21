#!/usr/bin/env python3
"""Install/uninstall the polyglot Claude PostToolUse hook and Codex notify hook.

Auto-edits ~/.claude/settings.json with confirmation and a unified-diff preview;
falls back to printing the manual JSON snippet when the file is unreadable or
unwritable. Codex install rewrites ~/.codex/config.toml in place (best effort).

Switching the active language pair never touches settings.json again — only the
polyglot config's `active_pair_id` field flips. The first install is the only
write to settings.json.

CLI usage:
    python3 -m polyglot.skill.installer status
    python3 -m polyglot.skill.installer install [--print] [--claude-only | --codex-only] [--yes]
    python3 -m polyglot.skill.installer uninstall [--yes]
    python3 -m polyglot.skill.installer set-pair <pair_id>
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from polyglot.storage import (  # noqa: E402
    get_active_pair_id,
    load_config,
    save_config,
    set_active_pair_id,
)


class InstallResult(Enum):
    INSTALLED = "installed"
    ALREADY_PRESENT = "already_present"
    DECLINED = "declined"
    FAILED = "failed"
    PRINTED_FALLBACK = "printed_fallback"
    NOT_FOUND = "not_found"


@dataclass
class HookOutcome:
    target: str  # "claude" | "codex"
    result: InstallResult
    message: str
    diff: str = ""


CLAUDE_HOOK_FILENAME = "hook.py"
CODEX_HOOK_FILENAME = "codex_notify.py"
SETTINGS_BACKUP_SUFFIX = ".polyglot.bak"


def claude_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def codex_config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def hook_command() -> str:
    return str((PROJECT_ROOT / "polyglot" / "skill" / CLAUDE_HOOK_FILENAME).resolve())


def codex_hook_command() -> str:
    return str((PROJECT_ROOT / "polyglot" / "skill" / CODEX_HOOK_FILENAME).resolve())


# -----------------------------------------------------------------------------
# Claude settings.json
# -----------------------------------------------------------------------------

def read_claude_settings(path: Path | None = None) -> dict:
    path = path or claude_settings_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        raise


def _claude_hook_present(settings: dict, hook_cmd: str) -> bool:
    hooks_block = settings.get("hooks", {})
    if not isinstance(hooks_block, dict):
        return False
    post_tool_use = hooks_block.get("PostToolUse", [])
    if not isinstance(post_tool_use, list):
        return False
    for matcher in post_tool_use:
        if not isinstance(matcher, dict):
            continue
        for hook in matcher.get("hooks", []) or []:
            if not isinstance(hook, dict):
                continue
            cmd = str(hook.get("command", ""))
            if hook_cmd in cmd and "polyglot" in cmd:
                return True
    return False


def _add_claude_hook(settings: dict, hook_cmd: str) -> dict:
    new = json.loads(json.dumps(settings))  # deep copy
    hooks_block = new.setdefault("hooks", {})
    if not isinstance(hooks_block, dict):
        hooks_block = {}
        new["hooks"] = hooks_block
    post_tool_use = hooks_block.setdefault("PostToolUse", [])
    if not isinstance(post_tool_use, list):
        post_tool_use = []
        hooks_block["PostToolUse"] = post_tool_use
    post_tool_use.append({
        "hooks": [
            {
                "type": "command",
                "command": f"python3 {hook_cmd}",
                "timeout": 5,
            }
        ]
    })
    return new


def _remove_claude_hook(settings: dict, hook_cmd: str) -> dict:
    new = json.loads(json.dumps(settings))
    hooks_block = new.get("hooks", {})
    if not isinstance(hooks_block, dict):
        return new
    post_tool_use = hooks_block.get("PostToolUse", [])
    if not isinstance(post_tool_use, list):
        return new
    pruned = []
    for matcher in post_tool_use:
        if not isinstance(matcher, dict):
            pruned.append(matcher)
            continue
        kept_hooks = []
        for hook in matcher.get("hooks", []) or []:
            if not isinstance(hook, dict):
                kept_hooks.append(hook)
                continue
            cmd = str(hook.get("command", ""))
            if hook_cmd in cmd and "polyglot" in cmd:
                continue
            kept_hooks.append(hook)
        if kept_hooks:
            new_matcher = dict(matcher)
            new_matcher["hooks"] = kept_hooks
            pruned.append(new_matcher)
    hooks_block["PostToolUse"] = pruned
    return new


def compute_claude_diff(settings: dict, hook_cmd: str) -> tuple[dict, str]:
    if _claude_hook_present(settings, hook_cmd):
        return settings, ""
    new = _add_claude_hook(settings, hook_cmd)
    before = json.dumps(settings, indent=2, ensure_ascii=False).splitlines(keepends=True)
    after = json.dumps(new, indent=2, ensure_ascii=False).splitlines(keepends=True)
    diff = "".join(
        difflib.unified_diff(
            before, after, fromfile="settings.json", tofile="settings.json (proposed)", n=3
        )
    )
    return new, diff


def write_claude_settings(new_settings: dict, path: Path | None = None) -> None:
    path = path or claude_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(path.name + SETTINGS_BACKUP_SUFFIX)
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
    fd, tmp_path = tempfile.mkstemp(prefix=".settings.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(new_settings, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def claude_snippet(hook_cmd: str) -> str:
    return json.dumps(
        {
            "hooks": {
                "PostToolUse": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": f"python3 {hook_cmd}",
                                "timeout": 5,
                            }
                        ]
                    }
                ]
            }
        },
        indent=2,
    )


def install_claude_hook(
    *,
    prompt: bool = True,
    confirm: callable | None = None,
    path: Path | None = None,
) -> HookOutcome:
    hook_cmd = hook_command()
    settings_path = path or claude_settings_path()
    try:
        settings = read_claude_settings(settings_path)
    except (OSError, json.JSONDecodeError) as exc:
        msg = (
            f"Could not read {settings_path}: {exc.__class__.__name__}. "
            "Add this block to your settings.json manually:\n\n"
            + claude_snippet(hook_cmd)
        )
        print(msg)
        return HookOutcome("claude", InstallResult.PRINTED_FALLBACK, msg)

    if _claude_hook_present(settings, hook_cmd):
        return HookOutcome("claude", InstallResult.ALREADY_PRESENT, "Claude hook already installed.")

    new_settings, diff = compute_claude_diff(settings, hook_cmd)
    if prompt:
        accept = confirm(diff) if confirm else _default_confirm(diff, label="Claude")
        if not accept:
            return HookOutcome("claude", InstallResult.DECLINED, "User declined Claude install.", diff)

    try:
        write_claude_settings(new_settings, settings_path)
    except OSError as exc:
        msg = (
            f"Could not write {settings_path}: {exc.__class__.__name__}. "
            "Add this block manually:\n\n" + claude_snippet(hook_cmd)
        )
        print(msg)
        return HookOutcome("claude", InstallResult.PRINTED_FALLBACK, msg, diff)
    return HookOutcome("claude", InstallResult.INSTALLED, f"Wrote {settings_path}.", diff)


def uninstall_claude_hook(
    *, prompt: bool = True, path: Path | None = None
) -> HookOutcome:
    hook_cmd = hook_command()
    settings_path = path or claude_settings_path()
    try:
        settings = read_claude_settings(settings_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HookOutcome("claude", InstallResult.FAILED, f"Could not read settings: {exc}")
    if not _claude_hook_present(settings, hook_cmd):
        return HookOutcome("claude", InstallResult.NOT_FOUND, "Claude polyglot hook not present.")
    new_settings = _remove_claude_hook(settings, hook_cmd)
    if prompt and not _default_confirm("Remove polyglot Claude hook from settings.json?", label="Claude"):
        return HookOutcome("claude", InstallResult.DECLINED, "User declined uninstall.")
    try:
        write_claude_settings(new_settings, settings_path)
    except OSError as exc:
        return HookOutcome("claude", InstallResult.FAILED, f"Write failed: {exc}")
    return HookOutcome("claude", InstallResult.INSTALLED, f"Removed polyglot hook from {settings_path}.")


# -----------------------------------------------------------------------------
# Codex config.toml
# -----------------------------------------------------------------------------

def codex_snippet(hook_cmd: str) -> str:
    return f'notify = ["python3", "{hook_cmd}"]'


def _codex_hook_present(text: str, hook_cmd: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("notify") and hook_cmd in stripped and "polyglot" in stripped:
            return True
    return False


def _replace_or_append_codex_notify(text: str, hook_cmd: str) -> str:
    snippet = codex_snippet(hook_cmd)
    lines = text.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if not replaced and stripped.startswith("notify") and "=" in stripped:
            out.append(snippet)
            replaced = True
            continue
        out.append(line)
    if not replaced:
        if out and out[-1].strip():
            out.append("")
        out.append(snippet)
    if not text.endswith("\n"):
        return "\n".join(out) + "\n"
    return "\n".join(out) + "\n"


def install_codex_hook(
    *,
    prompt: bool = True,
    confirm: callable | None = None,
    path: Path | None = None,
) -> HookOutcome:
    hook_cmd = codex_hook_command()
    config_path = path or codex_config_path()
    if not config_path.exists():
        msg = (
            f"Codex config not found at {config_path}. "
            "Create the file and add this line:\n\n" + codex_snippet(hook_cmd)
        )
        print(msg)
        return HookOutcome("codex", InstallResult.PRINTED_FALLBACK, msg)

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"Could not read {config_path}: {exc}. Add this line:\n\n" + codex_snippet(hook_cmd)
        print(msg)
        return HookOutcome("codex", InstallResult.PRINTED_FALLBACK, msg)

    if _codex_hook_present(text, hook_cmd):
        return HookOutcome("codex", InstallResult.ALREADY_PRESENT, "Codex hook already installed.")

    new_text = _replace_or_append_codex_notify(text, hook_cmd)
    diff = "".join(
        difflib.unified_diff(
            text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile="config.toml",
            tofile="config.toml (proposed)",
            n=3,
        )
    )
    if prompt:
        accept = confirm(diff) if confirm else _default_confirm(diff, label="Codex")
        if not accept:
            return HookOutcome("codex", InstallResult.DECLINED, "User declined Codex install.", diff)

    try:
        backup = config_path.with_name(config_path.name + SETTINGS_BACKUP_SUFFIX)
        if not backup.exists():
            backup.write_bytes(config_path.read_bytes())
        fd, tmp_path = tempfile.mkstemp(prefix=".config.", dir=str(config_path.parent))
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        os.replace(tmp_path, config_path)
    except OSError as exc:
        msg = f"Could not write {config_path}: {exc}. Add this line:\n\n" + codex_snippet(hook_cmd)
        print(msg)
        return HookOutcome("codex", InstallResult.PRINTED_FALLBACK, msg, diff)
    return HookOutcome("codex", InstallResult.INSTALLED, f"Wrote {config_path}.", diff)


# -----------------------------------------------------------------------------
# Prompt helper + high-level install
# -----------------------------------------------------------------------------

def _default_confirm(preview: str, *, label: str = "polyglot") -> bool:
    print(f"\n=== {label} hook install ===")
    if preview:
        print(preview)
    try:
        reply = input(f"Apply {label} change? [y/N] ").strip().lower()
    except EOFError:
        return False
    return reply in {"y", "yes"}


def install_all(
    *,
    pair_id: str | None = None,
    prompt: bool = True,
    confirm: callable | None = None,
    claude_only: bool = False,
    codex_only: bool = False,
    print_only: bool = False,
) -> list[HookOutcome]:
    outcomes: list[HookOutcome] = []
    if pair_id:
        set_active_pair_id(pair_id)

    if print_only:
        print("=== Claude Code: add to ~/.claude/settings.json ===")
        print(claude_snippet(hook_command()))
        print()
        print("=== Codex: add to ~/.codex/config.toml ===")
        print(codex_snippet(codex_hook_command()))
        outcomes.append(HookOutcome("claude", InstallResult.PRINTED_FALLBACK, "Printed Claude snippet."))
        outcomes.append(HookOutcome("codex", InstallResult.PRINTED_FALLBACK, "Printed Codex snippet."))
        return outcomes

    if not codex_only:
        outcomes.append(install_claude_hook(prompt=prompt, confirm=confirm))
    if not claude_only:
        outcomes.append(install_codex_hook(prompt=prompt, confirm=confirm))
    return outcomes


def status_summary(path_claude: Path | None = None, path_codex: Path | None = None) -> str:
    claude_path = path_claude or claude_settings_path()
    codex_path = path_codex or codex_config_path()
    pair_id = get_active_pair_id()

    try:
        settings = read_claude_settings(claude_path)
        claude_state = "installed" if _claude_hook_present(settings, hook_command()) else "not installed"
    except (OSError, json.JSONDecodeError):
        claude_state = "unreadable"

    if codex_path.exists():
        try:
            text = codex_path.read_text(encoding="utf-8")
            codex_state = "installed" if _codex_hook_present(text, codex_hook_command()) else "not installed"
        except OSError:
            codex_state = "unreadable"
    else:
        codex_state = "config missing"

    lines = [
        f"Active pair:   {pair_id or '(none — pick one from the polyglot grid)'}",
        f"Claude hook:   {claude_state}  ({claude_path})",
        f"Codex hook:    {codex_state}  ({codex_path})",
        f"Hook script:   {hook_command()}",
    ]
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="polyglot.skill.installer",
        description="Install / uninstall the polyglot ambient hooks.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_install = sub.add_parser("install", help="Install Claude + Codex hooks.")
    p_install.add_argument("--print", dest="print_only", action="store_true", help="Print snippets only.")
    p_install.add_argument("--claude-only", action="store_true", help="Install only the Claude hook.")
    p_install.add_argument("--codex-only", action="store_true", help="Install only the Codex hook.")
    p_install.add_argument("--yes", action="store_true", help="Skip confirmation prompts.")
    p_install.add_argument("--pair", dest="pair_id", help="Set this pair as active before installing.")

    p_un = sub.add_parser("uninstall", help="Remove the polyglot Claude hook.")
    p_un.add_argument("--yes", action="store_true", help="Skip confirmation prompts.")

    sub.add_parser("status", help="Show install status and active pair.")

    p_set = sub.add_parser("set-pair", help="Set active language pair without touching settings.json.")
    p_set.add_argument("pair_id", help="Pair id, e.g. en-es")

    args = parser.parse_args(argv)

    if args.cmd == "install":
        outcomes = install_all(
            pair_id=getattr(args, "pair_id", None),
            prompt=not args.yes,
            claude_only=args.claude_only,
            codex_only=args.codex_only,
            print_only=args.print_only,
        )
        for outcome in outcomes:
            print(f"[{outcome.target}] {outcome.result.value}: {outcome.message}")
        return 0

    if args.cmd == "uninstall":
        outcome = uninstall_claude_hook(prompt=not args.yes)
        print(f"[claude] {outcome.result.value}: {outcome.message}")
        return 0

    if args.cmd == "status":
        print(status_summary())
        return 0

    if args.cmd == "set-pair":
        from polyglot.data.content_loader import get_pair
        if not get_pair(args.pair_id):
            print(f"Unknown pair id: {args.pair_id}")
            return 2
        set_active_pair_id(args.pair_id)
        print(f"Active pair set to {args.pair_id}.")
        return 0

    parser.error("unreachable")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
