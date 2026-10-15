"""Matplotlib UI construction. No audio logic here."""

from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from . import config


@dataclass
class AnalyzerUI:
    fig: object
    ax_wave: object
    ax_fft: object
    wave_line: object
    fft_line: object
    rms_value: object
    frequency_value: object
    peak_value: object
    status_text: object
    reset_button: object
    hear_button: object
    voice_button: object
    rec_button: object
    save_button: object
    mode_text: object


def build_axes(freqs: np.ndarray, time_axis: np.ndarray, wave_buffer: np.ndarray):
    config.apply_style(plt)

    fig = plt.figure(figsize=(13, 8), facecolor=config.BG)
    fig.canvas.manager.set_window_title("SOUND / Live Audio Analyzer")
    fig.subplots_adjust(left=0.065, right=0.965, top=0.83, bottom=0.12, hspace=0.42)

    fig.text(0.065, 0.94, "SOUND", fontsize=22, fontweight="bold", color=config.TEXT)
    fig.text(
        0.065, 0.895,
        "LIVE AUDIO ANALYZER   /   MICROPHONE INPUT",
        fontsize=9, color=config.MUTED,
    )
    fig.text(0.965, 0.93, "●  LIVE", fontsize=10, color=config.GREEN, ha="right")

    ax_wave = fig.add_axes([0.065, 0.51, 0.9, 0.29])
    ax_fft = fig.add_axes([0.065, 0.17, 0.9, 0.25])

    for ax in (ax_wave, ax_fft):
        ax.set_facecolor(config.PANEL)
        for side in ax.spines.values():
            side.set_color(config.GRID)
        ax.grid(True, color=config.GRID, linewidth=0.7, alpha=0.75)
        ax.tick_params(length=0, pad=7)

    fig.text(0.075, 0.815, "WAVEFORM", fontsize=9, fontweight="bold", color=config.CYAN)
    fig.text(
        0.075, 0.435, "FREQUENCY SPECTRUM  /  FFT",
        fontsize=9, fontweight="bold", color=config.PURPLE,
    )

    wave_line, = ax_wave.plot(time_axis, wave_buffer, color=config.CYAN, linewidth=1.35)
    ax_wave.set_xlim(-config.DISPLAY_SECONDS, 0)
    ax_wave.set_ylim(-1.05, 1.05)
    ax_wave.set_xlabel("TIME (s)")
    ax_wave.set_ylabel("AMPLITUDE")

    fft_line, = ax_fft.plot(freqs, np.zeros_like(freqs), color=config.PURPLE, linewidth=1.35)
    ax_fft.fill_between(freqs, -100, np.zeros_like(freqs), color=config.PURPLE, alpha=0.035)
    ax_fft.set_xlim(0, config.SAMPLE_RATE / 2)
    ax_fft.set_ylim(-100, 5)
    ax_fft.set_xlabel("FREQUENCY (Hz)")
    ax_fft.set_ylabel("LEVEL (dB, RELATIVE)")

    rms_value = fig.text(0.065, 0.855, "RMS  —", fontsize=10, color=config.TEXT)
    frequency_value = fig.text(0.31, 0.855, "DOMINANT FREQ  —", fontsize=10, color=config.TEXT)
    peak_value = fig.text(0.61, 0.855, "PEAK HOLD  —", fontsize=10, color=config.TEXT)
    status_text = fig.text(
        0.065, 0.105, "Waiting for microphone audio…", fontsize=9, color=config.MUTED
    )
    mode_text = fig.text(
        0.965, 0.105, "MONITOR OFF  ·  VOICE OFF  ·  READY",
        fontsize=9, color=config.MUTED, ha="right",
    )

    def _make_button(rect, label):
        bax = fig.add_axes(rect)
        bax.set_facecolor(config.PANEL)
        btn = Button(bax, label, color=config.PANEL, hovercolor=config.GRID)
        btn.label.set_color(config.TEXT)
        btn.label.set_fontsize(9)
        return btn

    hear_button = _make_button([0.065, 0.035, 0.13, 0.05], "HEARING: OFF")
    voice_button = _make_button([0.21, 0.035, 0.15, 0.05], "VOICE: OFF")
    rec_button = _make_button([0.375, 0.035, 0.11, 0.05], "● REC")
    save_button = _make_button([0.50, 0.035, 0.12, 0.05], "SAVE WAV")

    button_ax = fig.add_axes([0.81, 0.035, 0.155, 0.05])
    button_ax.set_facecolor(config.PANEL)
    reset_button = Button(button_ax, "RESET PEAK", color=config.PANEL, hovercolor=config.GRID)
    reset_button.label.set_color(config.TEXT)
    reset_button.label.set_fontsize(9)

    return (fig, ax_wave, ax_fft, wave_line, fft_line, rms_value,
            frequency_value, peak_value, status_text, reset_button,
            hear_button, voice_button, rec_button, save_button, mode_text)


def create_ui(engine) -> AnalyzerUI:
    time_axis = (
        np.arange(len(engine.wave_buffer)) / engine.sample_rate
        - config.DISPLAY_SECONDS
    )
    freqs = np.fft.rfftfreq(config.FFT_SIZE, d=1 / config.SAMPLE_RATE)
    parts = build_axes(freqs, time_axis, engine.wave_buffer)
    (fig, ax_wave, ax_fft, wave_line, fft_line, rms_value,
     frequency_value, peak_value, status_text, reset_button,
     hear_button, voice_button, rec_button, save_button, mode_text) = parts
    reset_button.on_clicked(lambda _event: engine.reset_peak())
    # Stash freqs on figure for the animation loop without globals.
    fig._analyzer_freqs = freqs
    return AnalyzerUI(
        fig=fig, ax_wave=ax_wave, ax_fft=ax_fft,
        wave_line=wave_line, fft_line=fft_line,
        rms_value=rms_value, frequency_value=frequency_value,
        peak_value=peak_value, status_text=status_text,
        reset_button=reset_button, hear_button=hear_button,
        voice_button=voice_button, rec_button=rec_button,
        save_button=save_button, mode_text=mode_text,
    )
