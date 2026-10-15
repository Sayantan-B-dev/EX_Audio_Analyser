# TODO - planned improvements (not implemented yet)

## Export dialog

- [ ] SAVE opens a browse dialog to pick the destination folder instead of
  the fixed `recordings/` directory.
- [ ] SAVE lets the user rename the file. Keep the current
  `rec_<timestamp>_voice-<effect>.wav` pattern as the suggested default.
- [ ] Fall back to the automatic `recordings/` path when the dialog is
  cancelled or unavailable (headless environments).
- [ ] Confirm before overwriting an existing file with the same name.

## Wet export (final hearing render)

- [ ] Add an option to export the processed chain (denoise + voice effect +
  monitor gain), exactly as heard on the speakers, instead of only the dry
  mic signal.
- [ ] Offer a dry/wet choice at save time (two buttons or a toggle), with
  dry remaining the default so originals are always safe.
- [ ] Include the active effect and CLEAN state in the wet file name, for
  example `rec_<timestamp>_wet-<effect>-clean.wav`.
- [ ] Keep the recorder thread-safe for both taps (dry tap for analysis,
  wet tap after the monitor stage).

## Small export extras

- [ ] "Open folder" action after a successful save.
- [ ] Recording timer in the status line while REC is active.
- [ ] Maximum take length guard with a warning before RAM grows too large.
