from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path


AUDIO_DIR = Path(__file__).resolve().parent.parent / "assets" / "audio"


class AudioManager:
    def __init__(self) -> None:
        self.player = shutil.which("afplay")
        self.enabled = self.player is not None and AUDIO_DIR.exists()
        self.notice = None if self.enabled else "Audio unavailable"
        self._music_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._music_process: subprocess.Popen[bytes] | None = None

    def start_music(self) -> None:
        if not self.enabled or self._music_thread is not None:
            return
        loop_path = AUDIO_DIR / "game_loop.wav"
        if not loop_path.exists():
            self.notice = "Audio assets missing"
            return

        self._stop_event.clear()
        self._music_thread = threading.Thread(
            target=self._music_loop,
            args=(loop_path,),
            daemon=True,
        )
        self._music_thread.start()

    def _music_loop(self, loop_path: Path) -> None:
        while not self._stop_event.is_set():
            self._music_process = subprocess.Popen(
                [self.player, str(loop_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            while self._music_process.poll() is None:
                if self._stop_event.wait(0.1):
                    self._music_process.terminate()
                    self._music_process.wait(timeout=1)
                    return
            self._music_process = None

    def play(self, sound_name: str) -> None:
        if not self.enabled:
            return
        sound_path = AUDIO_DIR / f"{sound_name}.wav"
        if not sound_path.exists():
            return
        subprocess.Popen(
            [self.player, str(sound_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._music_process and self._music_process.poll() is None:
            self._music_process.terminate()
        if self._music_thread is not None:
            self._music_thread.join(timeout=1)
        self._music_thread = None
        self._music_process = None
