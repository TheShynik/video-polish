# Local desktop wrapper validation

- Tk window instantiated and controls rendered without errors.
- Eight consecutive preserved native input PNGs processed with frozen settings: all eight output frames have maximum absolute pixel difference **0** against approved Local Native PNGs. This checks Gaussian filtering, gamut limiting and temporal state reuse before video compression.
- Eight frames of the original Unity MP4 (starting at source frame740) exported successfully: H264,1920×1920,60/1 FPS,8frames,video duration .133333seconds. First source AAC stream copied; packet rounding gives audio duration .146667seconds. Processing/export/full-decode validation took6.30seconds on CPU. No GPU/model dependency added.
- Exported frame inspected: portrait composition retained, black side padding, no stretch. Full FFmpeg decode completed without errors.
- Stable reproduction manifest verification passed after app creation; main/tag and approved MP4 remain unchanged.

This is a short functional smoke test, not full-film quality/performance validation. Preview is sampled/silent. Native Windows UI is a local Tk prototype launched through the existing isolated Python environment, not a portable EXE installer. Render Polish is absent.
