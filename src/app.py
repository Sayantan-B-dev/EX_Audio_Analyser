"""Wires analyzer + live hearing + voice changer + recorder into one loop."""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from . import config
from . import dsp
from .audio_engine import AudioEngine
from .monitor import LiveMonitor
from .voice import VoiceChanger
from .recorder import Recorder
from .pipeline import LivePipeline
from .ui import create_ui


def _mode_line(monitor: LiveMonitor, voice: VoiceChanger, recorder: Recorder,
               engine: AudioEngine) -> str:
    mon = f"MONITOR {monitor.label}"
    vox = f"VOICE {voice.name.upper()}"
    if recorder.recording:
        rec = f"● REC {recorder.blocks} blocks"
    elif recorder.has_audio():
        rec = f"READY ({recorder.blocks} blocks, S to save)"
    else:
        rec = "READY"
    return f"{mon}  ·  {vox}  ·  {rec}"


def update(_frame, engine: AudioEngine, ui, monitor, voice, recorder) -> tuple:
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

    ui.mode_text.set_text(_mode_line(monitor, voice, recorder, engine))

    return (
        ui.wave_line, ui.fft_line, ui.rms_value,
        ui.frequency_value, ui.peak_value, ui.status_text, ui.mode_text,
    )


def _attach_controls(ui, monitor: LiveMonitor, voice: VoiceChanger,
                     recorder: Recorder, engine: AudioEngine) -> None:
    """Wire buttons + keyboard shortcuts to the live modules."""

    def refresh_buttons() -> None:
        ui.hear_button.label.set_text(
            f"HEARING: {'ON' if monitor.enabled else 'OFF'}")
        ui.voice_button.label.set_text(f"VOICE: {voice.name.upper()}")
        ui.rec_button.label.set_text(
            "■ STOP" if recorder.recording else "● REC")
        ui.mode_text.set_text(_mode_line(monitor, voice, recorder, engine))

    def toggle_hearing(_event=None) -> None:
        monitor.toggle()
        print(f"Hearing {'ON' if monitor.enabled else 'OFF'}")
        refresh_buttons()

    def cycle_voice(_event=None) -> None:
        name = voice.cycle()
        print(f"Voice effect: {name}")
        refresh_buttons()

    def toggle_rec(_event=None) -> None:
        if recorder.toggle():
            print("Recording started…")
        else:
            print(f"Recording stopped ({recorder.blocks} blocks). Press SAVE.")
        refresh_buttons()

    def save_wav(_event=None) -> None:
        path = recorder.save(config.RECORDINGS_DIR, config.SAMPLE_RATE,
                             effect=voice.name)
        if path:
            print(f"Saved: {path}")
        else:
            print("Nothing to save — press REC first.")
        refresh_buttons()

    ui.hear_button.on_clicked(toggle_hearing)
    ui.voice_button.on_clicked(cycle_voice)
    ui.rec_button.on_clicked(toggle_rec)
    ui.save_button.on_clicked(save_wav)

    def on_key(event) -> None:
        key = (event.key or "").lower()
        if key == "h":
            toggle_hearing()
        elif key == "v":
            cycle_voice()
        elif key == "r":
            toggle_rec()
        elif key == "s":
            save_wav()

    ui.fig.canvas.mpl_connect("key_press_event", on_key)
    refresh_buttons()


def main() -> None:
    engine = AudioEngine()
    monitor = LiveMonitor(enabled=config.MONITOR_DEFAULT_ON,
                          gain=config.MONITOR_GAIN)
    voice = VoiceChanger(effect=config.VOICE_DEFAULT,
                         sample_rate=config.SAMPLE_RATE)
    recorder = Recorder()
    pipeline = LivePipeline(engine, monitor, voice, recorder)
    ui = create_ui(engine)
    _attach_controls(ui, monitor, voice, recorder, engine)

    print("Keys: H hearing · V voice fx · R record · S save WAV")
    try:
        with pipeline.open_stream():
            animation = FuncAnimation(
                ui.fig, update,
                fargs=(engine, ui, monitor, voice, recorder),
                interval=config.UPDATE_INTERVAL_MS,
                blit=False,
                cache_frame_data=False,
            )
            ui.fig._sound_analyzer_animation = animation  # keep ref alive
            plt.show()
    except Exception as exc:
        print("Could not start microphone capture:", exc)
        print("Check microphone permissions or select a supported input device.")
