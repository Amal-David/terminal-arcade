from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path


AUDIO_DIR = Path(__file__).resolve().parent / "audio_assets"
SOUND_FILES = {
    "laser": "laser.wav",
    "enemy_blast": "enemy_blast.wav",
    "player_hit": "player_hit.wav",
    "boss_blast": "boss_blast.wav",
    "menu": "menu.wav",
}
MIN_PLAY_INTERVALS = {
    "laser": 0.05,
    "enemy_blast": 0.08,
    "player_hit": 0.20,
    "boss_blast": 0.25,
    "menu": 0.08,
}


class AudioManager:
    """Small optional sound-effect player for terminal gameplay."""

    def __init__(self) -> None:
        self.player = shutil.which("afplay") or shutil.which("ffplay")
        self.enabled = self.player is not None and AUDIO_DIR.exists()
        self.notice = None if self.enabled else "Audio unavailable"
        self._last_played: dict[str, float] = {}
        self._processes: list[subprocess.Popen[bytes]] = []

    def play(self, sound_name: str) -> None:
        if not self.enabled:
            return
        filename = SOUND_FILES.get(sound_name, f"{sound_name}.wav")
        sound_path = AUDIO_DIR / filename
        if not sound_path.exists():
            self.notice = "Star Blast audio assets missing"
            return

        now = time.monotonic()
        min_interval = MIN_PLAY_INTERVALS.get(sound_name, 0.0)
        if now - self._last_played.get(sound_name, 0.0) < min_interval:
            return
        self._last_played[sound_name] = now

        self._reap_finished()
        args = [self.player, str(sound_path)]
        if Path(self.player).name == "ffplay":
            args = [self.player, "-nodisp", "-autoexit", "-loglevel", "quiet", str(sound_path)]
        self._processes.append(
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )

    def _reap_finished(self) -> None:
        self._processes = [process for process in self._processes if process.poll() is None]

    def stop(self) -> None:
        for process in self._processes:
            if process.poll() is None:
                process.terminate()
        self._processes.clear()
