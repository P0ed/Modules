#!/usr/bin/env python3
"""Rebuild the unrouted v2 design. Never overwrites the routed Mixer.pcb."""
import copy, json, pathlib, uuid, hashlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
V1 = json.loads((ROOT/'tools/v1-template.json').read_text())
def save(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n')
def pt(x,y): return dict(x=round(x*1000),y=round(y*1000))
def size(w,h): return dict(width=round(w*1000),height=round(h*1000))
R = next(f for f in V1['board']['footprints'] if f['reference']=='R_CH1_MAIN')
C = next(f for f in V1['board']['footprints'] if f['reference']=='C_REF')
def part(ref,value,n1,n2,x,y,sx,sy):
    f=copy.deepcopy(C if ref.startswith('C') else R)
    f.update(reference=ref,value=value,at=pt(x,y),rotation=0)
    f['symbol']['at']=pt(sx,sy)
    for p,n in zip(f['symbol']['pins'],[n1,n2]): p['netLabel']=n
    for p in f['pads']: p.pop('net',None)
    return f
def module(ref,source,x,y,sx,sy,labels,params=None):
    src=json.loads((ROOT/'Base'/f'{source}.pcb').read_text())
    old=next(m for m in V1['modules'] if m['filename']==source)
    m=copy.deepcopy(old)
    m.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'Mixer_v2/'+ref)).upper(),reference=ref,
             filename=source+'.pcb',layoutAt=pt(x,y),schematicAt=pt(sx,sy),layoutRotation=0,
             schematicRotation=0,netLabels=labels,parameterValues=params or {})
    return m

