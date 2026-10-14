# Reference-calibrated detail experiment — actual results

**Completed; partial approximation, not a reproduction of TensorPix.** The local output visibly strengthens existing texture/edges while keeping objects and scene layout recognizable. However, it does not match TensorPix's stronger contour/facet treatment and does not demonstrate better materials/lighting beyond ordinary sharpening. A strength-matched single-radius unsharp control matches the target slightly better numerically. **No case for integrating this multiscale treatment into Video Polish is established.** Stop after this bounded test.

## Controlled test and settings

Original source `D:\_Work\VideoToTest\Movie_671.mp4`, frames **740–859**, **120 frames, 60 FPS, 2 seconds**. Reused the verified full-resolution original RGB frames in `visual_polish_test/original`. Processing at **1080×1920**, preserving full portrait composition; no AI model, replacement content, spatial warp of source RGB, frame interpolation or global grade. Existing isolated `.venv_phase7` tools only, no installs/downloads/cloud/UI.

Calibration uses six source frames **740/760/780/800/820/840** and TensorPix at corresponding indices, at 360×640. Six held-out frames **750/770/790/810/830/850** are excluded from fitting. Representative source800 is a training frame; the supplied source830 three-way image is **held out**. Native originals are resized with the same Pillow Lanczos route used for local outputs, so primary native/control comparisons have equal dimensions and identical presentation resampling. The actual uploaded TensorPix SD input is shown separately because it contains different sampling/compression history.

Luminance `Y=.2126R+.7152G+.0722B` in encoded RGB 0–1. Fixed correction:

`delta = 1.4128677*(Y−Gaussian(Y,2.1px)) + .04411087*(Y−Gaussian(Y,4.8px)) − .03137465*(Y−Gaussian(Y,12px))`.

Gains are a ridge regression (`lambda=.001`) from the six training frames; radius scale transferred from SD by factor3. No brightness/exposure/saturation term. Delta bounded **±.12** (30.6 levels), learned 99.5th-percentile target bound capped at .12. Equal offset added to all RGB channels, limited to original per-pixel gamut headroom. This preserves encoded opponent chroma before rounding, not identical perceived saturation.

Temporal correction-only stabilization: 75% current +25% previous flow-warped correction where input-derived bidirectional Farneback error <.4 px at 360×640 and native luminance residual <.025. Source RGB itself is **never warped or blended**. First frame has spatial correction only. No semantic masks, new shadows or geometry assumptions.

Baseline: ordinary `delta=.95507039*(Y−Gaussian(Y,3px))`, same correction/gamut bounds, fitted on the same training frames. It is **target-calibrated**, not a deliberately weak baseline. No temporal smoothing in the baseline. Exact [settings](reference_detail_test/settings.json), [processing script](test_reference_detail.py), [analysis script](analyze_reference_detail_test.py).

## Measured execution and comparison

CPU processing, 8 OpenCV threads; **no GPU kernels**, VRAM not applicable. All 120 frames/branches processed in **142.69 seconds**, including PNG reading/writing. Peak sampled processing Python RAM **267.0 MiB**. Calibration, MP4 encoding and later analysis excluded. No processing errors/OOM. [Run measurements](reference_detail_test/results.json), [log](reference_detail_run.log).

| Held-out luminance match to TensorPix | MSE (0–1 luma) | Reduction versus original |
|---|---:|---:|
| Original | 0.00146080 | — |
| Local multiscale | 0.00096825 | 33.7% |
| Single-radius unsharp | 0.00092843 | 36.4% |

**Matching error is not perceptual quality or a percentage of TensorPix reproduced.** A lower error can reflect sharpness, and does not establish rich materials or correct lighting. Baseline beats multiscale by about4.1% relative MSE; multiscale has no demonstrated advantage.

