"""Polyglot installer tests — settings.json upsert + active-pair switching."""

from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import polyglot.storage as polyglot_storage
from polyglot.skill import installer


class ClaudeHookInstallerTests(unittest.TestCase):
    def test_compute_diff_is_idempotent_when_hook_present(self) -> None:
        hook_cmd = "/tmp/fake/polyglot/skill/hook.py"
        settings = {
            "hooks": {
                "PostToolUse": [
                    {
                        "hooks": [
                            {"type": "command", "command": f"python3 {hook_cmd}", "timeout": 5}
                        ]
                    }
                ]
            }
        }
        new, diff = installer.compute_claude_diff(settings, hook_cmd)
        self.assertIs(new, settings)
        self.assertEqual(diff, "")

    def test_compute_diff_adds_post_tool_use_entry(self) -> None:
        hook_cmd = "/tmp/fake/polyglot/skill/hook.py"
        settings = {"hooks": {"PostToolUse": [{"hooks": [{"type": "command", "command": "echo other"}]}]}}
        new, diff = installer.compute_claude_diff(settings, hook_cmd)
        self.assertNotEqual(new, settings)
        post = new["hooks"]["PostToolUse"]
        self.assertEqual(len(post), 2)
        cmd = post[-1]["hooks"][0]["command"]
        self.assertIn("polyglot", cmd)
        self.assertIn(hook_cmd, cmd)
        self.assertNotEqual("", diff)

    def test_install_creates_settings_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            outcome = installer.install_claude_hook(prompt=False, path=settings_path)
            self.assertEqual(outcome.result, installer.InstallResult.INSTALLED)
            self.assertTrue(settings_path.exists())
            payload = json.loads(settings_path.read_text())
            self.assertIn("hooks", payload)
            cmd = payload["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
            self.assertIn("polyglot/skill/hook.py", cmd)

    def test_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            installer.install_claude_hook(prompt=False, path=settings_path)
            outcome = installer.install_claude_hook(prompt=False, path=settings_path)
            self.assertEqual(outcome.result, installer.InstallResult.ALREADY_PRESENT)

    def test_install_preserves_existing_unrelated_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PostToolUse": [
                                {"hooks": [{"type": "command", "command": "echo bookshelf-hook"}]}
                            ]
                        },
                        "model": "claude-opus-4-7",
                    }
                )
            )
            installer.install_claude_hook(prompt=False, path=settings_path)
            payload = json.loads(settings_path.read_text())
            self.assertEqual(payload["model"], "claude-opus-4-7")
            post = payload["hooks"]["PostToolUse"]
            self.assertEqual(len(post), 2)
            commands = [h["command"] for matcher in post for h in matcher.get("hooks", [])]
            self.assertTrue(any("bookshelf-hook" in c for c in commands))
            self.assertTrue(any("polyglot" in c for c in commands))

    def test_install_writes_one_time_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings_path.write_text(json.dumps({"model": "x"}))
            installer.install_claude_hook(prompt=False, path=settings_path)
            backup = settings_path.with_name(settings_path.name + installer.SETTINGS_BACKUP_SUFFIX)
            self.assertTrue(backup.exists())
            # Second install must NOT overwrite the original backup with new contents.
            original_backup_bytes = backup.read_bytes()
            installer.install_claude_hook(prompt=False, path=settings_path)
            self.assertEqual(backup.read_bytes(), original_backup_bytes)

    def test_uninstall_removes_only_polyglot_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PostToolUse": [
                                {"hooks": [{"type": "command", "command": "echo other"}]}
                            ]
                        }
                    }
                )
            )
            installer.install_claude_hook(prompt=False, path=settings_path)
            outcome = installer.uninstall_claude_hook(prompt=False, path=settings_path)
            self.assertEqual(outcome.result, installer.InstallResult.INSTALLED)
            payload = json.loads(settings_path.read_text())
            commands = [
                h["command"]
                for matcher in payload["hooks"]["PostToolUse"]
                for h in matcher.get("hooks", [])
            ]
            self.assertTrue(any("echo other" in c for c in commands))
            self.assertFalse(any("polyglot" in c for c in commands))

    def test_backup_is_atomic_and_skipped_when_already_present(self) -> None:
        """O_EXCL means a pre-existing backup is never re-written even if the source file changes."""
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings_path.write_text(json.dumps({"model": "first"}))
            installer.install_claude_hook(prompt=False, path=settings_path)
            backup = settings_path.with_name(settings_path.name + installer.SETTINGS_BACKUP_SUFFIX)
            self.assertTrue(backup.exists())
            original_backup_text = backup.read_text()

            # Even if someone hand-rewrites the live settings, a re-run must NOT overwrite the backup.
            settings_path.write_text(json.dumps({"model": "second-rewritten"}))
            installer._atomic_backup_once(settings_path)
            self.assertEqual(backup.read_text(), original_backup_text)

    def test_backup_preserves_private_source_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings_path.write_text(json.dumps({"secret": "private"}))
            settings_path.chmod(0o600)

            installer._atomic_backup_once(settings_path)

            backup = settings_path.with_name(settings_path.name + installer.SETTINGS_BACKUP_SUFFIX)
            self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)

    def test_declined_install_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            outcome = installer.install_claude_hook(
                prompt=True,
                confirm=lambda _: False,
                path=settings_path,
            )
            self.assertEqual(outcome.result, installer.InstallResult.DECLINED)
            self.assertFalse(settings_path.exists())


