#!/usr/bin/env python3
from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path


SAMPLE_RATE = 22_050
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "audio"


def envelope(position: int, total: int, attack: float = 0.08, release: float = 0.2) -> float:
    attack_samples = max(1, int(total * attack))
    release_samples = max(1, int(total * release))
    if position < attack_samples:
        return position / attack_samples
    if position > total - release_samples:
        return max(0.0, (total - position) / release_samples)
    return 1.0


def synth_tone(
    frequency: float,
    duration: float,
    volume: float = 0.35,
    vibrato: float = 0.0,
    vibrato_rate: float = 6.0,
) -> array:
    total_samples = int(SAMPLE_RATE * duration)
    samples = array("h")
    for index in range(total_samples):
        t = index / SAMPLE_RATE
        pitch = frequency
        if vibrato:
            pitch += math.sin(t * math.tau * vibrato_rate) * vibrato
        wave_sample = math.sin(t * math.tau * pitch)
        shape = math.sin(t * math.tau * pitch * 2) * 0.25
        amp = (wave_sample + shape) * envelope(index, total_samples) * volume
        samples.append(int(max(-1.0, min(1.0, amp)) * 32767))
    return samples


def mix_layers(layers: list[array]) -> array:
    length = max(len(layer) for layer in layers)
    output = array("h", [0] * length)
    for layer in layers:
        for index, sample in enumerate(layer):
            value = output[index] + sample
            output[index] = max(-32767, min(32767, value))
    return output


def silence(duration: float) -> array:
    return array("h", [0] * int(SAMPLE_RATE * duration))


def concat(parts: list[array]) -> array:
    output = array("h")
    for part in parts:
        output.extend(part)
    return output


def write_wav(path: Path, data: array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(data.tobytes())


def build_loop() -> array:
    melody = [220.0, 261.63, 329.63, 392.0, 329.63, 261.63, 246.94, 293.66]
    bass = [110.0, 110.0, 130.81, 146.83, 110.0, 110.0, 123.47, 146.83]
    parts: list[array] = []
    for index, note in enumerate(melody):
        lead = synth_tone(note, 0.35, volume=0.18, vibrato=2.5)
        under = synth_tone(bass[index], 0.35, volume=0.12)
        parts.append(mix_layers([lead, under]))
    return concat(parts)


def build_sounds() -> dict[str, array]:
    return {
        "jump": synth_tone(660, 0.16, volume=0.32, vibrato=6),
        "land": synth_tone(180, 0.12, volume=0.4),
        "checkpoint": concat(
            [
                synth_tone(523.25, 0.09, volume=0.25),
                synth_tone(659.25, 0.09, volume=0.25),
                synth_tone(783.99, 0.14, volume=0.28),
            ]
        ),
        "roar_ready": mix_layers(
            [synth_tone(440, 0.18, volume=0.22), synth_tone(554.37, 0.18, volume=0.18)]
        ),
        "roar": concat(
            [
                synth_tone(196, 0.18, volume=0.28, vibrato=7),
                synth_tone(164.81, 0.22, volume=0.3, vibrato=5),
            ]
        ),
        "hit": mix_layers(
            [synth_tone(110, 0.24, volume=0.35), synth_tone(82.41, 0.22, volume=0.3)]
        ),
        "menu": synth_tone(587.33, 0.1, volume=0.22),
        "pause": synth_tone(392, 0.1, volume=0.2),
    }


def main() -> None:
    write_wav(ASSET_DIR / "game_loop.wav", build_loop())
    for name, data in build_sounds().items():
        write_wav(ASSET_DIR / f"{name}.wav", data)
    print(f"Generated audio assets in {ASSET_DIR}")


if __name__ == "__main__":
    main()
