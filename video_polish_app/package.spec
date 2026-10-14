from pathlib import Path
root=Path(SPECPATH).parent
a=Analysis([str(root/'video_polish_app/app.py')],pathex=[str(root),str(root/'video_polish_app')],
 binaries=[(r'E:\ffmpeg\bin\ffmpeg.exe','ffmpeg'),(r'E:\ffmpeg\bin\ffprobe.exe','ffmpeg')],
 datas=[(str(root/'stable_local_native/settings.json'),'stable_local_native')],
 hiddenimports=[],excludes=['torch','torchvision','matplotlib','scipy'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='VideoPolish',console=False)
coll=COLLECT(exe,a.binaries,a.datas,name='VideoPolish')
