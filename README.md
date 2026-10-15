# SOUND - Live Audio Analyzer

A real-time microphone analyzer and live audio playground. It plots the
waveform and frequency spectrum of the mic input, and adds live hearing,
a voice changer, one-press recording with WAV export, and a self-training
noise cleanup stage. Everything is modular: the project root holds only
`main.py`, each feature lives in its own module under `src/`.

## Features

- **Live analyzer**: scrolling waveform plus FFT spectrum with RMS level,
  dominant frequency readout and peak hold.
- **Live hearing**: route the microphone to the speakers with adjustable gain.
- **Voice changer**: cycle through OFF, DEEP, CHIPMUNK, ROBOT and ECHO,
  applied live to the monitored output.
- **Record and export**: capture mic takes in RAM, save them as WAV files
  under `recordings/` with one click.
- **Noise cleanup**: an adaptive spectral gate that profiles the room in
  the background. The longer the app runs, the sharper the profile gets
  and the better the suppression. Toggle with the CLEAN button.

## Requirements

- Python 3.10 or newer
- A working microphone (and speakers for the hearing path)
- PortAudio runtime for `sounddevice`:
  - Windows: bundled with the wheel, nothing extra needed
  - macOS: `brew install portaudio`
  - Linux: `sudo apt install libportaudio2` (Debian/Ubuntu)

## Install

```bash
pip install -r requirements.txt
```

Dependencies are intentionally small: `numpy`, `sounddevice`, `matplotlib`.
WAV export uses only the Python standard library.

## Run

```bash
python main.py
```

Grant microphone permission when the OS asks. If no output device is
available the app falls back to mic-only mode and disables hearing.

## Controls

Buttons sit in the bottom bar, each has a keyboard shortcut:

| Button     | Key | Action                                              |
|------------|-----|-----------------------------------------------------|
| HEARING    | H   | Toggle mic-to-speaker monitoring on/off             |
| VOICE      | V   | Cycle voice effect: OFF, DEEP, CHIPMUNK, ROBOT, ECHO |
| CLEAN      | N   | Toggle adaptive noise cleanup on/off                |
| REC        | R   | Start/stop recording the dry mic signal             |
| SAVE WAV   | S   | Export the take to `recordings/`                    |
| RESET PEAK | -   | Clear the peak-hold readout                         |

The status line at the bottom right always shows the live state, for
example monitor gain, active voice effect, noise training time and the
recording state.

## Project structure

```text
audio/
  main.py              Single entry point: python main.py
  requirements.txt     numpy, sounddevice, matplotlib
  README.md            This file
  AGENT.md             Working rules for contributors and agents
  src/
    __init__.py        Package marker
    config.py          Sample rate, block size, theme, feature defaults
    dsp.py             Pure DSP helpers: RMS, spectrum, dominant frequency
    audio_engine.py    Mic capture, rolling buffers, peak tracking
    voice.py           VoiceChanger: pitch and modulation effects
    monitor.py         LiveMonitor: hearing on/off plus gain
    denoise.py         AdaptiveDenoiser: self-training noise cleanup
    recorder.py        Recorder: RAM takes plus WAV export
    pipeline.py        LivePipeline: one duplex callback for all of the above
    ui.py              Matplotlib figure, plots, buttons, status lines
    app.py             Wiring: controls, animation loop, main()
```

Signal flow in the duplex callback:

```text
mic block -> analysis queue -> recorder (dry) -> denoise.learn (always)
          -> denoise.process (if CLEAN on) -> voice fx -> monitor gain
          -> speakers
```

The analyzer plots and the recorder always use the dry mic signal. Cleanup
and voice effects only shape what you hear on the speakers.

## Noise cleanup training

The denoiser keeps a running estimate of the room spectrum:

1. Every mic block is observed, whether CLEAN is on or off.
2. Quiet frames (close to the tracked background floor) update the profile
   with a moving average: fast for the first seconds, slow refinement after.
3. Loud frames (speech) are rejected so they never pollute the profile.
4. The CLEAN button label and the status line show the learned background
   time, for example `CLEAN: ON (21s learned)`.

Practical tips: let the app listen to room silence for a few seconds after
launch before enabling CLEAN. Suppression is strongest on steady sounds
such as fan hum and hiss (around 18 dB once settled in testing). If the
room changes completely, restart the app to retrain from scratch.

## Recordings

Saves go to `recordings/rec_<timestamp>_voice-<effect>.wav`, 16-bit mono
at the configured sample rate. The directory is created automatically and
is ignored by git, so takes never end up in commits.

## Troubleshooting

- **No microphone / permission denied**: check the OS privacy settings and
  that an input device is selected, then restart the app.
- **No sound from hearing**: press HEARING (or H) to enable monitoring and
  check the system output volume. Some Bluetooth setups expose no duplex
  stream; the app then runs mic-only by design.
- **sounddevice install fails**: install the PortAudio runtime for your OS
  (see Requirements) and retry `pip install -r requirements.txt`.
- **High latency or stutter**: close other audio apps, or raise `BLOCK_SIZE`
  in `src/config.py` (larger blocks trade latency for stability).

## Configuration

All tunables live in `src/config.py`: sample rate, block size, display
window, FFT size, UI theme, monitor gain and feature defaults. The denoiser
keeps its own DSP tuning constants at the top of `src/denoise.py`.
