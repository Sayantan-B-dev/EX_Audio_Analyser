"""LivePipeline: one duplex callback combining analysis + monitor + voice + rec.

Keeps audio-thread work in a single place so app.py stays thin.
"""

import numpy as np
import sounddevice as sd

from . import config


class LivePipeline:
    def __init__(self, engine, monitor, voice, recorder, denoiser=None) -> None:
        self.engine = engine
        self.monitor = monitor
        self.voice = voice
        self.recorder = recorder
        self.denoiser = denoiser

    def callback(self, indata, outdata, frames, time_info, status) -> None:
        # 1. analysis path (reuses engine queue logic incl. status tracking)
        try:
            self.engine.callback(indata, frames, time_info, status)
        except Exception:
            pass
        try:
            mono = np.asarray(indata[:, 0], dtype=np.float32)
        except Exception:
            outdata.fill(0)
            return

        # 2. record dry mic signal
        try:
            self.recorder.append(mono)
        except Exception:
            pass

        # 3. denoise learns every block (self-training); cleans when on
        try:
            if self.denoiser is not None:
                self.denoiser.learn(mono)
                if self.denoiser.enabled:
                    mono = self.denoiser.process(mono)
        except Exception:
            pass

        # 4. voice fx -> monitor gain -> speakers
        try:
            fx = self.voice.process(mono)
            out = self.monitor.apply(fx)
        except Exception:
            out = np.zeros_like(mono)
        try:
            outdata[:, 0] = out
            if outdata.shape[1] > 1:  # mirror mono to extra channels
                outdata[:, 1:] = out.reshape(-1, 1)
        except Exception:
            pass

    def open_stream(self):
        """Duplex stream; falls back to mic-only InputStream if no output dev."""
        try:
            return sd.Stream(
                samplerate=config.SAMPLE_RATE,
                blocksize=config.BLOCK_SIZE,
                channels=1,
                dtype="float32",
                callback=self.callback,
            )
        except Exception as exc:
            print(f"No duplex output ({exc}); mic-only mode, hearing disabled.")
            self.monitor.enabled = False
            return self.engine.stream()
