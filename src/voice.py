"""Live voice-changer effects. Numpy-only, stateful where needed (echo/robot phase)."""

import numpy as np

EFFECTS = ("off", "deep", "chipmunk", "robot", "echo")


class VoiceChanger:
    """Apply a fun pitch/modulation effect to mono float32 blocks."""

    def __init__(self, effect: str = "off", sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self.effect = effect if effect in EFFECTS else "off"
        self._phase = 0  # continuous sample counter for modulation fx
        delay_s = 0.28
        self._delay_len = max(1, int(sample_rate * delay_s))
        self._delay_buf = np.zeros(self._delay_len, dtype=np.float64)
        self._delay_pos = 0
        self._decay = 0.35

    # -- public API --
    @property
    def name(self) -> str:
        return self.effect

    def set_effect(self, name: str) -> str:
        if name in EFFECTS:
            self.effect = name
        return self.effect

    def cycle(self) -> str:
        idx = (EFFECTS.index(self.effect) + 1) % len(EFFECTS)
        self.effect = EFFECTS[idx]
        return self.effect

    def reset_state(self) -> None:
        self._phase = 0
        self._delay_buf.fill(0)
        self._delay_pos = 0

    def process(self, block: np.ndarray) -> np.ndarray:
        """Transform a mono block, always returning same-length float32."""
        if block.size == 0:
            return block
        x = np.asarray(block, dtype=np.float64)
        if self.effect == "off":
            out = x
        elif self.effect == "deep":
            out = _pitch_shift(x, 0.6) * 1.1
        elif self.effect == "chipmunk":
            out = _pitch_shift(x, 1.5) * 0.9
        elif self.effect == "robot":
            out = self._robot(x)
        elif self.effect == "echo":
            out = self._echo(x)
        else:
            out = x
        return np.clip(out, -1.0, 1.0).astype(np.float32)

    # -- internal fx --
    def _robot(self, x: np.ndarray) -> np.ndarray:
        n = len(x)
        t = (self._phase + np.arange(n)) / self.sample_rate
        self._phase += n
        modulator = np.sign(np.sin(2 * np.pi * 30.0 * t)) * 0.5 + 0.5
        crushed = np.round(x * 6.0) / 6.0  # light bitcrush
        return crushed * (0.35 + 0.65 * modulator)

    def _echo(self, x: np.ndarray) -> np.ndarray:
        n = len(x)
        out = np.empty(n, dtype=np.float64)
        for i in range(n):
            delayed = self._delay_buf[self._delay_pos]
            out[i] = x[i] + self._decay * delayed
            self._delay_buf[self._delay_pos] = x[i] + self._decay * delayed * 0.5
            self._delay_pos = (self._delay_pos + 1) % self._delay_len
        return out


def _pitch_shift(x: np.ndarray, factor: float) -> np.ndarray:
    """Naive same-length pitch shift via interpolated ring resampling."""
    n = len(x)
    if n == 0 or factor <= 0:
        return x
    pos = (np.arange(n, dtype=np.float64) * factor) % n
    i0 = pos.astype(np.int64)
    i1 = (i0 + 1) % n
    frac = pos - i0
    return x[i0] * (1.0 - frac) + x[i1] * frac
