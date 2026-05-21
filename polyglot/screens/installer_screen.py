"""Confirm-install screen — shown after the user picks a pair."""

from __future__ import annotations

from polyglot.data.pairs import LanguagePair
from polyglot.skill import installer
from polyglot.skill.installer import HookOutcome, InstallResult


def _short_status(label: str, present: bool) -> str:
    marker = "✓" if present else "·"
    state = "installed" if present else "not installed"
    return f"  {marker} {label} hook: {state}"


def _check_state() -> tuple[bool, bool]:
    claude_settings_path = installer.claude_settings_path()
    codex_path = installer.codex_config_path()

    claude_present = False
    try:
        settings = installer.read_claude_settings(claude_settings_path)
        claude_present = installer._claude_hook_present(settings, installer.hook_command())
    except Exception:
        claude_present = False

    codex_present = False
    if codex_path.exists():
        try:
            text = codex_path.read_text(encoding="utf-8")
            codex_present = installer._codex_hook_present(text, installer.codex_hook_command())
        except Exception:
            codex_present = False
    return claude_present, codex_present


def run_install_flow(
    pair: LanguagePair,
    *,
    auto_confirm: bool = False,
    print_only: bool = False,
) -> list[HookOutcome]:
    """Run the installer outside curses so input() works cleanly.

    Caller must restore curses afterward (see polyglot/app.py).
    """
    print()
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  Polyglot install — {pair.source_lang} → {pair.target_lang}")
    print(f"╚══════════════════════════════════════════════╝")
    print()

    current = installer.get_active_pair_id()
    if current and current != pair.id:
        print(f"Current active pair: {current} → will be replaced by {pair.id}")
    elif current == pair.id:
        print(f"Current active pair: {current} (already active — will refresh hooks)")
    else:
        print(f"Current active pair: (none — first install)")
    print()

    claude_present, codex_present = _check_state()
    print(_short_status("Claude", claude_present))
    print(_short_status("Codex ", codex_present))
    print()

    if print_only:
        print("=== Manual install: add to ~/.claude/settings.json ===")
        print(installer.claude_snippet(installer.hook_command()))
        print()
        print("=== Manual install: add to ~/.codex/config.toml ===")
        print(installer.codex_snippet(installer.codex_hook_command()))
        installer.set_active_pair_id(pair.id)
        print(f"\nActive pair set to {pair.id}. Reopen polyglot to switch later.")
        return []

    outcomes = installer.install_all(
        pair_id=pair.id,
        prompt=not auto_confirm,
        claude_only=False,
        codex_only=False,
        print_only=False,
    )

    print()
    print("--- Result ---")
    for outcome in outcomes:
        marker = {
            InstallResult.INSTALLED: "✓",
            InstallResult.ALREADY_PRESENT: "✓",
            InstallResult.DECLINED: "·",
            InstallResult.FAILED: "✗",
            InstallResult.PRINTED_FALLBACK: "→",
            InstallResult.NOT_FOUND: "·",
        }[outcome.result]
        print(f"  {marker} {outcome.target}: {outcome.result.value} — {outcome.message.splitlines()[0]}")
    print()
    print(f"Active pair: {pair.id}.  Run `python3 -m polyglot.skill.cadence` to change frequency.")
    print()
    try:
        input("Press Enter to return to the cabinet...")
    except EOFError:
        pass
    return outcomes
