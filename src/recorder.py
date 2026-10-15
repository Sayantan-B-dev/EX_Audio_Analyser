"""Recorder: accumulate mic blocks in RAM, export to WAV (stdlib only)."""

import os
import wave
from datetime import datetime

import numpy as np


class Recorder:
    def __init__(self) -> None:
        self.recording = False
        self._frames: list[np.ndarray] = []

    # -- transport --
    def start(self) -> None:
        self._frames = []
        self.recording = True

    def stop(self) -> int:
        self.recording = False
        return len(self._frames)

    def toggle(self) -> bool:
        if self.recording:
            self.stop()
        else:
            self.start()
        return self.recording

    def append(self, block: np.ndarray) -> None:
        if self.recording and block.size:
            self._frames.append(np.asarray(block, dtype=np.float32).copy())

    # -- query --
    @property
    def blocks(self) -> int:
        return len(self._frames)

    def seconds(self, sample_rate: int, block_size: int) -> float:
        return self.blocks * block_size / max(sample_rate, 1)

    def has_audio(self) -> bool:
        return bool(self._frames)

    def clear(self) -> None:
        self._frames = []
        self.recording = False

    # -- export ("download" = save a WAV under recordings/) --
    def save(self, directory: str, sample_rate: int, effect: str = "off") -> str | None:
        if not self._frames:
            return None
        sample_rate = int(sample_rate)
        os.makedirs(directory, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(directory, f"rec_{stamp}_voice-{effect}.wav")
        audio = np.concatenate(self._frames)
        audio = np.clip(audio, -1.0, 1.0)
        pcm16 = (audio * 32767).astype(np.int16)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm16.tobytes())
        return path
