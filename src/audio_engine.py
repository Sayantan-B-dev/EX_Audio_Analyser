"""Microphone capture + rolling buffers. Owns all mutable audio state."""

import queue

import numpy as np
import sounddevice as sd

from . import config


class AudioEngine:
    def __init__(
        self,
        sample_rate: int = config.SAMPLE_RATE,
        block_size: int = config.BLOCK_SIZE,
        display_seconds: float = config.DISPLAY_SECONDS,
    ) -> None:
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.display_seconds = display_seconds
        self.audio_queue: queue.Queue = queue.Queue(
            maxsize=config.AUDIO_QUEUE_SIZE
        )
        self.wave_buffer = np.zeros(
            int(sample_rate * display_seconds), dtype=np.float32
        )
        self.latest_block = np.zeros(block_size, dtype=np.float32)
        self.peak_hold = 0.0
        self.last_status = "Initializing microphone"

    # -- sounddevice callback (runs in audio thread) --
    def callback(self, indata, frames, time_info, status) -> None:
        if status:
            self.last_status = str(status)
        try:
            self.audio_queue.put_nowait(indata[:, 0].copy())
        except queue.Full:
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put_nowait(indata[:, 0].copy())
            except queue.Empty:
                pass

    def reset_peak(self) -> None:
        self.peak_hold = 0.0

    def drain(self) -> bool:
        """Move all queued blocks into wave_buffer. Returns True if any audio."""
        got_audio = False
        while True:
            try:
                self.latest_block = self.audio_queue.get_nowait()
                self.wave_buffer = np.concatenate(
                    (self.wave_buffer, self.latest_block)
                )[-len(self.wave_buffer):]
                got_audio = True
            except queue.Empty:
                break
        return got_audio

    def observe_peak(self) -> float:
        if self.latest_block.size:
            current_peak = float(np.max(np.abs(self.latest_block)))
            self.peak_hold = max(self.peak_hold, current_peak)
        return self.peak_hold

    def stream(self):
        """Context manager yielding an open InputStream wired to this engine."""
        return sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            callback=self.callback,
        )