class CodexInstallerTests(unittest.TestCase):
    def test_missing_codex_config_falls_back_to_print(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            outcome = installer.install_codex_hook(prompt=False, path=cfg)
            self.assertEqual(outcome.result, installer.InstallResult.PRINTED_FALLBACK)
            self.assertFalse(cfg.exists())

    def test_install_appends_notify_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text("model = \"o4-mini\"\n")
            outcome = installer.install_codex_hook(prompt=False, path=cfg)
            self.assertEqual(outcome.result, installer.InstallResult.INSTALLED)
            text = cfg.read_text()
            self.assertIn("notify", text)
            self.assertIn("polyglot/skill/codex_notify.py", text)
            self.assertIn("model = \"o4-mini\"", text)

    def test_install_replaces_existing_notify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text("notify = [\"echo\", \"hi\"]\nmodel = \"x\"\n")
            installer.install_codex_hook(prompt=False, path=cfg)
            text = cfg.read_text()
            notify_key_lines = [
                line for line in text.splitlines() if line.strip().startswith("notify =")
            ]
            self.assertEqual(len(notify_key_lines), 1)
            self.assertIn("polyglot", text)
            self.assertNotIn("echo", text)
            self.assertIn("model = \"x\"", text)

    def test_install_does_not_replace_notify_prefixed_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text("notify_timeout = 5\nmodel = \"x\"\n")

            installer.install_codex_hook(prompt=False, path=cfg)

            text = cfg.read_text()
            self.assertIn("notify_timeout = 5", text)
            self.assertIn("notify = [", text)

    def test_install_ignores_nested_notify_and_inserts_root_key_before_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text('[features]\nnotify = "nested"\nhooks = true\n')

            installer.install_codex_hook(prompt=False, path=cfg)

            lines = cfg.read_text().splitlines()
            self.assertTrue(lines[0].startswith("notify = ["))
            self.assertIn('notify = "nested"', lines)

    def test_install_preserves_multiline_root_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text('trusted_commands = [\n  "git status",\n]\n[features]\nhooks = true\n')

            installer.install_codex_hook(prompt=False, path=cfg)

            text = cfg.read_text()
            self.assertIn('trusted_commands = [\n  "git status",\n]', text)
            self.assertLess(text.index("notify = ["), text.index("[features]"))

    def test_install_refuses_to_rewrite_multiline_notify_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            original = 'notify = [\n  "echo",\n  "hi",\n]\nmodel = "x"\n'
            cfg.write_text(original)

            outcome = installer.install_codex_hook(prompt=False, path=cfg)

            self.assertEqual(outcome.result, installer.InstallResult.PRINTED_FALLBACK)
            self.assertEqual(cfg.read_text(), original)

    def test_codex_backup_preserves_private_config_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text('model = "x"\n')
            cfg.chmod(0o600)

            installer.install_codex_hook(prompt=False, path=cfg)

            backup = cfg.with_name(cfg.name + installer.SETTINGS_BACKUP_SUFFIX)
            self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)

    def test_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "config.toml"
            cfg.write_text("")
            installer.install_codex_hook(prompt=False, path=cfg)
            outcome = installer.install_codex_hook(prompt=False, path=cfg)
            self.assertEqual(outcome.result, installer.InstallResult.ALREADY_PRESENT)


class ActivePairPersistenceTests(unittest.TestCase):
    def test_set_active_pair_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(polyglot_storage, "data_dir", return_value=Path(tmp)):
                polyglot_storage.set_active_pair_id("en-fr")
                self.assertEqual(polyglot_storage.get_active_pair_id(), "en-fr")

    def test_history_tracks_pair_picks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(polyglot_storage, "data_dir", return_value=Path(tmp)):
                polyglot_storage.set_active_pair_id("en-fr")
                polyglot_storage.set_active_pair_id("en-ja")
                polyglot_storage.set_active_pair_id("en-fr")
                cfg = polyglot_storage.load_config()
                self.assertEqual(cfg["pair_history"][-1], "en-fr")
                self.assertIn("en-ja", cfg["pair_history"])


if __name__ == "__main__":
    unittest.main()
