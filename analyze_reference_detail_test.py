"""Post-test diagnostics only; same shared flow for all equal-size branches."""
from pathlib import Path
import json
import numpy as np,cv2
from PIL import Image,ImageDraw
from test_reference_detail import ROOT,REF,load,luma
def main():
    folders=[ROOT/'original_sd',REF,ROOT/'baseline_sd',ROOT/'local_sd'];keys=['original','tensorpix','baseline','local']
    spatial={key:[] for key in keys};temporal={key:[] for key in keys};changes=[];previous=None;valid_areas=[]
    cv2.setNumThreads(8)
    for i in range(120):
        images=[load(folder/f'frame_{i:04d}.png') for folder in folders];ys=[luma(image) for image in images]
        for key,y in zip(keys,ys):
            gx=cv2.Sobel(y,cv2.CV_32F,1,0)/8;gy=cv2.Sobel(y,cv2.CV_32F,0,1)/8
            hp=y-cv2.GaussianBlur(y,(0,0),1);mid=y-cv2.GaussianBlur(y,(0,0),4)
            spatial[key].append({'mean_gradient':float(np.sqrt(gx*gx+gy*gy).mean()),'highpass_rms':float(np.sqrt(np.mean(hp*hp))),'local_contrast_rms':float(np.sqrt(np.mean(mid*mid)))})
        diff=images[3]-images[0];changes.append({'mean_rgb_delta_levels':(diff.mean(axis=(0,1))*255).tolist(),'mean_abs_rgb_delta_levels':float(np.abs(diff).mean()*255),'opponent_chroma_max_abs_levels':float(np.abs(diff[...,:2]-diff[...,2,None]).max()*255)})
        if previous is not None:
            flow=cv2.calcOpticalFlowFarneback(ys[0],previous[0],None,.5,3,15,3,5,1.2,0);back=cv2.calcOpticalFlowFarneback(previous[0],ys[0],None,.5,3,15,3,5,1.2,0)
            yy,xx=np.mgrid[:640,:360].astype('float32');mx,my=xx+flow[...,0],yy+flow[...,1]
            bx=cv2.remap(back[...,0],mx,my,cv2.INTER_LINEAR);by=cv2.remap(back[...,1],mx,my,cv2.INTER_LINEAR);old=cv2.remap(previous[0],mx,my,cv2.INTER_LINEAR)
            valid=(np.sqrt((flow[...,0]+bx)**2+(flow[...,1]+by)**2)<.75)&(np.abs(ys[0]-old)<.05)&(mx>1)&(my>1)&(mx<359)&(my<639)
            valid_areas.append(float(valid.mean()))
            for key,y,p in zip(keys,ys,previous):
                error=y-cv2.remap(p,mx,my,cv2.INTER_LINEAR);temporal[key].append(float(np.sqrt(np.mean(error[valid]**2))))
        previous=ys
    results={'spatial_means':{key:{field:float(np.mean([row[field] for row in rows])) for field in rows[0]} for key,rows in spatial.items()},'temporal_luma_rms_means':{key:float(np.mean(rows)) for key,rows in temporal.items()},'flow_valid_fraction':float(np.mean(valid_areas)),'local_mean_rgb_delta_levels':np.mean([r['mean_rgb_delta_levels'] for r in changes],axis=0).tolist(),'local_mean_abs_rgb_delta_levels':float(np.mean([r['mean_abs_rgb_delta_levels'] for r in changes])),'local_max_opponent_chroma_delta_levels':max(r['opponent_chroma_max_abs_levels'] for r in changes),'caution':'Metrics measure change not perceptual quality. Sharpness increases subpixel warp residual. RGB ratios/perceived saturation not guaranteed identical; opponent chroma can change during quantization/resizing.'}
    (ROOT/'quality_metrics.json').write_text(json.dumps(results,indent=2))
    # Consecutive frames around representative, all same sizes, for detailed temporal review.
    indices=[58,59,60,61,62];out=Image.new('RGB',(360*5,672*3),'#202020');draw=ImageDraw.Draw(out)
    for row,key,folder in [(0,'original',folders[0]),(1,'TensorPix',folders[1]),(2,'local',folders[3])]:
        for col,i in enumerate(indices):
            out.paste(Image.open(folder/f'frame_{i:04d}.png'),(col*360,row*672+32));draw.text((col*360+8,row*672+10),f'{key} / source {740+i}',fill='white')
    out.save(ROOT/'consecutive_frame_review.png');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
