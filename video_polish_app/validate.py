"""Real baseline parity and short export check; no model/UI changes."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from engine import ROOT,process_frame,enhance

def main():
    previous=prev_y=None;diffs=[]
    for i in range(8):
        rgb=np.asarray(Image.open(ROOT/f'local_native_v1_assets/input/native/frame_{i:04d}.png').convert('RGB'),np.float32)/255
        out,previous,prev_y=process_frame(rgb,previous,prev_y)
        reference=np.asarray(Image.open(ROOT/f'reference_detail_test/local_native/frame_{i:04d}.png'))
        diffs.append(int(np.abs(out.astype(int)-reference.astype(int)).max()))
    print('Eight consecutive baseline frame maximum pixel differences:',diffs,flush=True)
    assert max(diffs)==0
    folder=ROOT/'video_polish_app/outputs';folder.mkdir(exist_ok=True)
    result=enhance(Path(r'D:\_Work\VideoToTest\Movie_671.mp4'),folder/'smoke_8frames.mp4',max_frames=8,start_frame=740)
    (folder/'validation.json').write_text(json.dumps({'baseline_pixel_max_differences':diffs,'export':result},indent=2))
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
