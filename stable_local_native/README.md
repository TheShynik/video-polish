# Approved stable version: local-native-v1

The user approved `reference_detail_test/local_native_60fps.mp4` on 2026-10-14. This snapshot preserves that working RGB-only pipeline irrespective of earlier quality assessments. No AI model is used. Original numerical scripts are unchanged; `reproduce.py` only verifies hashes and redirects inputs/outputs.

## Code, settings and dependencies

Git tracks the exact root processing script, its `test_visual_polish.py` temporal helper, analysis script, approved `settings.json`, measured results, output probes, full installed-version record and this reproduction wrapper. Python 3.12.14; required runtime packages are pinned in `requirements_runtime.txt`. The full `.venv_phase7` package snapshot also records Torch/MMCV and other packages already present, although this approved pipeline does not import/use them. No GPU model/checkpoint is required.

Native Gaussian sigmas: 2.1/4.8/12 px; gains 1.4128677007851675/.044110865057794484/−.03137465144174198; correction bound ±.12; equal-channel gamut-limited offset;25% flow-warped previous correction only where consistent. Full calibration, held-out frames, dimensions, FPS, color and export settings are in settings/code. Output120frames,1080×1920,60FPS,2seconds,silent. Preserve encoded BT709 color assumptions and exact PNG inputs.

## Assets outside Git

- Approved original output: `D:\_Work\EnhanceTool\reference_detail_test\local_native_60fps.mp4`.
- Separate preserved copy: `D:\_Work\EnhanceTool\local_native_v1_assets\reference\local_native_60fps.mp4`.
- Exact native original PNGs: `local_native_v1_assets\input\native` (120).
- Exact decoded TensorPix calibration/reference PNGs: `local_native_v1_assets\input\tensorpix` (120).
- Exact uploaded proxy decoded PNGs: `local_native_v1_assets\input\proxy` (120).
- Original Unity MP4: `D:\_Work\VideoToTest\Movie_671.mp4`.
- TensorPix MP4: `D:\_Sett\2026\Week_42\TensorPix - original_sd_proxy_360x640_60fps.mp4`.
- Existing model weights/environments remain under their original ignored experiment directories; `manifest.json` lists locations. None is needed by local-native-v1.

All360 snapshot input files, reference video and processing-source hashes are in `manifest.json`. Neither videos, images, checkpoints, virtual environments nor nested upstream model repositories are committed. Git alone is not a backup of these assets: copy `local_native_v1_assets` with the repository when moving/backing up the project. Existing environments and original experimental outputs remain untouched.

## Verification and safe reproduction

From `D:\_Work\EnhanceTool`:

```powershell
& .\.venv_phase7\Scripts\python.exe stable_local_native/reproduce.py --verify-only
& .\.venv_phase7\Scripts\python.exe stable_local_native/reproduce.py --output D:\_Work\EnhanceTool\local_native_v1_reproduction
```

The wrapper refuses changed snapshot/source hashes, existing output directories and writes into the protected asset directory. It verifies recalibrated settings equal the frozen approved settings. Reproduction is not run merely to create this snapshot. On another machine use Python3.12.14, create a new isolated venv, install only `requirements_runtime.txt`, restore the snapshot assets and use the same FFmpeg/FFprobe versions/binaries documented in `ffmpeg_versions.txt`.

## Branch policy

`main` and annotated tag `local-native-v1` identify the stable snapshot. Future experiments must use `experiments/after-local-native-v1` or a new branch based on the tag. Do not move/replace the tag or write into stable asset directories. Use fresh experiment output folders and dedicated environments. No Render Polish work is included in this preservation task.

```powershell
git switch experiments/after-local-native-v1
# Or create a separate future branch from the stable tag:
git switch -c experiments/new-experiment local-native-v1
```
