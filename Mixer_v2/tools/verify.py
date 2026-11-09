#!/usr/bin/env python3
"""DC/AC nodal analysis of Xcopper's resolved nets; geometry and assembly audit.
No third party dependencies. Linear op amps, finite DC gain, no saturation model.
The nonlinear LED branch is excluded from signal analysis and checked structurally.
"""
import cmath, itertools, json, math, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'validation/netlist.json').read_text())['parts']
D=json.loads((ROOT/'validation/layout.json').read_text())
def pins(p):return {v['number']:v['net']['name'] if v['net'] else None for v in p['pins']}
def val(s):
    s=s.split()[0]
    m=re.fullmatch(r'(\d+(?:\.\d+)?)([KkMmRrupn]?)(\d*)',s)
    assert m,s
    a,u,b=m.groups();return float(a+('.'+b if b else ''))*{'':1,'R':1,'r':1,'K':1e3,'k':1e3,'M':1e6,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12}[u]
res=[];caps=[];amps=[];switches=[]
for p in P:
    r=p['reference'];n=pins(p);c=p['component']
    if r.startswith(('M_LED_DRIVE.','R_PROT_LED_')) or c=='HLMP-WL02':continue
    if c=='AD823A':
        amps.extend([(n['1'],n['3'],n['2']),(n['7'],n['5'],n['6'])])
    elif c=='NKK MN12':switches.append((int(r.rsplit('SW',1)[1]),n))
    elif r.rsplit('.',1)[-1].startswith('R'):res.append((n['1'],n['2'],val(p['value'])))
    elif r.rsplit('.',1)[-1].startswith('C'):caps.append((n['1'],n['2'],val(p['value'])))

def solve(route,phase,levels,signals=(.6,-.8,1.1,-1.3),aux=(.25,-.4),ret=(.165,-.165),frequency=0,load=None):
    fixed={'GND':0,'VCC':12 if not frequency else 0,'VEE':-12 if not frequency else 0,
           'AUX_SEND':aux[0],'AUX_MAIN':aux[1],'RET_P':ret[0],'RET_N':ret[1]}
    for i in range(4):fixed[f'CH{i+1}_IN']=signals[i];fixed[f'CH{i+1}_LEVEL']=signals[i]*levels[i]
    branches=[(a,b,1/r) for a,b,r in res]
    if frequency:branches += [(a,b,2j*math.pi*frequency*c) for a,b,c in caps]
    for i,n in switches:
        # 1=MAIN, 3=SEND; auxiliary 1=invert, 3=normal.
        throw=(3 if route[i-1] else 1) if i<=4 else (3 if phase[i-5] else 1)
        branches.append((n['2'],n[str(throw)],1e3))
    if load:
        for bus in ['SEND','OUT']:branches.append((bus+'_P',bus+'_N',1/load))
    nodes=sorted({n for a,b,g in branches for n in [a,b]}|{n for a in amps for n in a})
    unknown=[n for n in nodes if n not in fixed];ix={n:i for i,n in enumerate(unknown)}
    N=len(unknown)+len(amps);A=[[0j]*N for _ in range(N)];z=[0j]*N
    def add(row,n,v):
        if n in fixed:z[row]-=v*fixed[n]
        else:A[row][ix[n]]+=v
    for a,b,g in branches:
        for node,other in [(a,b),(b,a)]:
            if node not in ix:continue
            add(ix[node],node,g);add(ix[node],other,-g)
    gain=1e6
    for k,(out,plus,minus) in enumerate(amps):
        row=len(unknown)+k;A[ix[out]][row]+=1
        add(row,out,1/gain);add(row,plus,-1);add(row,minus,1)
    # Partial-pivot Gaussian elimination; only nonzero terms updated.
    for k in range(N):
        p=max(range(k,N),key=lambda i:abs(A[i][k]));assert abs(A[p][k])>1e-18,('singular',k)
        A[k],A[p]=A[p],A[k];z[k],z[p]=z[p],z[k]
        active=[j for j in range(k+1,N) if A[k][j]];pivot=A[k][k]
        for i in range(k+1,N):
            if not A[i][k]:continue
            f=A[i][k]/pivot;A[i][k]=0
            for j in active:A[i][j]-=f*A[k][j]
            z[i]-=f*z[k]
    v=[0j]*N
    for i in range(N-1,-1,-1):v[i]=(z[i]-sum(A[i][j]*v[j] for j in range(i+1,N)))/A[i][i]
    return {**fixed,**{n:v[i] for n,i in ix.items()}}

