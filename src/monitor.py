"""Live hearing (mic -> speaker monitor) state + gain."""

import numpy as np


class LiveMonitor:
    """Owns only the monitor on/off + gain. Playback math stays trivial."""

    def __init__(self, enabled: bool = False, gain: float = 1.0) -> None:
        self.enabled = enabled
        self.gain = float(gain)

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def set_gain(self, gain: float) -> float:
        self.gain = max(0.0, min(float(gain), 3.0))
        return self.gain

    def apply(self, block: np.ndarray) -> np.ndarray:
        """Return what should be sent to speakers (silence when off)."""
        if not self.enabled or block.size == 0:
            return np.zeros_like(block, dtype=np.float32)
        out = np.asarray(block, dtype=np.float64) * self.gain
        return np.clip(out, -1.0, 1.0).astype(np.float32)

    @property
    def label(self) -> str:
        return f"ON x{self.gain:.1f}" if self.enabled else "OFF"
