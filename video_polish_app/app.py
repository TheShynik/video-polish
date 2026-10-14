"""Small native Tk desktop app. Worker messages return to the UI thread."""
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
import threading,queue,subprocess,io,json
from pathlib import Path
from PIL import Image,ImageTk
from engine import probe,enhance,FF,FLAGS

class App:
    def __init__(self,root):
        self.root=root;root.title('Video Polish — Local Native');root.geometry('1000x800');root.minsize(760,650)
        self.source=None;self.output=None;self.busy=False;self.cancel=threading.Event();self.messages=queue.Queue();self.playing=False;self.frame_id=0;self.preview_busy=False;self.generation=0
        top=ttk.Frame(root,padding=12);top.pack(fill='x')
        self.pick=ttk.Button(top,text='Choose Video',command=self.choose);self.pick.pack(side='left')
        self.export=ttk.Button(top,text='Enhance → Save MP4',command=self.run,state='disabled');self.export.pack(side='left',padx=12)
        self.stop=ttk.Button(top,text='Cancel',command=self.cancel.set,state='disabled');self.stop.pack(side='left')
        self.info=ttk.Label(root,text='Local Native • Offline',padding=8);self.info.pack(fill='x')
        self.canvas=tk.Label(root,bg='#181818');self.canvas.pack(fill='both',expand=True,padx=12)
        nav=ttk.Frame(root,padding=10);nav.pack(fill='x')
        self.play=ttk.Button(nav,text='▶ Preview',command=self.toggle,state='disabled');self.play.pack(side='left')
        self.view=tk.StringVar(value='Original');self.mode=ttk.Combobox(nav,textvariable=self.view,values=['Original','Result'],state='readonly',width=15);self.mode.pack(side='left',padx=12);self.mode.bind('<<ComboboxSelected>>',lambda e:self.seek())
        self.position=tk.DoubleVar();self.slider=ttk.Scale(nav,from_=0,to=1,variable=self.position);self.slider.pack(side='left',fill='x',expand=True);self.slider.bind('<ButtonRelease-1>',lambda e:self.seek())
        self.progress=ttk.Progressbar(root,maximum=100);self.progress.pack(fill='x',padx=12,pady=8)
        self.status=ttk.Label(root,text='Choose a source MP4. Export: 1920×1920 with padding, original FPS and audio.',padding=10);self.status.pack(fill='x')
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.poll)

    def choose(self):
        path=filedialog.askopenfilename(title='Choose Video',filetypes=[('Video','*.mp4 *.mov *.mkv *.avi'),('All Files','*.*')])
        if not path:return
        try:
            data,v=probe(path)
            self.source=path;self.output=None;self.view.set('Original');self.fps=__import__('fractions').Fraction(v['r_frame_rate']);self.duration=float(v.get('duration',data['format'].get('duration',0)))
            self.playing=False;self.generation+=1;self.slider.configure(to=max(0,self.duration-1/float(self.fps)));self.position.set(0)
            self.info.configure(text=f'{Path(path).name} • {v["width"]}×{v["height"]} • {float(self.fps):g} FPS • {self.duration:.2f} s • Local Native')
            self.export.configure(state='normal');self.play.configure(state='normal');self.seek()
        except Exception as e:messagebox.showerror('Unsupported Video',str(e))

    def seek(self):
        self.playing=False;self.play.configure(text='▶ Preview');self.generation+=1;self.preview()

    def toggle(self):
        if not self.source:return
        self.playing=not self.playing;self.play.configure(text='❚❚ Pause' if self.playing else '▶ Preview')
        if self.playing:self.tick()

    def tick(self):
        if not self.playing:return
        if not self.preview_busy:
            self.position.set((self.position.get()+.2)%max(.2,self.duration));self.preview()
        self.root.after(200,self.tick)

    def preview(self):
        path=self.output if self.view.get()=='Result' else self.source
        if not path:
            self.status.configure(text='Enhance the video first to preview the result.');return
        if self.preview_busy:return
        self.preview_busy=True;generation=self.generation;t=self.position.get()
        def worker():
            try:
                raw=subprocess.check_output([FF,'-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-vf','scale=800:560:force_original_aspect_ratio=decrease','-f','image2pipe','-vcodec','png','pipe:1'],creationflags=FLAGS)
                im=Image.open(io.BytesIO(raw)).convert('RGB');self.messages.put(('preview',generation,im))
            except Exception as e:self.messages.put(('preview_error',generation,str(e)))
        threading.Thread(target=worker,daemon=True).start()

    def run(self):
        if not self.source or self.busy:return
        dest=filedialog.asksaveasfilename(title='Save Enhanced MP4',defaultextension='.mp4',initialfile=Path(self.source).stem+'_local_native.mp4',filetypes=[('MP4','*.mp4')])
        if not dest:return
        if Path(dest).exists():messagebox.showerror('New Output File','Choose a new filename. Existing files are never overwritten.');return
        self.busy=True;self.playing=False;self.cancel.clear();self.pick.configure(state='disabled');self.export.configure(state='disabled');self.stop.configure(state='normal');self.progress['value']=0
        self.status.configure(text='Processing with Local Native. This may take several minutes…')
        def worker():
            try:
                r=enhance(self.source,dest,lambda n,total,secs:self.messages.put(('progress',n,total,secs)),self.cancel)
                self.messages.put(('done',dest,r))
            except Exception as e:self.messages.put(('error',str(e)))
        threading.Thread(target=worker,daemon=True).start()

    def poll(self):
        try:
            while True:
                item=self.messages.get_nowait();kind=item[0]
                if kind in ('preview','preview_error'):
                    self.preview_busy=False
                    if item[1]==self.generation:
                        if kind=='preview':self.photo=ImageTk.PhotoImage(item[2]);self.canvas.configure(image=self.photo)
                        else:self.status.configure(text='Preview error: '+item[2])
                    else:self.preview()
                elif kind=='progress':
                    _,n,total,secs=item;self.progress['value']=100*n/total if total else 0;self.status.configure(text=f'Frames: {n} / {total or "?"} • {secs:.0f} s • source unchanged')
                elif kind in ('done','error'):
                    self.busy=False;self.pick.configure(state='normal');self.export.configure(state='normal');self.stop.configure(state='disabled')
                    if kind=='done':
                        self.output=item[1];self.progress['value']=100;self.status.configure(text='Done: '+self.output);self.view.set('Result');self.position.set(0);self.seek();messagebox.showinfo('Done','MP4 saved:\n'+self.output)
                    else:self.status.configure(text=item[1]);messagebox.showerror('Processing Stopped',item[1])
        except queue.Empty:pass
        self.root.after(100,self.poll)

    def close(self):
        if self.busy:
            self.cancel.set();messagebox.showinfo('Cancel','Wait for processing to stop, then close the window.');return
        self.root.destroy()

if __name__=='__main__':
    root=tk.Tk();ttk.Style().theme_use('clam');App(root);root.mainloop()
