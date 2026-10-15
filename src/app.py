"""Wires audio engine + DSP + UI into the live animation loop."""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from . import config
from . import dsp
from .audio_engine import AudioEngine
from .ui import create_ui


def update(_frame, engine: AudioEngine, ui) -> tuple:
    """FuncAnimation callback. Drains audio, refreshes plots/texts."""

    freqs = ui.fig._analyzer_freqs
    got_audio = engine.drain()
    ui.wave_line.set_ydata(engine.wave_buffer)

    if got_audio and engine.latest_block.size:
        engine.observe_peak()
        rms = dsp.compute_rms(engine.latest_block)
        segment = engine.wave_buffer[-config.FFT_SIZE:]
        spectrum_db = dsp.compute_spectrum(segment, config.FFT_SIZE)
        linear = dsp.compute_linear_spectrum(segment, config.FFT_SIZE)
        ui.fft_line.set_ydata(spectrum_db)

        dominant_hz = dsp.dominant_frequency(linear, freqs)
        rms_dbfs = dsp.rms_to_dbfs(rms)

        ui.rms_value.set_text(f"RMS  {rms_dbfs:,.1f} dBFS")
        ui.frequency_value.set_text(f"DOMINANT FREQ  {dominant_hz:,.1f} Hz")
        ui.peak_value.set_text(f"PEAK HOLD  {engine.peak_hold:.3f}")

        stream_status = (
            engine.last_status
            if engine.last_status != "Initializing microphone"
            else "Streaming"
        )
        ui.status_text.set_text(
            f"Microphone active  ·  {config.SAMPLE_RATE:,} Hz"
            f"  ·  Mono input  ·  {stream_status}"
        )
    else:
        ui.status_text.set_text(
            f"Waiting for microphone audio…  {engine.last_status}"
        )

    return (
        ui.wave_line, ui.fft_line, ui.rms_value,
        ui.frequency_value, ui.peak_value, ui.status_text,
    )


def main() -> None:
    engine = AudioEngine()
    ui = create_ui(engine)
    try:
        with engine.stream():
            animation = FuncAnimation(
                ui.fig, update,
                fargs=(engine, ui),
                interval=config.UPDATE_INTERVAL_MS,
                blit=False,
                cache_frame_data=False,
            )
            ui.fig._sound_analyzer_animation = animation  # keep ref alive
            plt.show()
    except Exception as exc:
        print("Could not start microphone capture:", exc)
        print("Check microphone permissions or select a supported input device.")
