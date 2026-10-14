# Video Polish — Local Native desktop prototype

Portable build: `outputs/package-v1/VideoPolish-Windows-x64-v1.zip`. Extract the entire folder and open `VideoPolish.exe`; `_internal` must remain beside it. The package includes its own Python runtime and FFmpeg, and processing requires no network. Read `THIRD_PARTY.md` before redistribution: full corresponding source for all bundled FFmpeg dependencies has not been assembled, so redistribution licensing completeness is unresolved.

Build on Windows x64 with Python3.12.14: create a NEW isolated environment, install `requirements_build_locked.txt`, then run `python video_polish_app/build_package.py`. The script refuses an existing package-v1 output directory. It reads existing FFmpeg binaries from `E:\ffmpeg\bin` and packages their unmodified files, stable settings, licenses, dependency versions and SHA256 manifest. No existing inference environment is modified. Artifacts/build logs remain outside Git; source and build pins are committed.

Packaged EXE validation: launched independently from Windows TEMP, Tk initialized and the original video was processed using bundled FFmpeg into an eight-frame1920×1920/60FPS MP4 with audio; full-decode check passed, exit0,7.96seconds. Tested on this Windows11 machine; a separate clean machine has not been tested. The executable is unsigned.

Double-click `Start Video Polish.cmd` in this directory. Uses existing isolated `.venv_phase7`; no installation, model downloads, global Python changes or GPU inference. Not yet a packaged standalone executable.

1. Choose an SDR constant-FPS video.
2. Use the slider or Preview to inspect it. Preview is silent and sampled at up to 5 FPS, not a real-time playback benchmark. Export retains source FPS.
3. Click Enhance → save MP4 and choose a NEW filename. Source/existing outputs are never overwritten.
4. After completion select Result for preview. MP4 opens in any Windows video player; a sibling settings JSON records processing settings and time.

Export: 1920×1920, aspect-preserving fit/padding, H264 CRF12, source constant FPS; first audio stream is copied without re-encoding when MP4-compatible. Unsupported audio produces an explicit export error. HDR, variable FPS, rotated metadata and non-square pixels are rejected. Source untagged color assumes limited BT709 like the approved baseline; explicit SDR matrix/range is honored. No tone mapping. This wrapper is intended for the existing 1080×1920 SDR Unity source; other resolutions use the same fixed pixel-scale filter, with no claimed visual validation.

Frozen Local Native gains/sigmas/limit are read from stable settings. Exactly the approved per-frame Gaussian correction, gamut limiting and temporal residual helper are reused. No TensorPix calibration, experimental Render Polish or AI model is applied. Original scripts and stable tag are unchanged. Temporal state starts from the first frame of the selected input, so a full movie frame is not expected to be bit-identical to a standalone segment starting with reset state.

Processing streams one RGB frame at a time; temporary encoded video is held on disk in Windows TEMP then cleaned. Cancel operates between decoded frames; output is published only after frame/FPS/dimension validation and full FFmpeg decode. Large videos can take considerable CPU time and temporary disk space. No resume support. Preview has no before/after overlay; Original/Result toggle uses the same time position.
