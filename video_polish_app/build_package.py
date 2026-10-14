"""Build portable directory, retain notices and create a ZIP. Run in .venv_package."""
import sys,subprocess,json,shutil,hashlib,importlib.metadata,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'video_polish_app/outputs/package-v1'
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(OUT/'dist'),'--workpath',str(OUT/'build'),str(ROOT/'video_polish_app/package.spec')],check=True)
    folder=OUT/'dist/VideoPolish';licenses=folder/'LICENSES';licenses.mkdir()
    for dist in importlib.metadata.distributions():
        for file in dist.files or []:
            if any(part.lower().startswith(('license','copying','notice')) for part in file.parts):
                src=Path(dist.locate_file(file))
                if src.is_file():
                    dst=licenses/dist.metadata['Name']/str(file);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    for name in ['LICENSE','README.txt']:shutil.copy2(Path(r'E:\ffmpeg')/name,licenses/('FFmpeg-'+name))
    shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',licenses/'Python-LICENSE.txt')
    for name in ['PORTABLE_README.txt','THIRD_PARTY.md']:shutil.copy2(ROOT/'video_polish_app'/name,folder/name)
    versions={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    (folder/'build_versions.json').write_text(json.dumps(versions,indent=2))
    (OUT/'requirements_build_locked.txt').write_text('\n'.join(f'{k}=={v}' for k,v in sorted(versions.items()))+'\n')
    manifest={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
    (folder/'SHA256.json').write_text(json.dumps(manifest,indent=2))
    archive=OUT/'VideoPolish-Windows-x64-v1.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in folder.rglob('*'):
            if p.is_file():z.write(p,str(Path('VideoPolish')/p.relative_to(folder)))
    print(str(archive),flush=True)
if __name__=='__main__':main()
