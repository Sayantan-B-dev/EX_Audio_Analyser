"""DSP helpers: RMS, spectrum, dominant frequency. Pure functions, no I/O."""

import numpy as np


def compute_rms(block: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(block, dtype=np.float64))))


def rms_to_dbfs(rms: float) -> float:
    return 20 * np.log10(max(rms, 1e-8))


def compute_spectrum(segment: np.ndarray, fft_size: int) -> np.ndarray:
    """Return spectrum in dB (relative), mirroring original analyzer logic."""
    if len(segment) < fft_size:
        segment = np.pad(segment, (fft_size - len(segment), 0))
    segment = segment.astype(np.float64)
    segment -= np.mean(segment)
    window = np.hanning(fft_size)
    spectrum = np.abs(np.fft.rfft(segment * window))
    spectrum_db = 20 * np.log10(
        np.maximum(spectrum / max(np.sum(window), 1), 1e-8)
    )
    return spectrum_db


def compute_linear_spectrum(segment: np.ndarray, fft_size: int) -> np.ndarray:
    """Linear magnitude spectrum, used for dominant-frequency picking."""
    if len(segment) < fft_size:
        segment = np.pad(segment, (fft_size - len(segment), 0))
    segment = segment.astype(np.float64)
    segment -= np.mean(segment)
    window = np.hanning(fft_size)
    return np.abs(np.fft.rfft(segment * window))


def dominant_frequency(linear_spectrum: np.ndarray, freqs: np.ndarray) -> float:
    if linear_spectrum.size <= 1:
        return 0.0
    return float(freqs[np.argmax(linear_spectrum[1:]) + 1])
