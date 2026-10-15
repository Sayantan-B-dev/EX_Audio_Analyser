# AGENT.md - Working rules for this repo

These rules apply to every contributor, human or agent. Follow them for
every change, from a one-line fix to a full feature.

## 1. Project layout

- The project root holds only `main.py` plus docs and config
  (`README.md`, `AGENT.md`, `requirements.txt`, `.gitignore`).
- All code lives in `src/`, one module per feature. Never add a second
  runnable script at the root.
- `main.py` stays a thin entry point: it imports `main` from `src.app`
  and calls it. No logic in `main.py`.
- Inside `src/`, use relative imports (`from . import config`).
  Absolute imports of sibling modules are not allowed.

## 2. Module responsibilities

- `config.py`: constants and defaults only. No I/O, no DSP.
- `dsp.py`: pure functions only. No state, no devices, no files.
- `audio_engine.py`: mic capture and analysis buffers only.
- `voice.py`, `monitor.py`, `denoise.py`, `recorder.py`: one feature
  each, with a small public API (`process`, `toggle`, `append`, `save`).
- `pipeline.py`: the only place that touches the duplex callback. New
  live audio features hook in here, nowhere else.
- `ui.py`: figure and widgets only. No audio logic, no file writes.
- `app.py`: wiring only (controls, animation loop, `main()`).
- Signal order is fixed: analysis, recorder (dry), denoise, voice,
  monitor gain, speakers. The recorder always stores the dry mic signal.

## 3. Code style

- Comments must be short and factual: one line explaining why, not what.
  No comment essays, no commented-out code blocks, no TODO comments left
  behind. Remove a TODO in the same change that resolves it.
- No emojis anywhere: not in code, comments, docs, commit messages or
  file names.
- No em-dash or en-dash characters anywhere. Use a plain hyphen (-) or
  restructure the sentence. This covers code, docs and commits.
- Console output must be ASCII-safe. The Windows console cannot print
  characters such as the bullet or block glyphs, so `print()` calls use
  plain ASCII only. (UI labels inside matplotlib may use richer glyphs.)
- Keep lines at a readable width (about 100 columns max).
- No new third-party dependencies without explicit approval. Prefer the
  standard library plus the existing numpy, sounddevice and matplotlib.

## 4. Audio thread discipline

- The sounddevice callback must never block, allocate heavily, print,
  or raise. Wrap each stage in try/except and fall back to silence.
- Stateful DSP (delay lines, phase counters, gain smoothing) must keep
  working across consecutive blocks with no clicks on toggle.
- `learn()` style background training runs on every block, independent
  of any on/off flag. Flags only gate `process()`.

## 5. Docs

- Any user-facing change (button, key, behavior, config option, file
  output) must update `README.md` in the same commit series: controls
  table, structure tree or relevant section.
- Docs follow the same style rules: no emojis, no em-dash or en-dash,
  ASCII-safe code samples.

## 6. Verification before every commit

Run at minimum, with the headless backend so no window opens:

```bash
python -c "import src.config, src.dsp, src.audio_engine, src.ui, src.app"
python -c "import main"
```

For audio behavior changes, add a synthetic check with
`MPLBACKEND=Agg`: feed generated blocks (sine, noise) through the new
code and assert shape, dtype and the expected effect (for example
suppression level or correlation). Do not commit code that has not been
executed.

## 7. Commit rules

- Group work into a short series of commits, at most 10 per task. One
  commit per logical step (core, feature, wiring, docs).
- Each commit must leave the tree importable and runnable. Never commit
  a state where `import main` fails.
- Messages are short, imperative and specific, for example
  "Add live hearing toggle to pipeline". No emojis, no AI tags, no
  "Co-Authored-By" trailers, no "Generated with" footers, no links.
- Never commit generated or local files: `__pycache__/`, `*.pyc`,
  `recordings/`, virtualenvs, `.env` files, IDE folders. They are
  gitignored; delete strays before committing.
- Stage explicitly (`git add <paths>`), review `git status` and
  `git diff --stat`, then commit. Do not use `git add -A` blindly.
- Only commit, amend or push when asked. Never rewrite history that has
  already been pushed. Never change git identity config to commit; use
  the identity already configured in the repo.

## 8. Adding a feature (checklist)

1. Create `src/<name>.py` with a minimal class and NumPy-only logic.
2. Add defaults to `src/config.py` if the feature needs tuning.
3. Hook the audio path in `src/pipeline.py` behind try/except.
4. Add the button and status readout in `src/ui.py`.
5. Wire the button, key shortcut and mode line in `src/app.py`.
6. Update the README controls table and structure section.
7. Verify headless, then commit the feature as one commit.
