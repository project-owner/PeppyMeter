# Windows Audio and Meter Controls Update

## Summary

This update adds Windows system playback capture and interactive controls to the standalone PeppyMeter window. Existing non-Windows named-pipe behavior remains available. No third-party dependency was added for the menu or keyboard controls; Windows loopback capture uses the `soundcard` package.

## Windows system playback capture

- The `loopback` data source records audio from the current default Windows playback device through WASAPI loopback.
- On Windows, the existing `type = pipe` configuration is automatically mapped to `loopback`. Other platforms retain the `pipe` source and its existing behavior.
- The recorder captures stereo floating-point samples at 48 kHz. Per-channel RMS levels are converted to the meter's configured range using a -60 to 0 dBFS scale, then passed through the existing channel and smoothing logic.
- Missing `soundcard` installations and recorder/device failures leave the source silent and log an actionable error instead of terminating the application.
- Changing the Windows default playback device requires restarting PeppyMeter so the capture recorder can bind to the new device.

Install the capture dependency in the same Python 3 environment used to launch PeppyMeter:

```powershell
py -3 -m pip install soundcard
```

## Resolution and skin controls

The right-click menu contains these actions:

| Menu item | Behavior |
| --- | --- |
| Switch resolution | Loads the selected `320x240`, `480x320`, `800x480`, or `1280x400` skin configuration and resizes the Pygame window |
| Random skin now | Chooses one skin from the active resolution for a one-time change |
| Timed random skin (20 seconds) | Toggles automatic random skin changes at the configured interval |
| Previous / next skin | Moves through the active resolution's skin list and wraps at either end |

The window also supports keyboard control while focused:

| Key | Behavior |
| --- | --- |
| Up | Move to the next resolution in the order listed above, wrapping to the first |
| Down | Move to the previous resolution, wrapping to the last |
| Left | Select the previous skin in the current resolution |
| Right | Select the next skin in the current resolution |

Manual previous/next skin changes disable timed random switching. A one-time random change leaves the timer setting unchanged. Resolution changes preserve the timer setting and keep the existing audio data source object active. If a skin configuration cannot be loaded, PeppyMeter restores the previous configuration and window mode.

## Launching on Windows

Run `start_peppymeter.cmd` from Explorer or a command prompt. It switches to the project directory, invokes the Python 3 launcher when available, and falls back to `python` on `PATH`. To launch manually, use `py -3 peppymeter.py` from the project directory.

## Validation

The repository test suite was run with:

```powershell
python -m pytest -q
```

Result: **20 passed**. Coverage includes Windows source selection and loopback sample conversion, menu layout and drawing, resolution configuration loading, audio source reuse, random/manual skin behavior, and keyboard shortcut cycling. The tests use simulated audio devices and a Pygame surface; they do not replace a manual check against a live Windows playback device and display window.
