"""Protected reproduction wrapper; original numerical pipeline unchanged."""
from pathlib import Path
import argparse,json,hashlib,sys
WORK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(WORK))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    manifest=json.loads((WORK/'stable_local_native/manifest.json').read_text())
    for relative,digest in manifest['files_sha256'].items():
        path=WORK/relative
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=digest:raise RuntimeError('Stable file changed: '+str(path))
    print('Stable code, exact input assets and approved reference SHA256 verified.')
    if args.verify_only:return
    if args.output is None:parser.error('--output must name a fresh directory')
    output=args.output.resolve()
    if output.exists():parser.error('Refusing existing output directory')
    assets=(WORK/'local_native_v1_assets').resolve()
    if output==assets or assets in output.parents:parser.error('Refusing output inside protected stable assets')
    import test_reference_detail as pipeline
    pipeline.ROOT=output
    pipeline.INPUT=assets/'input/native'
    pipeline.REF=assets/'input/tensorpix'
    pipeline.PROXY=assets/'input/proxy'
    pipeline.main()
    generated=json.loads((output/'settings.json').read_text())
    frozen=json.loads((WORK/'stable_local_native/settings.json').read_text())
    if generated!=frozen:raise RuntimeError('Recomputed settings differ from approved version; do not call this a reproduction')
    print('Reproduction settings match approved local-native-v1 exactly.')
if __name__=='__main__':main()
