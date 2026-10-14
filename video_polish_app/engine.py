"""Streaming wrapper around frozen Local Native numerics; no calibration or models."""
import sys,json,subprocess,tempfile,time,os
from fractions import Fraction
from pathlib import Path
import numpy as np
import cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_reference_detail import luma,apply
from test_visual_polish import stable_residual
ROOT=Path(sys._MEIPASS) if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
SETTINGS=json.loads((ROOT/'stable_local_native/settings.json').read_text())
BIN=ROOT/'ffmpeg' if getattr(sys,'frozen',False) else Path(r'E:\ffmpeg\bin')
FF=str(BIN/'ffmpeg.exe'); FP=str(BIN/'ffprobe.exe')
FLAGS=subprocess.CREATE_NO_WINDOW

def probe(path):
    data=json.loads(subprocess.check_output([FP,'-v','error','-show_streams','-show_format','-of','json',str(path)],creationflags=FLAGS))
    v=next(s for s in data['streams'] if s['codec_type']=='video')
    if v.get('color_transfer') in ('smpte2084','arib-std-b67'):raise ValueError('HDR is not supported by this SDR pipeline.')
    if v.get('sample_aspect_ratio','1:1') not in ('1:1','N/A'):raise ValueError('Non-square pixels are not supported yet.')
    if any(s.get('rotation',0) for s in v.get('side_data_list',[])):raise ValueError('Rotated video metadata is not supported yet.')
    rate=v['r_frame_rate']
    if rate=='0/0' or v.get('avg_frame_rate')!=rate:raise ValueError('Use a constant-frame-rate source; variable FPS is not supported yet.')
    if float(Fraction(rate))<=0:raise ValueError('Invalid frame rate.')
    return data,v

def process_frame(rgb,previous=None,prev_y=None):
    y=luma(rgb);delta=np.zeros_like(y)
    for sigma,gain in zip(SETTINGS['sigmas_native_px'],SETTINGS['gains']):delta+=gain*(y-cv2.GaussianBlur(y,(0,0),sigma))
    delta=np.clip(delta,-SETTINGS['delta_limit'],SETTINGS['delta_limit'])
    delta,coverage=stable_residual(delta,previous,y,prev_y)
    return np.rint(np.clip(apply(rgb,delta),0,1)*255).astype('uint8'),delta,y

