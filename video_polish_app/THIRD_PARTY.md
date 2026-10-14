# Third-party components

This package includes Python (PSF license), Tcl/Tk (permissive license), NumPy (BSD), Pillow (HPND), OpenCV/opencv-python (Apache-2.0 plus third-party notices), psutil (BSD), and the PyInstaller bootloader (GPL exception permits bundled applications). Collected wheel license/notice files and Python license are included in LICENSES. Tcl/Tk license files are included in the runtime tree where supplied by the Python distribution.

FFmpeg and FFprobe are separate unmodified Gyan binaries: `2026-10-08-git-ec420ba161-essentials_build`, GPLv3 build with x264 and other external libraries. GPL license and original build README (external library versions) are included. Sources/build locations:

- https://www.gyan.dev/ffmpeg/builds/ (original build and library details)
- https://github.com/FFmpeg/FFmpeg/tree/ec420ba161 (exact FFmpeg revision)
- https://ffmpeg.org/legal.html (distribution requirements)
- https://github.com/opencv/opencv-python (wheel build and third-party dependencies)
- https://github.com/numpy/numpy/tree/v1.26.4
- https://github.com/python-pillow/Pillow/tree/10.3.0
- https://github.com/giampaolo/psutil/tree/release-6.1.1
- https://www.python.org/downloads/source/
- https://pyinstaller.org/en/stable/license.html

No proprietary enhancement models or weights are included. Video Polish source is preserved in the owner's private repository; it has not been assigned a public open-source license. Third-party components retain their own licenses.

Source links and notices are NOT a claim that this ZIP contains complete corresponding source for every statically linked FFmpeg dependency. Before public or commercial binary distribution, arrange equivalent access to exact corresponding third-party source/build materials. This package is a local prototype; licensing completeness for redistribution has not been certified.
