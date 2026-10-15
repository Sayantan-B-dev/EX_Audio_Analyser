"""Adaptive noise cleanup. Self-training spectral gate.

How it works:
- Every mic block is observed via learn(): if the frame looks like
  background (RMS near the tracked floor), its spectrum is folded into
  a running noise profile with an exponential moving average.
- Early frames adapt fast, later frames refine slowly — so the longer
  the app runs, the sharper the profile gets ("the more it runs...").
- process() applies spectral subtraction with a smoothed gain mask.
  Rectangular window => perfect reconstruction when the mask is 1,
  so enabling/disabling never clicks or distorts clean audio.

Numpy-only, stateful, safe to call from the audio thread.
"""

import numpy as np

_EPS = 1e-10


class AdaptiveDenoiser:
    def __init__(self, sample_rate: int = 16000, frame_size: int = 1024,
                 enabled: bool = False) -> None:
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.enabled = enabled
        self.n_bins = frame_size // 2 + 1
        self.noise_mag = np.zeros(self.n_bins, dtype=np.float64)
        self._smooth_gain = np.ones(self.n_bins, dtype=np.float64)
        self._floor_db = -50.0      # tracked background level (dBFS)
        self.learned_frames = 0     # noise-only frames absorbed so far
        self.total_frames = 0
        # Tuning (kept here so config.py stays small)
        self.oversub = 2.0          # magnitude over-subtraction factor
        self.floor_keep = 0.08      # residual floor (avoids dead silence)
        self.smooth = 0.6           # temporal mask smoothing (less warble)
        self.vad_margin_db = 6.0    # frame counts as noise if within this of floor
        self.warmup_frames = 16     # first ~1s always trains (standard seed)
        self.fast_frames = 50       # fast-learn for ~first 3s of noise

    # -- public API --
    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def reset(self) -> None:
        """Forget the learned profile and start training over."""
        self.noise_mag.fill(0)
        self._smooth_gain.fill(1.0)
        self._floor_db = -50.0
        self.learned_frames = 0
        self.total_frames = 0

    @property
    def learned_seconds(self) -> float:
        return self.learned_frames * self.frame_size / max(self.sample_rate, 1)

    @property
    def label(self) -> str:
        state = "ON" if self.enabled else "OFF"
        return f"CLEAN: {state} ({self.learned_seconds:.0f}s learned)"

    # -- training: call on EVERY mic block, enabled or not --
    def learn(self, block: np.ndarray) -> bool:
        """Fold background frames into the noise profile. Returns True if learned."""
        if block.size != self.frame_size:
            return False
        self.total_frames += 1
        x = np.asarray(block, dtype=np.float64)
        rms_db = 20 * np.log10(float(np.sqrt(np.mean(x * x))) + _EPS) \
            if np.any(x) else -100.0

        # Instant attack: the floor is always the quietest seen level.
        if rms_db < self._floor_db:
            self._floor_db = rms_db

        warming = self.total_frames <= self.warmup_frames
        if warming:
            # Fast pull toward whatever the room sounds like at startup,
            # from either direction (quiet init vs loud room or vice versa).
            self._floor_db += (rms_db - self._floor_db) * 0.3
        if warming or rms_db <= self._floor_db + self.vad_margin_db:
            mag = np.abs(np.fft.rfft(x))
            if warming:
                rate = 0.3
            else:
                rate = 0.15 if self.learned_frames < self.fast_frames else 0.02
            self.noise_mag += (mag - self.noise_mag) * rate
            self.learned_frames += 1
            return True

        # Loud frame (speech?): don't pollute the profile, but leak the
        # floor up so a permanently louder background can take over.
        self._floor_db += min((rms_db - self._floor_db) * 0.02, 0.3)
        return False

    # -- cleanup: call on the live output path when enabled --
    def process(self, block: np.ndarray) -> np.ndarray:
        if (not self.enabled or block.size != self.frame_size
                or not np.any(self.noise_mag)):
            return np.asarray(block, dtype=np.float32)
        x = np.asarray(block, dtype=np.float64)
        spectrum = np.fft.rfft(x)
        mag = np.abs(spectrum)
        phase = spectrum / np.maximum(mag, _EPS)

        # Magnitude subtraction: bins dominated by the learned profile
        # get pushed down to a small residual floor.
        clean_mag = np.maximum(mag - self.oversub * self.noise_mag,
                               self.floor_keep * self.noise_mag)
        gain = np.clip(clean_mag / np.maximum(mag, _EPS), 0.0, 1.0)

        # Smooth the mask over time to suppress "musical noise" warble.
        self._smooth_gain += (gain - self._smooth_gain) * (1.0 - self.smooth)
        out = np.fft.irfft(self._smooth_gain * mag * phase, n=self.frame_size)
        return np.clip(out, -1.0, 1.0).astype(np.float32)