def balanced():
    """Matched differential pair from one source, identical noise gains and poles.
    Positive half: + divider 20K/3K3, - divider GND20K/feedback3K3.
    Negative half: - input20K/feedback3K3, + divider GND20K/3K3.
    47p across each 3K3, 470R outside feedback on each output.
    """
    d=copy.deepcopy(V1); b=d['board']
    b.update(footprints=[],traces=[],vias=[],holes=[],wires=[],size=size(25.4,28),sheetSize=size(250,180))
    d['nets']=[];d['parameters']=[]
    d['modules']=[module('M_OP','OP',12.7,14,125,85,
        {'1':'P_RAW','2':'P_MINUS','3':'P_PLUS','4':'N_PLUS','5':'N_MINUS','6':'N_RAW'})]
    specs=[
      ('R_P_IN','20K 0.1%','#1 IN','P_PLUS',6.35,3.0),
      ('R_P_GND','3K3 0.1%','P_PLUS','GND',6.35,5.5),
      ('C_P_DIV','47p C0G','P_PLUS','GND',6.35,8.0),
      ('R_P_GAIN','20K 0.1%','GND','P_MINUS',6.35,14),
      ('R_P_FB','3K3 0.1%','P_MINUS','P_RAW',6.35,21),
      ('C_P_FB','47p C0G','P_MINUS','P_RAW',6.35,23.5),
      ('R_P_OUT','470 0.5W','P_RAW','#2 P',6.35,26),
      ('R_N_BIAS','20K 0.1%','GND','N_PLUS',19.05,3),
      ('R_N_GND','3K3 0.1%','N_PLUS','GND',19.05,5.5),
      ('C_N_DIV','47p C0G','N_PLUS','GND',19.05,8),
      ('R_N_IN','20K 0.1%','N_MINUS','#1 IN',19.05,15.5),
      ('R_N_FB','3K3 0.1%','N_MINUS','N_RAW',19.05,21),
      ('C_N_FB','47p C0G','N_MINUS','N_RAW',19.05,23.5),
      ('R_N_OUT','470 0.5W','N_RAW','#3 N',19.05,26),
    ]
    for i,(ref,val,n1,n2,x,y) in enumerate(specs):
        b['footprints'].append(part(ref,val,n1,n2,x,y,35+(i//7)*170,25+(i%7)*20))
    save(ROOT/'Balanced.unrouted.json',d)
    if not (ROOT/'Balanced.pcb').exists():save(ROOT/'Balanced.pcb',d)
    return d

def mixer():
    d=copy.deepcopy(V1);b=d['board']
    b.update(traces=[],vias=[],wires=[],sheetSize=size(650,420))
    # The controls module already locates switches and LEDs on the bottom side.
    keep=[f for f in b['footprints'] if not f['reference'].startswith(('R_HALF','R_MAG','R_ENV','C_ENV','R_REF','C_REF','R_BAL'))]
    b['footprints']=keep
    parts={f['reference']:f for f in keep}
    def label(ref,pin,net):
        f=parts[ref]
        next(p for p in f['symbol']['pins'] if p['number']==str(pin))['netLabel']=net
    def move(ref,x,y): parts[ref]['at']=pt(x,y)
    def add(ref,val,n1,n2,x,y):
        f=part(ref,val,n1,n2,x,y,20,20);keep.append(f);parts[ref]=f
    for f in keep:
        for p in f.get('pads',[]):p.pop('net',None)
        if f.get('component') in ['Bourns 51','Pomona 1581']:f['flipped']=True
    for i in range(1,5):
        add(f'R_PROT_CH{i}','4K7',f'CH{i}_LEVEL',f'CH{i}_SAFE',
            [70,82.4,19.2,31.6][i-1],120.5)
        move(f'R_CH{i}_SEND',38.5,92.5+(i-1)*2.5)
        move(f'R_CH{i}_MAIN',63.1,92.5+(i-1)*2.5)
        label(f'R_CH{i}_MAIN',1,'SUM_MAIN');label(f'R_CH{i}_MAIN',2,f'CH{i}_MAIN')
    move('R_AUX_SEND_SUM',38.5,102.5)
    move('R_AUX_MAIN_SUM',63.1,102.5)
    label('R_AUX_MAIN_SUM',1,'SUM_MAIN');label('R_AUX_MAIN_SUM',2,'AUX_MAIN_PHASE')
    move('R_RETURN_SUM',63.1,105)
    label('R_RETURN_SUM',1,'SUM_MAIN');label('R_RETURN_SUM',2,'RETURN_SERGE')
    for name,x in [('SEND',38.5),('MAIN',63.1)]:
        move('R_AUX_'+name+'_IN',x,75.5)
        move('R_AUX_'+name+'_FB',x,78)
        parts['R_AUX_'+name+'_IN']['value']='15K3'
        label('R_AUX_'+name+'_IN',1,'AUX_'+name+'_SAFE')
        add('R_PROT_AUX_'+name,'4K7','AUX_'+name,'AUX_'+name+'_SAFE',x,73)
        add('R_PROT_PHASE_'+name,'4K7','AUX_'+name+'_SW','AUX_'+name+'_PLUS',x,80.5)
        move('R_BUS_'+name,x,52)
        add('R_PROT_LED_'+name,'4K7',name+'_AMP','LED_'+name+'_SAFE',44.45 if name=='SEND' else 57.15,81)
    move('R_RET_P_GND',63.5,28.5)
    move('R_RET_FB',38.1,28.5)
    for sign,x in [('N',38.1),('P',63.5)]:
        parts['R_RET_'+sign+'_IN']['value']='28K3 0.1%'
        label('R_RET_'+sign+'_IN',1,'RET_'+sign+'_SAFE')
        add('R_PROT_RET_'+sign,'4K7 0.1%','RET_'+sign,'RET_'+sign+'_SAFE',x,22.5)
    # Arrange the schematic by channel strips and functional blocks.
    d['modules']=[
      module('M_BUF12','BUF',76.2,126,150,70,{'1':'CH1_BUF','2':'CH1_SAFE','3':'CH2_SAFE','4':'CH2_BUF'}),
      module('M_BUF34','BUF',25.4,126,150,145,{'1':'CH3_BUF','2':'CH3_SAFE','3':'CH4_SAFE','4':'CH4_BUF'}),
      module('M_CONTROLS','IOControls',50.8,101.6,240,110,
          {**next(m['netLabels'] for m in V1['modules'] if m['reference']=='M_CONTROLS'),
           '14':'AUX_SEND_SW','23':'AUX_MAIN_SW'}),
      module('M_AUX','OP',50.8,74.5,240,240,{'1':'AUX_SEND_PHASE','2':'AUX_SEND_MINUS','3':'AUX_SEND_PLUS','4':'AUX_MAIN_PLUS','5':'AUX_MAIN_MINUS','6':'AUX_MAIN_PHASE'}),
      module('M_SUM','MIX',50.8,101,370,110,{'1':'SUM_SEND_NEG','2':'SUM_SEND','3':'SUM_MAIN','4':'SUM_MAIN_NEG'},{'R1':'20K','R2':'20K'}),
      module('M_BUS','OUT',50.8,52,460,110,{'1':'SEND_BUS','2':'SEND_INV','3':'SEND_AMP','4':'MAIN_AMP','5':'MAIN_INV','6':'MAIN_BUS'},{'R1':'20K','R2':'20K'}),
      module('M_RETURN','OP',50.8,25.4,370,330,{'1':'RETURN_SERGE','2':'RET_MINUS','3':'RET_PLUS','4':'GND','5':'UNUSED_RETURN','6':'UNUSED_RETURN'}),
      module('M_LED_DRIVE','LEDDRIVE',50.8,86,460,240,{'1':'LED_SEND_A','2':'LED_SEND_K','3':'LED_SEND_SAFE','4':'LED_MAIN_SAFE','5':'LED_MAIN_K','6':'LED_MAIN_A'},{'R1':'4K7','R2':'4K7'}),
    ]
    for name,x,inputnet in [('SEND',76.2,'SEND_BUS'),('OUT',25.4,'MAIN_BUS')]:
        m=copy.deepcopy(d['modules'][3]);m.update(reference='M_BAL_'+name,filename='Balanced.pcb',
            id=str(uuid.uuid5(uuid.NAMESPACE_URL,'Mixer_v2/M_BAL_'+name)).upper(),
            size=size(25.4,28),layoutAt=pt(x,98),schematicAt=pt(560,85 if name=='SEND' else 155),
            interface=[{'name':n,'number':i+1} for i,n in enumerate(['IN','P','N'])],
            netLabels={'1':inputnet,'2':name+'_P','3':name+'_N'},parameters=[],parameterValues={})
        d['modules'].append(m)
    groups=[
      ([r for i in range(1,5) for r in [f'J_IN{i}',f'P{i}',f'R_PROT_CH{i}']],30,30,3),
      ([f'R_CH{i}_{bus}' for i in range(1,5) for bus in ['SEND','MAIN']]+['R_AUX_SEND_SUM','R_AUX_MAIN_SUM','R_RETURN_SUM'],300,30,2),
      ([r for r in parts if 'AUX' in r and not r.endswith('_SUM')],30,220,4),
      (['R_BUS_SEND','R_BUS_MAIN','J_SEND_BAN','J_MAIN_BAN'],420,40,2),
      (['J_SEND','J_OUT'],610,85,1),
      (['J_RETURN']+[r for r in parts if r.startswith(('R_RET','R_PROT_RET')) and r!='R_RETURN_SUM'],260,300,3),
      (['R_PROT_LED_SEND','R_PROT_LED_MAIN'],420,200,2),
      (['R_PROT_PHASE_SEND','R_PROT_PHASE_MAIN'],160,280,2),
      (['J_PWR','C_PWR_POS','C_PWR_NEG'],30,360,3),
    ]
    seen=set()
    for refs,x,y,cols in groups:
        for i,r in enumerate(refs):
            if r in seen:continue
            parts[r]['symbol']['at']=pt(x+(i%cols)*35,y+(i//cols)*20);seen.add(r)
    assert set(parts)==seen, set(parts)-seen
    d['nets']=[]
    save(ROOT/'Mixer.unrouted.json',d)
    if not (ROOT/'Mixer.pcb').exists():save(ROOT/'Mixer.pcb',d)
    manifest={'panel':'MIX4.panel','panelTransform':{'mirrorX':True,'boardOffsetMm':[3.175,12.7]},
      'boardMm':[101.6,152.4],'stack':['SIG','GND','VCC','VEE','GND','SIG'],
      'bananaToolRadiusMm':8.5,'placement':{r:f['at'] for r,f in parts.items()},
      'baseSHA256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'Base').glob('*.pcb'))}}
    save(ROOT/'manifest.json',manifest)

if __name__=='__main__':
    balanced();mixer()