def enhance(source,destination,progress=lambda *a:None,cancel=None,max_frames=None,start_frame=0):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if destination.exists() or source==destination:raise ValueError('Choose a new output filename; existing files are never overwritten.')
    data,v=probe(source);w,h=v['width'],v['height'];fps=v['r_frame_rate'];total=int(v.get('nb_frames',0));t0=time.perf_counter()
    # Average rate alone cannot establish constant cadence (B-frame packets may be unordered).
    timestamps=subprocess.check_output([FP,'-v','error','-select_streams','v:0','-show_entries','packet=pts_time','-of','csv=p=0',str(source)],creationflags=FLAGS).decode()
    pts=sorted(float(line.split(',')[0]) for line in timestamps.splitlines() if line and line.split(',')[0]!='N/A')
    interval=1/float(Fraction(fps))
    if len(pts)<2 or any(abs((b-a)-interval)>max(.0001,interval*.01) for a,b in zip(pts,pts[1:])):raise ValueError('Variable or discontinuous frame timestamps are not supported; no output was created.')
    if cancel and cancel.is_set():raise InterruptedError('Cancelled.')
    if min(w,h)<12:raise ValueError('Video dimensions are too small.')
    # Exact baseline limited BT709 decode for untagged input; honor explicit SDR matrix/range.
    matrix=v.get('color_space','bt709');matrix=matrix if matrix in ('bt709','smpte170m','bt470bg') else 'bt709'
    rng='pc' if v.get('color_range')=='pc' else 'tv'
    selection=f'select=gte(n\\,{start_frame}),' if start_frame else ''
    decoder_args=[FF,'-v','error','-noautorotate','-i',str(source),'-an','-vf',selection+f'scale=iw:ih:in_color_matrix={matrix}:in_range={rng}:out_range=full,format=rgb24','-fps_mode','passthrough']
    if max_frames:decoder_args+=['-frames:v',str(max_frames)]
    decoder_args+=['-f','rawvideo','pipe:1']
    # Fit within square, never stretch. For baseline portrait no resizing occurs.
    scale='scale=1920:1920:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,pad=1920:1920:(ow-iw)/2:(oh-ih)/2:black,scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p'
    count=0;prev=prev_y=None
    with tempfile.TemporaryDirectory(prefix='video-polish-') as tmp:
        movie=Path(tmp)/'processed.mp4'
        with open(Path(tmp)/'decode.log','w+b') as de,open(Path(tmp)/'encode.log','w+b') as ee:
            dec=subprocess.Popen(decoder_args,stdout=subprocess.PIPE,stderr=de,creationflags=FLAGS)
            enc=subprocess.Popen([FF,'-v','error','-n','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate',fps,'-i','pipe:0','-vf',scale,'-c:v','libx264','-preset','fast','-crf','12','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE,stderr=ee,creationflags=FLAGS)
            try:
                while True:
                    if cancel and cancel.is_set():raise InterruptedError('Cancelled; source unchanged.')
                    raw=dec.stdout.read(w*h*3)
                    if not raw:break
                    if len(raw)!=w*h*3:raise RuntimeError('Incomplete decoded frame.')
                    rgb=np.frombuffer(raw,np.uint8).reshape(h,w,3).astype('float32')/255
                    out,prev,prev_y=process_frame(rgb,prev,prev_y);enc.stdin.write(out.tobytes());count+=1
                    progress(count,min(total-start_frame,max_frames) if max_frames else total,time.perf_counter()-t0)
                enc.stdin.close()
                if dec.wait()!=0 or enc.wait()!=0:
                    de.seek(0);ee.seek(0);raise RuntimeError((de.read()+ee.read()).decode(errors='replace'))
            finally:
                for p in (dec,enc):
                    if p.poll() is None:p.kill()
                    p.wait()
            if not count:raise RuntimeError('No video frames decoded.')
        # Original audio is stream copied when MP4-compatible, otherwise error is explicit.
        stage=destination.with_name(destination.stem+'.partial.mp4')
        if stage.exists():raise ValueError('Temporary output already exists: '+str(stage))
        try:
            args=[FF,'-v','error','-n','-i',str(movie)]
            if start_frame:args+=['-ss',str(start_frame/float(__import__('fractions').Fraction(fps)))]
            args+=['-i',str(source),'-map','0:v:0','-map','1:a:0?','-c','copy','-t',str(count/float(__import__('fractions').Fraction(fps))),'-movflags','+faststart',str(stage)]
            subprocess.run(args,check=True,creationflags=FLAGS,capture_output=True)
            _,ov=probe(stage)
            if ov['width']!=1920 or ov['height']!=1920 or ov['avg_frame_rate']!=fps or int(ov['nb_frames'])!=count:raise RuntimeError('Export validation failed.')
            subprocess.run([FF,'-v','error','-xerror','-i',str(stage),'-f','null','-'],check=True,creationflags=FLAGS,capture_output=True)
            if cancel and cancel.is_set():raise InterruptedError('Cancelled.')
            if destination.exists():raise ValueError('Output filename was created while processing.')
            os.rename(stage,destination)
        finally:
            if stage.exists():stage.unlink()
    record={'source':str(source),'output':str(destination),'frames':count,'fps':fps,'output_size':[1920,1920],'seconds':time.perf_counter()-t0,'settings':SETTINGS,'processor':'CPU; unchanged Local Native numerics','color_assumption':f'{matrix}/{rng} SDR; output BT709 limited','audio':'first source audio stream copied; no audio if absent'}
    destination.with_suffix('.settings.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record
