"""Bounded reference-calibrated RGB-only experiment; no AI/cloud/downloads."""
from pathlib import Path
import sys,json,time,threading,subprocess
import numpy as np,cv2,psutil
from PIL import Image,ImageDraw
from test_visual_polish import stable_residual
WORK=Path(__file__).resolve().parent;ROOT=WORK/'reference_detail_test'
INPUT=WORK/'visual_polish_test/original';REF=WORK/'phase8_analysis/tensorpix_decoded';PROXY=WORK/'phase8_analysis/proxy_decoded'
FF=r'E:\ffmpeg\bin\ffmpeg.exe';FP=r'E:\ffmpeg\bin\ffprobe.exe'
TRAIN=[0,20,40,60,80,100];HELD=[10,30,50,70,90,110];SIGMAS=[.7,1.6,4.]
cv2.setNumThreads(8)
def load(p):return np.asarray(Image.open(p).convert('RGB'),np.float32)/255
def luma(x):return x@np.array([.2126,.7152,.0722],np.float32)
def small(x):return np.asarray(Image.fromarray(np.rint(np.clip(x,0,1)*255).astype('uint8')).resize((360,640),Image.Resampling.LANCZOS),np.float32)/255
def features(y,sigmas):return np.stack([y-cv2.GaussianBlur(y,(0,0),sigma) for sigma in sigmas],axis=2)
def save(x,p):Image.fromarray(np.rint(np.clip(x,0,1)*255).astype('uint8')).save(p,compress_level=1)
def apply(rgb,delta):return rgb+np.clip(delta,-rgb.min(axis=2),1-rgb.max(axis=2))[...,None]
def encode(folder,path,w=None,h=None):
    vf=f'scale={w}:{h}:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p' if w else 'scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p'
    subprocess.run([FF,'-hide_banner','-v','error','-n','-framerate','60/1','-start_number','0','-i',str(folder/'frame_%04d.png'),'-frames:v','120','-vf',vf,'-c:v','libx264','-preset','fast','-crf','12','-an','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(path)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
def sheet(i,crop=False):
    if crop:
        images=[Image.open(INPUT/f'frame_{i:04d}.png').crop((284,416,796,928)),Image.open(ROOT/'baseline_native'/f'frame_{i:04d}.png').crop((284,416,796,928)),Image.open(ROOT/'local_native'/f'frame_{i:04d}.png').crop((284,416,796,928))];names=['Original native crop','Strength-matched unsharp','Calibrated local native crop']
    else:
        images=[Image.open(ROOT/'original_sd'/f'frame_{i:04d}.png'),Image.open(PROXY/f'frame_{i:04d}.png'),Image.open(REF/f'frame_{i:04d}.png'),Image.open(ROOT/'baseline_sd'/f'frame_{i:04d}.png'),Image.open(ROOT/'local_sd'/f'frame_{i:04d}.png')];names=['Original native -> 360','Actual TensorPix input','TensorPix reference','Strength-matched unsharp','Local native -> 360']
    w,h=images[0].size;out=Image.new('RGB',(w*len(images),h+36),'#202020');draw=ImageDraw.Draw(out)
    for j,(im,name) in enumerate(zip(images,names)):out.paste(im,(j*w,36));draw.text((j*w+8,10),name,fill='white')
    out.save(ROOT/(f'native_crop_{i:04d}.png' if crop else f'comparison_{i:04d}.png'))
def main():
    ROOT.mkdir(exist_ok=False)
    for key in ['original_sd','baseline_sd','local_sd','baseline_native','local_native']:(ROOT/key).mkdir()
    xs=[];bs=[];ds=[]
    for i in TRAIN:
        src=small(load(INPUT/f'frame_{i:04d}.png'));ref=load(REF/f'frame_{i:04d}.png');y=luma(src);d=luma(ref)-y
        xs.append(features(y,SIGMAS)[::3,::3].reshape(-1,3));bs.append(features(y,[1.])[::3,::3].reshape(-1,1));ds.append(d[::3,::3].ravel())
    x=np.concatenate(xs).astype('float64');b=np.concatenate(bs).astype('float64');d=np.concatenate(ds).astype('float64')
    # Fixed regularized linear gains fitted only on training frames. No exposure/grade term.
    ridge=.001;coef=np.linalg.solve(x.T@x+ridge*np.eye(3),x.T@d);baseline=np.linalg.lstsq(b,d,rcond=None)[0][0]
    limit=float(min(.12,max(.03,np.percentile(np.abs(d),99.5))))
    settings={'train_frames':TRAIN,'heldout_frames':HELD,'source_frames':[740,859],'sigmas_sd_px':SIGMAS,'sigmas_native_px':[s*3 for s in SIGMAS],'gains':coef.tolist(),'ridge':ridge,'baseline_sigma_native_px':3.,'baseline_gain':float(baseline),'delta_limit':limit,'color':'Equal-channel encoded-RGB offset, gamut limited; no tone/exposure/saturation change','temporal':'25% warped previous correction only where bidirectional flow and brightness consistent; source RGB never warped/blended','input_resolution':[1080,1920],'comparison_resolution':[360,640],'frames':120,'fps':'60/1','models':'none','implementation':'CPU, existing OpenCV/NumPy/Pillow; no installation'}
    (ROOT/'settings.json').write_text(json.dumps(settings,indent=2));print(json.dumps(settings,indent=2),flush=True)
    peak=[0];stop=threading.Event()
    def sample():
        proc=psutil.Process()
        while not stop.wait(.05):peak[0]=max(peak[0],proc.memory_info().rss/2**20)
    thread=threading.Thread(target=sample,daemon=True);thread.start();t0=time.perf_counter();prev=prev_y=None;records=[]
    for i in range(120):
        rgb=load(INPUT/f'frame_{i:04d}.png');y=luma(rgb)
        delta=np.zeros_like(y)
        for sigma,gain in zip(SIGMAS,coef):delta+=gain*(y-cv2.GaussianBlur(y,(0,0),sigma*3))
        delta=np.clip(delta,-limit,limit);delta,coverage=stable_residual(delta,prev,y,prev_y);prev,prev_y=delta,y
        out=apply(rgb,delta)
        base=apply(rgb,np.clip(baseline*(y-cv2.GaussianBlur(y,(0,0),3)),-limit,limit))
        osd=small(rgb);lsd=small(out);bsd=small(base)
        save(out,ROOT/'local_native'/f'frame_{i:04d}.png');save(base,ROOT/'baseline_native'/f'frame_{i:04d}.png')
        for key,image in [('original_sd',osd),('local_sd',lsd),('baseline_sd',bsd)]:save(image,ROOT/key/f'frame_{i:04d}.png')
        ref=load(REF/f'frame_{i:04d}.png');target=luma(ref)
        records.append({'index':i,'source_frame':740+i,'heldout':i in HELD,'flow_valid_fraction':coverage,'original_target_luma_mse':float(np.mean((luma(osd)-target)**2)),'local_target_luma_mse':float(np.mean((luma(lsd)-target)**2)),'baseline_target_luma_mse':float(np.mean((luma(bsd)-target)**2)),'local_mean_abs_rgb_delta_levels':float(np.mean(np.abs(lsd-osd))*255)})
        if i%20==0:print(f'Processed {i+1}/120',flush=True)
    elapsed=time.perf_counter()-t0;stop.set();thread.join()
    for i in [30,60,90]:sheet(i);sheet(i,True)
    results={'settings':settings,'processing_wall_seconds_including_png_io':elapsed,'peak_python_rss_mib':peak[0],'gpu_vram':'not applicable: CPU processing; no GPU kernels','frame_metrics':records,'heldout_target_mse':{k:float(np.mean([r[k] for r in records if r['heldout']])) for k in ['original_target_luma_mse','local_target_luma_mse','baseline_target_luma_mse']}}
    (ROOT/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in results.items() if k!='frame_metrics'},indent=2),flush=True)
    for key in ['original_sd','baseline_sd','local_sd','local_native']:encode(ROOT/key,ROOT/f'{key}_60fps.mp4')
    # Equal-size evidence encoded directly from frames, preserving60FPS and frame order.
    args=[FF,'-hide_banner','-v','error','-n']
    for folder in [ROOT/'original_sd',REF,ROOT/'baseline_sd',ROOT/'local_sd']:args+=['-framerate','60/1','-start_number','0','-i',str(folder/'frame_%04d.png')]
    args+=['-filter_complex','[0:v][1:v][2:v][3:v]hstack=inputs=4,scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p[v]','-map','[v]','-frames:v','120','-c:v','libx264','-preset','fast','-crf','12','-an','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(ROOT/'comparison_60fps.mp4')]
    subprocess.run(args,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    probes={}
    for path in ROOT.glob('*.mp4'):
        data=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(path)]));v=data['streams'][0]
        assert int(v['nb_frames'])==120 and v['avg_frame_rate']=='60/1' and abs(float(v['duration'])-2)<.001
        subprocess.run([FF,'-v','error','-xerror','-i',str(path),'-f','null','-'],check=True,creationflags=subprocess.CREATE_NO_WINDOW);probes[path.name]=data
    (ROOT/'output_probes.json').write_text(json.dumps(probes,indent=2));print('All5videos passed120frames/60FPS/2seconds and decode checks.',flush=True)
if __name__=='__main__':main()
