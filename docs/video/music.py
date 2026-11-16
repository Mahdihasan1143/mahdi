import numpy as np, wave
SR=44100; DUR=31.0; BPM=110; beat=60/BPM
N=int(SR*DUR); L=np.zeros(N); R=np.zeros(N)
def mid(m): return 440*2**((m-69)/12)
def add(sig,t0,pan=0.0,gain=1.0):
    i=int(t0*SR)
    if i>=N: return
    s=sig[:N-i]*gain; L[i:i+len(s)]+=s*(1-max(pan,0)); R[i:i+len(s)]+=s*(1+min(pan,0))
def env(n,a,d,s,r_):
    e=np.ones(n); a=int(a*SR); d=int(d*SR); r_=int(r_*SR)
    e[:a]=np.linspace(0,1,max(a,1)); e[a:a+d]=np.linspace(1,s,max(d,1)); e[a+d:]=s
    if r_>0: e[-r_:]*=np.linspace(1,0,r_)
    return e
def tone(f,dur,kind='saw',a=.01,d=.1,s=.6,r_=.1,det=0.0):
    n=int(dur*SR); t=np.arange(n)/SR
    if kind=='sine': w=np.sin(2*np.pi*f*t)
    elif kind=='tri': w=2/np.pi*np.arcsin(np.sin(2*np.pi*f*t))
    else:
        w=sum((2*((f*(1+k)*t)%1)-1) for k in (-det,0,det))/3
        w=np.convolve(w,np.ones(12)/12,mode='same')
    return w*env(n,a,d,s,r_)
def kick():
    n=int(.28*SR); t=np.arange(n)/SR; f=50+110*np.exp(-t*28)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)
def hat(o=False):
    n=int((.18 if o else .05)*SR); x=np.random.randn(n); x=np.diff(x,prepend=0)
    return x*np.exp(-np.arange(n)/SR*(18 if o else 70))*.5
def clap():
    n=int(.2*SR); x=np.random.randn(n); return np.convolve(x,np.ones(4)/4,mode='same')*np.exp(-np.arange(n)/SR*22)*.7
chords=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]
bass=[45,41,36,43]
bar=4*beat
for b in range(int(DUR/bar)+1):
    T=b*bar; c=chords[b%4]
    lvl=0.35 if T<6.5 else (1.0 if T<24.5 else 1.15)
    for m in c: add(tone(mid(m),bar+.3,'saw',.4,.3,.7,.4,.003),T,0.0,0.07*lvl)
    if T>=3.0:
        seq=[c[0]+12,c[1]+12,c[2]+12,c[1]+12,c[2]+12,c[1]+12,c[0]+24,c[1]+12]
        for k,m in enumerate(seq):
            add(tone(mid(m),.25,'tri',.004,.12,.1,.08),T+k*beat/2,(-.3 if k%2 else .3),0.16*lvl)
    if T>=6.4:
        for k in range(4): add(tone(mid(bass[b%4]),beat*.9,'sine',.01,.1,.8,.1),T+k*beat,0,0.3*lvl)
        for k in range(4):
            add(kick(),T+k*beat,0,0.55*lvl); add(hat(),T+k*beat+beat/2,.2,0.12*lvl)
        add(clap(),T+beat,0,0.25*lvl); add(clap(),T+3*beat,0,0.25*lvl)
    elif T>=3.0:
        add(kick(),T,0,0.25)
n=int(2.0*SR); t=np.arange(n)/SR; x=np.random.randn(n); x=np.convolve(x,np.ones(8)/8,mode='same')*(t/2)**2*.25
add(x,23.4,0,1.0)
n=int(1.6*SR); t=np.arange(n)/SR; imp=(np.sin(2*np.pi*55*t)*np.exp(-t*3)+np.random.randn(n)*np.exp(-t*12)*.4)
add(imp,27.0,0,.7)
for m in [57,60,64,69]: add(tone(mid(m),4.0,'saw',.02,.5,.6,1.5,.003),27.0,0,0.08)
fi=int(.6*SR); fo=int(1.6*SR)
for ch in (L,R):
    ch[:fi]*=np.linspace(0,1,fi); ch[-fo:]*=np.linspace(1,0,fo)
m=np.stack([L,R],1); m/=np.max(np.abs(m))*1.08
with wave.open('music.wav','wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((m*32767).astype('<i2').tobytes())
print('ok')