def analysis():
    worst=0;count=0
    signals=(.6,-.8,1.1,-1.3);aux=(.25,-.4)
    for route in itertools.product([0,1],repeat=4):
        for phase in itertools.product([0,1],repeat=2):
            for levels in [(0,0,0,0),(1,1,1,1),(.2,.45,.7,.95)]:
                v=solve(route,phase,levels)
                send=sum(s*l for s,l,r in zip(signals,levels,route) if r)+aux[0]*(1 if phase[0] else -1)
                main=sum(s*l for s,l,r in zip(signals,levels,route) if not r)+aux[1]*(1 if phase[1] else -1)+1
                expected={'SEND_BUS':send,'MAIN_BUS':main,'SEND_P':.165*send,'SEND_N':-.165*send,'OUT_P':.165*main,'OUT_N':-.165*main}
                for n,t in expected.items():
                    err=abs(v[n]-t);worst=max(worst,err);assert err<1e-4,(route,phase,levels,n,v[n],t)
                count+=1
    cm=[]
    for voltage in [-5,0,5]:
        v=solve((0,0,0,0),(0,0),(0,0,0,0),aux=(0,0),ret=(voltage,voltage))
        cm.append(abs(v['MAIN_BUS']));assert cm[-1]<1e-4;assert abs(v['SEND_BUS'])<1e-8
    ac=[]
    for f in [1,20,100,1000,10000,20000,100000]:
        v=solve((1,0,0,0),(0,0),(1,0,0,0),signals=(1,0,0,0),aux=(0,0),ret=(0,0),frequency=f)
        p,n=v['SEND_P']/v['SEND_BUS'],v['SEND_N']/v['SEND_BUS']
        err=abs(p+n)/abs(p-n);assert err<1e-5,(f,p,n)
        ac.append({'Hz':f,'differentialGain':abs(p-n),'legMismatch':err,'phaseDeg':math.degrees(cmath.phase(p-n))})
    loaded=[]
    for r in [1000,10000,100000]:
        v=solve((1,0,0,0),(0,0),(1,0,0,0),signals=(1,0,0,0),aux=(0,0),ret=(0,0),load=r)
        g=(v['SEND_P']-v['SEND_N']).real/v['SEND_BUS'].real
        assert abs(g-.33*r/(r+940))<1e-5
        loaded.append({'ohms':r,'differentialGain':g})
    return {'dcCases':count,'maxDCErrorVolts':worst,'returnCommonModeResidualVolts':cm,'balancedAC':ac,'balancedLoads':loaded,
            'model':'Finite DC gain 1e6; ideal output impedances; real passive RC networks. No op-amp bandwidth, clipping, noise, distortion, parasitics or LED nonlinearity.'}

def audit():
    problems=[]
    pads=[(p,q) for p in D['parts'] for q in p['layout']['pads']]
    for via in D['vias']:
        for p,q in pads:
            # Via drill circle must remain outside the entire pad copper.
            dx=max(0,abs(via['at']['x']-q['at']['x'])-q['size']['width']/2)
            dy=max(0,abs(via['at']['y']-q['at']['y'])-q['size']['height']/2)
            if math.hypot(dx,dy)<via['drill']/2:problems.append(('via_in_pad',via['at'],p['reference'],q['number']))
    for p in D['parts']:
        r=p['reference'];c=p['component'];lay=p['layout']
        if c=='AD823A':assert lay['rotation']==0 and not lay['flipped'],r
        if p['package'].startswith('Chip'):
            assert p['package']=='Chip 1206' and not lay['flipped'],r
            if not p['readOnly']:assert lay['rotation']==0,r
        if c in ['Bourns 51','Pomona 1581','HLMP-WL02','NKK MN12']:assert lay['flipped'],r
        if c=='MTA-156-3':assert not lay['flipped'],r
    assert all(m['layoutRotation']==0 for m in D['modules'])
    bananas=[p for p in D['parts'] if p['component']=='Pomona 1581']
    closest=1e9
    for p in D['parts']:
        if p['component']=='Pomona 1581':continue
        b=p['layout']['bounds'];o=b['origin'];s=b['size']
        for banana in bananas:
            at=banana['layout']['at'];dx=max(o['x']-at['x'],at['x']-o['x']-s['width'],0);dy=max(o['y']-at['y'],at['y']-o['y']-s['height'],0)
            distance=math.hypot(dx,dy);closest=min(closest,distance)
            if distance<8500:problems.append(('banana_tool_clearance',p['reference'],banana['reference'],distance))
    spans={}
    for net in ['SUM_SEND','SUM_MAIN']:
        points=[q['at'] for p,q in pads if q['net'] and q['net']['name']==net]
        spans[net]={'widthMm':(max(p['x'] for p in points)-min(p['x'] for p in points))/1000,'heightMm':(max(p['y'] for p in points)-min(p['y'] for p in points))/1000,
                    'copperLengthMm':sum(math.hypot(t['end']['x']-t['start']['x'],t['end']['y']-t['start']['y']) for t in D['traces'] if t['net'] and t['net']['name']==net)/1000}
    return {'parts':len(P),'opAmps':sum(p['component']=='AD823A' for p in P),'passives':sum(p['package']=='Chip 1206' for p in D['parts']),
        'minimumBananaToolRadiusMm':closest/1000,'summingNodes':spans,'problems':problems}

if __name__=='__main__':
    result={'analysis':analysis(),'layout':audit()}
    (ROOT/'validation/verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    assert not result['layout']['problems'], 'Geometry audit failed'
