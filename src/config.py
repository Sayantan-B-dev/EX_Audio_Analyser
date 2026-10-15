"""Central configuration: audio parameters, UI theme, matplotlib style."""

BG = "#0b1020"
PANEL = "#121a2b"
GRID = "#263247"
TEXT = "#e7edf7"
MUTED = "#8b9bb4"
CYAN = "#48d7e8"
PURPLE = "#a78bfa"
GREEN = "#5ee0a0"

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
DISPLAY_SECONDS = 2
FFT_SIZE = 4096
UPDATE_INTERVAL_MS = 50

AUDIO_QUEUE_SIZE = 32

# Advanced live features
RECORDINGS_DIR = "recordings"
MONITOR_GAIN = 1.0
MONITOR_DEFAULT_ON = False
VOICE_DEFAULT = "off"
DENOISE_DEFAULT_ON = False


def apply_style(plt) -> None:
    """Apply global matplotlib theme. Takes plt module to avoid import cycle."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "text.color": TEXT,
        "axes.labelcolor": MUTED,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.edgecolor": GRID,
        "figure.facecolor": BG,
        "axes.facecolor": PANEL,
    })
