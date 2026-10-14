"""One-time snapshot of already approved code/settings/media; no inference/install."""
from pathlib import Path
import shutil,json,hashlib,subprocess,sys
WORK=Path(__file__).resolve().parents[1];DOC=WORK/'stable_local_native';ASSETS=WORK/'local_native_v1_assets'
ASSETS.mkdir(exist_ok=False)
for original,dest in [(WORK/'visual_polish_test/original',ASSETS/'input/native'),(WORK/'phase8_analysis/tensorpix_decoded',ASSETS/'input/tensorpix'),(WORK/'phase8_analysis/proxy_decoded',ASSETS/'input/proxy')]:
    dest.mkdir(parents=True)
    for p in sorted(original.glob('frame_*.png')):shutil.copy2(p,dest/p.name)
    assert len(list(dest.glob('frame_*.png')))==120
(ASSETS/'reference').mkdir()
shutil.copy2(WORK/'reference_detail_test/local_native_60fps.mp4',ASSETS/'reference/local_native_60fps.mp4')
for name in ['settings.json','results.json','quality_metrics.json','native_color_checks.json','output_probes.json']:
    shutil.copy2(WORK/'reference_detail_test'/name,DOC/name)
freeze=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True)
(DOC/'installed_versions_full.txt').write_text(freeze,encoding='utf-8')
files=[WORK/'test_reference_detail.py',WORK/'test_visual_polish.py',WORK/'analyze_reference_detail_test.py',DOC/'settings.json',DOC/'requirements_runtime.txt']+list(ASSETS.rglob('*.png'))+list(ASSETS.rglob('*.mp4'))
manifest={'tag':'local-native-v1','approval':'User-approved local_native_60fps.mp4; snapshot2026-10-14','python':sys.version,'models':'none; CPU conventional RGB processing','assets_directory':str(ASSETS),'source_mp4':r'D:\_Work\VideoToTest\Movie_671.mp4','tensorpix_reference_mp4':r'D:\_Sett\2026\Week_42\TensorPix - original_sd_proxy_360x640_60fps.mp4','original_result':str(WORK/'reference_detail_test/local_native_60fps.mp4'),'preserved_reference':str(ASSETS/'reference/local_native_60fps.mp4'),'other_model_locations':['phase7_test/RealBasicVSR.pth','phase7_test/RealESRGAN_x4plus.pth','model_backends','depth_guided_test','lightavideo_test','gainres_test','seedvr_test'],'files_sha256':{}}
for p in files:
    with p.open('rb') as f:manifest['files_sha256'][p.relative_to(WORK).as_posix()]=hashlib.file_digest(f,'sha256').hexdigest()
(DOC/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Preserved360 exact input PNGs and approved reference separately from Git.')
print('Approved reference SHA256:',manifest['files_sha256']['local_native_v1_assets/reference/local_native_60fps.mp4'])
