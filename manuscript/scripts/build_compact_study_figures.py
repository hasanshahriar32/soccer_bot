#!/usr/bin/env python3
"""Reflow the three supplied wide diagrams into readable single-column vectors.

The supplied PDFs are preserved. Values are bound to the saved offline studies;
no robot runtime, transport, inference or hardware code is executed.
"""
from pathlib import Path
import hashlib
import json
import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white

# Reuse the architecture/mission palette so future changes stay consistent.
from render_hazbot_figures import INK, MUTED, BLUE, TEAL, GOLD, RED, GRAY

BASE = Path(__file__).resolve().parents[1]
OUT = BASE/'figures/worflow-methodology-arch'
W = 248.4  # 3.45 inches: IEEE column width.
FILLS = {BLUE:'#f1f6f8', TEAL:'#eff6f7', GOLD:'#f9f6f1', RED:'#f8f0ef'}
FONT_DIR = Path('/usr/share/fonts/truetype/noto')
MATH_DIR = Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('HazSans', str(FONT_DIR/'NotoSans-Regular.ttf')))
pdfmetrics.registerFont(TTFont('HazBold', str(FONT_DIR/'NotoSans-Bold.ttf')))
pdfmetrics.registerFont(TTFont('HazMath', str(MATH_DIR/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('HazMathBold', str(MATH_DIR/'DejaVuSans-Bold.ttf')))

def label(c, x, y, text, size=7, bold=False, color=INK, bounds=None):
    """Use the paper's Noto Sans, with embedded fallback for math symbols."""
    font = 'HazBold' if bold else 'HazSans'
    fallback = 'HazMathBold' if bold else 'HazMath'
    widths = pdfmetrics.getFont(font).face.charWidths
    runs = []
    for char in text:
        chosen = font if ord(char) in widths else fallback
        if runs and runs[-1][0] == chosen:
            runs[-1] = (chosen,runs[-1][1]+char)
        else:
            runs.append((chosen,char))
    total = sum(pdfmetrics.stringWidth(t,f,size) for f,t in runs)
    assert x >= 3 and x+total <= W-3, text
    if bounds is not None:
        bx,by,bw,bh = bounds
        ascent = max(pdfmetrics.getAscent(f)*size/1000 for f,_ in runs)
        descent = min(pdfmetrics.getDescent(f)*size/1000 for f,_ in runs)
        assert bx+3 <= x and x+total <= bx+bw-3, ('panel width',text)
        assert by+3 <= y+descent and y+ascent <= by+bh-3, ('panel height',text)
    c.setFillColor(HexColor(color))
    for f,t in runs:
        c.setFont(f,size);c.drawString(x,y,t)
        x += pdfmetrics.stringWidth(t,f,size)

def badge(c,x,y,number,color=BLUE,size=10):
    c.setFillColor(HexColor(color));c.roundRect(x,y,size,size,1.5,stroke=0,fill=1)
    label(c,x+1.3,y+2.1,str(number),6.5,True,'#ffffff')

def section(c,x,y,number,title,color=BLUE):
    badge(c,x,y-2,number,color)
    label(c,x+14,y,title,6.8,True,color)

def box(c, x, y, w, h, color=BLUE):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(.65)
    c.setFillColor(HexColor(FILLS.get(color,"#f5f8fa")))
    c.roundRect(x, y, w, h, 3, stroke=1, fill=1)

def arrow(c, x1, y1, x2, y2, color=GRAY, dashed=False):
    c.setStrokeColor(HexColor(color)); c.setFillColor(HexColor(color)); c.setLineWidth(.7)
    c.setDash(2, 2) if dashed else c.setDash()
    c.line(x1,y1,x2,y2); c.setDash()
    a=math.atan2(y2-y1,x2-x1)
    p=c.beginPath(); p.moveTo(x2,y2)
    p.lineTo(x2-3*math.cos(a-.5),y2-3*math.sin(a-.5))
    p.lineTo(x2-3*math.cos(a+.5),y2-3*math.sin(a+.5));p.close()
    c.drawPath(p,fill=1,stroke=0)

def begin(stem, title, height):
    c=canvas.Canvas(str(OUT/f'{stem}_column.pdf'),pagesize=(W,height),invariant=1,initialFontName="HazSans")
    c.setTitle('HazBot: '+title); c.setAuthor('')
    label(c,4,height-12,'HAZBOT / '+title.upper(),7.8,True)
    c.setStrokeColor(HexColor('#d6e1e8'));c.line(4,height-18,W-4,height-18)
    return c

def methodology(ch, mission):
    c=begin('hazbot_methodology','Study methodology',216)
    source = (15,166,222,25)
    box(c,*source,BLUE)
    section(c,20,181,'01','SOURCES',BLUE)
    label(c,20,171,'Mission spec · URDF · wheel + arm gateways',6.5,
          color=MUTED,bounds=source)
    section(c,15,149,'02','ANALYSES',TEAL)
    section(c,132,149,'03','EVIDENCE',GOLD)

    rows=[(108,TEAL,'A  Coordinator',('28,672 pairs / policy', 'Oracle + BFS; 109 checks'),
           '0 full-policy violations',('Ablated guard violations:', '480 / 128 / 288')),
          (67,BLUE,'B  Wrist geometry',('68,921 joint poses', '1,013 independent FK poses'),
           '0.200 m link-sum bound',('2,747 below ground', 'Δ ≤ 6.8 × 10⁻¹⁷ m')),
          (26,GOLD,'C  Command interfaces',('261,121 wheel pairs', '2,255 arm-mapping cases'),
           '1,020: no sender call',('Mixed-zero input pairs', 'Magnitude lost; 29 checks'))]
    # Source fan-out and evidence collection stay in the outer gutters.
    # Every arrow terminates exactly on a panel boundary.
    c.setStrokeColor(HexColor(GRAY));c.setLineWidth(.7)
    c.lines([(15,178.5,6,178.5),(6,178.5,6,44.5),
             (244,126.5,244,11)])
    for y,color,title,analysis,result,detail in rows:
        left=(15,y,105,37);right=(132,y,105,37)
        box(c,*left,color);box(c,*right,color)
        label(c,20,y+26,title,7,True,color,bounds=left)
        for n,line in enumerate(analysis):
            label(c,20,y+16-10*n,line,6.5,color=MUTED,bounds=left)
        label(c,137,y+26,result,6.8,True,bounds=right)
        for n,line in enumerate(detail):
            label(c,137,y+16-10*n,line,6.5,color=MUTED,bounds=right)
        arrow(c,6,y+18.5,15,y+18.5)
        arrow(c,120,y+18.5,132,y+18.5,color)
        c.setStrokeColor(HexColor(GRAY));c.line(237,y+18.5,244,y+18.5)
    needs=(15,3,222,16)
    box(c,*needs,RED)
    section(c,20,8,'04','NEEDS',RED)
    label(c,64,8,'Stop feedback · calibrated reach · wheel rates',6.5,
          color=MUTED,bounds=needs)
    arrow(c,244,11,237,11)
    c.save()


def workflow():
    c=begin('hazbot_workflow','Retrieval workflow',196)
    for x,title,body,color in [(4,'Pi Camera V2','640 × 480 CSI → INT8 TFLite',BLUE),
                                (128,'YDLIDAR X4','CP2102 USB–UART → scan parser',TEAL)]:
        box(c,x,145,116.4,28,color)
        section(c,x+5,162,'01' if x==4 else '02',title,color)
        label(c,x+5,151,body,6.5,color=MUTED)
    for x,title,body,color in [(4,'Detection record','Class · confidence · position · age',BLUE),
                                (128,'Scan record','Clearance · range · age',TEAL)]:
        arrow(c,x+58,145,x+58,136,color);box(c,x,108,116.4,28,color)
        label(c,x+5,125,title,7,True,color);label(c,x+5,114,body,6.5,color=MUTED)
    box(c,4,84,240.4,17,GOLD);label(c,9,90,'Evidence + task authority: T, S, C · handling policy · deposit',6.5)
    for x in (62,186):arrow(c,x,108,x,101)
    arrow(c,W/2,84,W/2,77)
    box(c,4,34,240.4,43,TEAL)
    section(c,9,66,'03','REFERENCE COORDINATOR',TEAL)
    label(c,9,55,'SEARCH → APPROACH → DOCK → GRASP',6.8)
    label(c,9,45,'→ CARRY → PLACE → COMPLETE; failed guard → HOLD',6.5)
    arrow(c,62,34,62,30,GOLD);arrow(c,186,34,186,30,RED)
    box(c,4,4,116.4,26,GOLD);box(c,128,4,116.4,26,RED)
    section(c,9,20,'04','DRIVE · 9600 baud',GOLD)
    label(c,9,8,'F/B/L/R/S · requires S ∧ C ∧ A',6.5,color=MUTED)
    section(c,133,20,'05','ARM · 115200 baud',RED)
    label(c,133,8,'B/S/A/G · requires base rest B',6.5,color=MUTED)
    c.save()

def verification(m):
    c=begin('hazbot_verification','Bounded coordination verification',176)
    box(c,4,125,240.4,28,TEAL)
    section(c,9,142,'01','ENUMERATE',TEAL)
    section(c,130,142,'02','ORACLE + BFS',TEAL)
    label(c,9,131,'7 × 4,096 = 28,672 pairs / policy · 4 policies · no pruning',6.5,color=MUTED)
    arrow(c,W/2,125,W/2,118)
    label(c,4,109,'Base motion ⇒ S ∧ C ∧ A; approach ⇒ T; arm motion ⇒ B',6.5)
    section(c,4,96,'03','POLICY',RED);label(c,149,96,'Violations',7,True);label(c,211,96,'Prefix',7,True)
    policies=[('All guards','full',None),('No base–arm interlock','no_base_arm_interlock',1),
              ('No target authorization','no_target_authorization',2),('No scan age','no_scan_age',1)]
    for i,(name,key,prefix) in enumerate(policies):
        y=82-15*i
        if i%2==0:
            c.setFillColor(HexColor('#F0F5F7'));c.rect(4,y-4,240.4,14,fill=1,stroke=0)
        label(c,8,y,name,7)
        count=m['policies'][key]['violating_cases']
        c.setFillColor(HexColor(RED if count else TEAL))
        if count:
            c.rect(145,y,35*count/480,4,fill=1,stroke=0)
        value=f'{count:,}'
        label(c,205-pdfmetrics.stringWidth(value,'HazBold',7),y,value,7,True,
              TEAL if i==0 else RED)
        prefix_text='—' if prefix is None else str(prefix)
        label(c,230-pdfmetrics.stringWidth(prefix_text,'HazSans',7),y,prefix_text,7)
    section(c,4,21,'04','REACHABILITY: 7/7 phases · 13 edges · depth 6',TEAL)
    label(c,4,8,'11-step witness covers 9 actions. Counts are model properties.',6.5)
    c.save()

def main():
    OUT.mkdir(exist_ok=True)
    mission=json.loads((BASE/'data/hazbot_mission_results.json').read_text())
    ch=json.loads((BASE/'data/hazbot_characterization.json').read_text())
    assert mission['validation']['passed'] and mission['validation']['check_count']==109
    assert [mission['policies'][p]['violating_cases'] for p in ('full','no_base_arm_interlock','no_target_authorization','no_scan_age')]==[0,480,128,288]
    assert ch['validation']['passed'] and ch['validation']['check_count']==29
    assert ch['workspace']['grid']['total_poses']==68921
    assert ch['workspace']['grid']['below_ground_plane_count']==2747
    assert ch['workspace']['fk_validation']['total_poses']==1013
    assert ch['workspace']['fk_validation']['maximum_disagreement_m'] <= 6.8e-17
    assert ch['workspace']['shoulder_to_wrist_link_sum_bound_m']==0.2
    assert ch['protocols']['wheel']['exhaustive_cases']==261121
    assert ch['protocols']['arm']['total_mapping_cases']==2255
    methodology(ch,mission);workflow();verification(mission)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    record={'date':'2026-10-25','column_width_inches':3.45,'minimum_label_size_pt':6.5,
            'description':'Compact diagrams with connected methodology flow, uniform row spacing, bounded panel text and consistent paper styling.',
            'panel_padding_pt':3, 'methodology_height_pt':216,
            'style_reference':'scripts/render_hazbot_figures.py',
            'style_reference_sha256':sha(BASE/'scripts/render_hazbot_figures.py'),
            'primary_font':'Noto Sans', 'symbol_fallback':'DejaVu Sans',
            'palette':{'ink':INK,'muted':MUTED,'blue':BLUE,'teal':TEAL,'gold':GOLD,'red':RED,'arrows':GRAY},
            'generator_sha256':sha(Path(__file__)),
            'inputs_sha256':{str(p.relative_to(BASE)):sha(p) for p in
              [BASE/'data/hazbot_mission_results.json',BASE/'data/hazbot_characterization.json',
               *[OUT/f'hazbot_{n}.pdf' for n in ('methodology','workflow','verification')]]},
            'outputs_sha256':{str(p.relative_to(BASE)):sha(p) for p in OUT.glob('*_column.pdf')}}
    (BASE/'data/compact_study_figures.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Built three single-column vector figures; supplied originals preserved.')

if __name__=='__main__':main()