| Whole-sequence measurement, equal360×640 | Original | TensorPix | Unsharp | Local |
|---|---:|---:|---:|---:|
| Mean edge gradient | 0.02096 | 0.02956 | 0.02530 | 0.02467 |
| Highpass RMS sigma1 | 0.02776 | 0.05240 | 0.03657 | 0.03641 |
| Local contrast RMS sigma4 | 0.06142 | 0.08596 | 0.07131 | 0.06995 |
| Shared-flow temporal luma RMS | 0.01705 | 0.03161 | 0.02189 | 0.02172 |

Local edge gradient rises about18% over native-original common-size view, while TensorPix rises about41%. Local highpass rises about31%, versus89% for TensorPix. Thus there is a substantial remaining visual/detail gap. Lower local temporal residual than TensorPix is **not evidence of better stability**, because local processing is weaker. Flow-valid area **80.8%**; excluded occlusions/hard boundaries, sharpened edge interpolation and only two seconds limit conclusions. No flicker-free claim.

## Visual assessment and color limits

Inspected source800 and held-out source830 common-size views, native512×512 crops and consecutive samples. Main object positions, geometry, animation and original water pattern remain recognizable; no hallucinated objects/material replacements. Sand grain, leaf/facet boundaries and posts become somewhat more defined. Narrow bright/dark rims and accentuated existing noise are visible at native scale. Water detail is retained rather than replaced, but no new material response, contact shading or credible light transport appears. This is **conventional detail enhancement**, not a demonstrated premium-render engine.

Mean local RGB change at common-size view is about **−1.15 levels per channel**, mean absolute change **1.79/255**. The six held-out native PNGs preserve opponent-chroma differences within **1 level**; verified [native color checks](reference_detail_test/native_color_checks.json). After 360×640 Lanczos resampling, isolated maximum opponent-chroma difference reaches **38 levels**, despite the small global mean, so comparison-scale colors cannot be called pixel-identical. Resampling/clipping of sharpened saturated boundaries is a limitation, not something hidden by a color grade. Perceived palette stays recognizable in inspected images. Video chroma subsampling introduces further lossy changes.

## Outputs and conclusion

- [Held-out three-way PNG](reference_detail_test/heldout_three_way.png): original / TensorPix / local, source830; same360×640 panels.
- [Five-way source800 PNG](reference_detail_test/comparison_0060.png), [five-way held-out source830 PNG](reference_detail_test/comparison_0090.png): original / actual TensorPix input / TensorPix / target-matched unsharp / local.
- [Native source800 crop](reference_detail_test/native_crop_0060.png), [native held-out source830 crop](reference_detail_test/native_crop_0090.png): original / unsharp / local, same512×512 crop.
- [Four-way comparison MP4](reference_detail_test/comparison_60fps.mp4): original / TensorPix / unsharp / local, same360×640 panels, overall1440×640.
- [Local full native MP4](reference_detail_test/local_native_60fps.mp4), [local common-size MP4](reference_detail_test/local_sd_60fps.mp4), [original common-size MP4](reference_detail_test/original_sd_60fps.mp4), [baseline MP4](reference_detail_test/baseline_sd_60fps.mp4).
- [Consecutive-frame review](reference_detail_test/consecutive_frame_review.png), [metrics](reference_detail_test/quality_metrics.json), full PNG sequences and [output probes](reference_detail_test/output_probes.json).

All five videos validated **120frames /60FPS /2seconds** and full decode. Silent diagnostic clips, same frame ordering; original audio not exported. H.264 CRF12/fast/yuv420p, explicit limited BT.709; source mastering tags unknown. No full-length export.

Reproduction from this workspace: `.venv_phase7\Scripts\python.exe test_reference_detail.py`, then `.venv_phase7\Scripts\python.exe analyze_reference_detail_test.py`. The runner refuses an existing `reference_detail_test` directory; choose/change the output root in a separate copy if repeating, preserving this evidence. No hidden fallback, new AI model or retuned follow-up.

**Verdict: bounded test complete; only partial conventional sharpening match.** Do not describe it as equivalent to TensorPix or as a new rendering/lighting engine. This specific multiscale approach does not beat the ordinary unsharp control, so further escalation of its strength is not justified by the result. No UI/integration or additional model test started.
