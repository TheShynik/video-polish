"""Phase 6: bounded, non-generative RGB filter comparison. No AI/depth inference."""
from pathlib import Path
import subprocess, json, time, threading
import numpy as np
import cv2
from PIL import Image, ImageDraw
import psutil

ROOT = Path(__file__).resolve().parent / 'visual_polish_test'
SOURCE = Path(r'D:\_Work\VideoToTest\Movie_671.mp4')
FF = r'E:\ffmpeg\bin\ffmpeg.exe'
FP = r'E:\ffmpeg\bin\ffprobe.exe'
START, COUNT, REPRESENTATIVE = 740, 120, 800
NAMES = ['Original', 'Baseline', 'A Material', 'B Volume', 'C Clean', 'D Balanced']
KEYS = ['original', 'baseline', 'a', 'b', 'c', 'd']
cv2.setNumThreads(8)
def call(args):
    subprocess.run(args, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
def read(p):
    return np.asarray(Image.open(p).convert('RGB'), dtype=np.float32) / 255
def gray(rgb):
    return rgb @ np.array([.2126, .7152, .0722], np.float32)
def guided(y, radius, eps):
    size=(radius*2+1, radius*2+1)
    mean=cv2.boxFilter(y,-1,size,borderType=cv2.BORDER_REFLECT)
    var=np.maximum(cv2.boxFilter(y*y,-1,size,borderType=cv2.BORDER_REFLECT)-mean*mean,0)
    a=var/(var+eps)
    b=mean-a*mean
    return cv2.boxFilter(a,-1,size,borderType=cv2.BORDER_REFLECT)*y+cv2.boxFilter(b,-1,size,borderType=cv2.BORDER_REFLECT)
def save(rgb,p):
    Image.fromarray(np.rint(np.clip(rgb,0,1)*255).astype('uint8')).save(p)
def apply_delta(rgb,y,delta):
    # Equal RGB offset preserves encoded-RGB opponent chroma, limited before gamut clipping.
    delta=np.clip(delta, -rgb.min(axis=2), 1-rgb.max(axis=2))
    return rgb+delta[...,None]
def effects(rgb):
    y=gray(rgb)
    fine=guided(y,3,.0009)
    medium=guided(y,14,.0036)
    broad=guided(y,48,.0081)
    # Reject large edges and very dark/bright pixels. This is a numeric gate, not segmentation.
    gx=cv2.Sobel(y,cv2.CV_32F,1,0,ksize=3)/8
    gy=cv2.Sobel(y,cv2.CV_32F,0,1,ksize=3)/8
    gate=np.exp(-(gx*gx+gy*gy)/(.055**2))
    headroom=np.clip(np.minimum(y,1-y)/.12,0,1)
    a=np.clip(.18*(y-fine)+.14*(fine-medium),-.016,.016)*gate*headroom
    b=np.clip(.18*(medium-broad),-.018,.018)*gate*headroom
    # Selective subpixel-scale smoothing only where high-frequency energy is strong.
    smooth=cv2.GaussianBlur(y,(0,0),.55)
    residual=smooth-y
    energy=cv2.GaussianBlur((y-smooth)**2,(0,0),1.2)
    c=np.clip(.32*residual*np.clip(np.sqrt(energy)/.018,0,1),-.010,.010)*gate*headroom
    return y,a,b,c
def stable_residual(current,previous,y,prev_y):
    if previous is None:
        return current,0.
    h,w=y.shape
    small=cv2.resize(y,(w//3,h//3),interpolation=cv2.INTER_AREA)
    old=cv2.resize(prev_y,(w//3,h//3),interpolation=cv2.INTER_AREA)
    flow=cv2.calcOpticalFlowFarneback(small,old,None,.5,3,15,3,5,1.2,0)
    back=cv2.calcOpticalFlowFarneback(old,small,None,.5,3,15,3,5,1.2,0)
    sy,sx=np.mgrid[:small.shape[0],:small.shape[1]].astype('float32')
    bx=cv2.remap(back[...,0],sx+flow[...,0],sy+flow[...,1],cv2.INTER_LINEAR)
    by=cv2.remap(back[...,1],sx+flow[...,0],sy+flow[...,1],cv2.INTER_LINEAR)
    consistency=np.sqrt((flow[...,0]+bx)**2+(flow[...,1]+by)**2)<.4
    full=cv2.resize(flow,(w,h))*3
    yy,xx=np.mgrid[:h,:w].astype('float32')
    mx,my=xx+full[...,0],yy+full[...,1]
    warped_y=cv2.remap(prev_y,mx,my,cv2.INTER_LINEAR)
    valid=(cv2.resize(consistency.astype('float32'),(w,h),interpolation=cv2.INTER_NEAREST)>.5)&(np.abs(y-warped_y)<.025)&(mx>=0)&(my>=0)&(mx<w-1)&(my<h-1)
    warped=cv2.remap(previous,mx,my,cv2.INTER_LINEAR)
    # Only the tiny filter residual is stabilized, never the source RGB content.
    result=np.where(valid,.75*current+.25*warped,current)
    return result,float(np.mean(valid))
def encode(folder,dest):
    call([FF,'-hide_banner','-v','error','-n','-framerate','60/1','-start_number','0','-i',str(folder/'frame_%04d.png'),'-frames:v',str(COUNT),'-vf','scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p','-c:v','libx264','-preset','fast','-crf','12','-an','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(dest)])
def sheet(paths,crop=False):
    tiles=[]
    for name,path in zip(NAMES,paths):
        im=Image.open(path).convert('RGB')
        if crop: im=im.crop((284,416,796,928))
        else: im=im.resize((360,640),Image.Resampling.LANCZOS)
        tile=Image.new('RGB',(im.width,im.height+36),'#202020')
        tile.paste(im,(0,36)); ImageDraw.Draw(tile).text((12,10),name,fill='white')
        tiles.append(tile)
    out=Image.new('RGB',(tiles[0].width*3,tiles[0].height*2),'#202020')
    for i,tile in enumerate(tiles): out.paste(tile,((i%3)*tile.width,(i//3)*tile.height))
    out.save(ROOT/('contact_sheet_crop_1to1.png' if crop else 'contact_sheet_full_frame.png'))
def main():
    ROOT.mkdir(exist_ok=True)
    for key in KEYS: (ROOT/key).mkdir(exist_ok=True)
    meta=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(SOURCE)]))
    (ROOT/'source_probe.json').write_text(json.dumps(meta,indent=2))
    call([FF,'-hide_banner','-v','error','-n','-i',str(SOURCE),'-vf',rf'select=between(n\,{START}\,{START+COUNT-1}),scale=iw:ih:in_color_matrix=bt709:in_range=tv:out_range=full,format=rgb24','-fps_mode','passthrough','-frames:v',str(COUNT),'-start_number','0',str(ROOT/'original'/'frame_%04d.png')])
    peak=[0]; stop=threading.Event()
    def monitor():
        proc=psutil.Process()
        while not stop.wait(.05): peak[0]=max(peak[0],proc.memory_info().rss)
    thread=threading.Thread(target=monitor,daemon=True); thread.start()
    prior=prior_y=None; rows=[]; t0=time.perf_counter()
    timings={'filter_seconds':0.,'temporal_seconds':0.,'png_seconds':0.}
    for i in range(COUNT):
        rgb=read(ROOT/'original'/f'frame_{i:04d}.png')
        t=time.perf_counter(); y,a,b,c=effects(rgb); timings['filter_seconds']+=time.perf_counter()-t
        t=time.perf_counter(); c,coverage=stable_residual(c,prior,y,prior_y); timings['temporal_seconds']+=time.perf_counter()-t
        prior,prior_y=c,y
        baseline_delta=.04*(y-.5)+.30*(y-cv2.GaussianBlur(y,(0,0),1.))
        variants=[apply_delta(rgb,y,baseline_delta),apply_delta(rgb,y,a),apply_delta(rgb,y,b),apply_delta(rgb,y,c),apply_delta(rgb,y,.65*a+.65*b+.75*c)]
        row={'frame':START+i,'flow_valid_fraction':coverage,'variants':{}}
        t=time.perf_counter()
        for key,out in zip(KEYS[1:],variants):
            save(out,ROOT/key/f'frame_{i:04d}.png')
            delta=gray(out)-y
            row['variants'][key]={'mean_luma_delta':float(delta.mean()),'mean_abs_luma_delta':float(np.abs(delta).mean()),'max_abs_luma_delta':float(np.abs(delta).max())}
        timings['png_seconds']+=time.perf_counter()-t; rows.append(row)
        if i%20==0: print(f'Processed {i+1}/{COUNT}',flush=True)
    elapsed=time.perf_counter()-t0; stop.set();thread.join()
    paths=[ROOT/key/f'frame_{REPRESENTATIVE-START:04d}.png' for key in KEYS]
    sheet(paths);sheet(paths,True)
    summary={'source':str(SOURCE),'source_start_frame':START,'frame_count':COUNT,'representative_source_frame':REPRESENTATIVE,'fps':'60/1','size':[1080,1920],'duration_s':COUNT/60,'processor':'CPU; OpenCV 8 threads; no GPU kernels or AI models','processing_wall_seconds':elapsed,'timings':timings,'process_peak_rss_mib':peak[0]/2**20,'audio':'diagnostic clips silent','color_assumption':'source untagged; limited BT709 decode to full encoded RGB; equal RGB offset preserves opponent chroma before quantization; gamut limited','frame_metrics':rows}
    (ROOT/'results.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='frame_metrics'},indent=2),flush=True)
    for key in KEYS:
        encode(ROOT/key,ROOT/f'{key}_60fps.mp4')
    for key in KEYS[2:]:
        # Original / baseline / treatment: full-resolution panels, no spatial scaling.
        call([FF,'-hide_banner','-v','error','-n','-i',str(ROOT/'original_60fps.mp4'),'-i',str(ROOT/'baseline_60fps.mp4'),'-i',str(ROOT/f'{key}_60fps.mp4'),'-filter_complex','[0:v][1:v][2:v]hstack=inputs=3[v]','-map','[v]','-c:v','libx264','-preset','fast','-crf','12','-an','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(ROOT/f'comparison_{key}_60fps.mp4')])
    probes={}
    for p in ROOT.glob('*.mp4'):
        probe=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(p)]))
        stream=probe['streams'][0]
        assert stream['avg_frame_rate']=='60/1' and int(stream['nb_frames'])==COUNT
        call([FF,'-hide_banner','-v','error','-xerror','-i',str(p),'-f','null','-'])
        probes[p.name]=probe
    (ROOT/'output_probes.json').write_text(json.dumps(probes,indent=2))
    print('All ten clips passed FPS/frame-count and full-decode checks.',flush=True)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT,help='Use a fresh directory; existing frames/exports are never overwritten.')
    ROOT=parser.parse_args().output.resolve()
    main()
