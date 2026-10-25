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
from reportlab.lib.colors import HexColor, Color, white

BASE = Path(__file__).resolve().parents[1]
OUT = BASE/'figures/worflow-methodology-arch'
W = 248.4  # 3.45 inches: IEEE column width.
INK, MUTED = '#24384A', '#596F82'
BLUE, TEAL, GOLD, RED = '#2C7D9F', '#008B92', '#AD7B2D', '#B35B50'
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('HazSans', str(FONT_DIR/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('HazBold', str(FONT_DIR/'DejaVuSans-Bold.ttf')))

def label(c, x, y, text, size=7, bold=False, color=INK):
    c.setFillColor(HexColor(color))
    c.setFont('HazBold' if bold else 'HazSans', size)
    assert x + pdfmetrics.stringWidth(text, 'HazBold' if bold else 'HazSans', size) <= W - 3, text
    c.drawString(x, y, text)

def box(c, x, y, w, h, color=BLUE):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(.65)
    rgb = HexColor(color)
    c.setFillColor(Color(.95+.05*rgb.red, .95+.05*rgb.green, .95+.05*rgb.blue))
    c.roundRect(x, y, w, h, 3, stroke=1, fill=1)

def arrow(c, x1, y1, x2, y2, color=MUTED, dashed=False):
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
    label(c,4,height-12,title,9,True)
    c.setStrokeColor(HexColor('#D5E1E8'));c.line(4,height-18,W-4,height-18)
    return c

def methodology(ch, mission):
    c=begin('hazbot_methodology','Study methodology',184)
    box(c,4,139,240.4,23)
    label(c,9,152,'Sources: mission specification · URDF chain',6.7,True)
    label(c,9,143,'Wheel SET: branch · arm mapper (5 aliases / 4 channels)',6.7)
    arrow(c,W/2,139,W/2,132)
    rows=[(96,TEAL,'A  Coordinator',('28,672 pairs / policy', 'Oracle + BFS; 109 checks'),
           '0 full-policy violations',('Ablated guard violations:', '480 / 128 / 288')),
          (57,BLUE,'B  Wrist geometry',('68,921 joint poses', '1,013 independent FK poses'),
           '0.200 m link-sum bound',('2,747 below ground', 'Δ ≤ 6.8 × 10⁻¹⁷ m')),
          (18,GOLD,'C  Command interfaces',('261,121 wheel pairs', '2,255 arm-mapping cases'),
           '1,020: no command',('Mixed-zero wheel pairs', 'Magnitude lost; 29 checks'))]
    for y,color,title,analysis,result,detail in rows:
        box(c,4,y,117,34,color);box(c,130,y,114.4,34,color)
        label(c,9,y+24,title,7,True,color)
        for n,line in enumerate(analysis):label(c,9,y+14-9*n,line,6.5)
        label(c,135,y+24,result,6.8,True)
        for n,line in enumerate(detail):label(c,135,y+14-9*n,line,6.5)
        arrow(c,121,y+17,130,y+17,color)
    label(c,4,6,'Needs: stop feedback · calibrated reach · wheel-rate semantics',6.5)
    c.save()

def workflow():
    c=begin('hazbot_workflow','Retrieval workflow',196)
    for x,title,body,color in [(4,'Pi Camera V2','640 × 480 CSI → INT8 TFLite',BLUE),
                                (128,'YDLIDAR X4','CP2102 USB–UART → scan parser',TEAL)]:
        box(c,x,145,116.4,28,color);label(c,x+5,162,title,7,True,color);label(c,x+5,151,body,6.5)
    for x,title,body,color in [(4,'Detection record','Class · confidence · position · age',BLUE),
                                (128,'Scan record','Clearance · range · age',TEAL)]:
        arrow(c,x+58,145,x+58,136,color);box(c,x,108,116.4,28,color)
        label(c,x+5,125,title,7,True,color);label(c,x+5,114,body,6.5)
    box(c,4,84,240.4,17,GOLD);label(c,9,90,'Evidence + task authority: T, S, C · handling policy · deposit',6.5)
    for x in (62,186):arrow(c,x,108,x,102)
    arrow(c,W/2,84,W/2,77)
    box(c,4,34,240.4,43,TEAL)
    label(c,9,66,'Seven-phase reference coordinator',7,True,TEAL)
    label(c,9,55,'SEARCH → APPROACH → DOCK → GRASP',6.8)
    label(c,9,45,'→ CARRY → PLACE → COMPLETE; failed guard → HOLD',6.5)
    arrow(c,62,34,62,26,GOLD);arrow(c,186,34,186,26,RED)
    box(c,4,4,116.4,22,GOLD);box(c,128,4,116.4,22,RED)
    label(c,9,17,'Drive: F/B/L/R/S · 9600 baud',6.5,True,GOLD)
    label(c,9,8,'Motion requires S ∧ C ∧ A',6.5)
    label(c,133,17,'Arm: B/S/A/G · 115200 baud',6.5,True,RED)
    label(c,133,8,'Arm motion requires base rest B',6.5)
    c.save()

def verification(m):
    c=begin('hazbot_verification','Bounded coordination verification',176)
    box(c,4,125,240.4,28,TEAL)
    label(c,9,142,'7 phases × 4,096 valuations = 28,672 pairs / policy',7,True)
    label(c,9,131,'Four policies → independent command oracle → BFS',6.8)
    arrow(c,W/2,125,W/2,118)
    label(c,4,109,'Base motion ⇒ S ∧ C ∧ A; approach ⇒ T; arm motion ⇒ B',6.5)
    label(c,4,96,'Policy',7,True);label(c,149,96,'Violations',7,True);label(c,211,96,'Prefix',7,True)
    policies=[('All guards','full',None),('No base–arm interlock','no_base_arm_interlock',1),
              ('No target authorization','no_target_authorization',2),('No scan age','no_scan_age',1)]
    for i,(name,key,prefix) in enumerate(policies):
        y=82-15*i
        if i%2==0:
            c.setFillColor(HexColor('#F0F5F7'));c.rect(4,y-4,240.4,14,fill=1,stroke=0)
        label(c,8,y,name,7);label(c,164,y,f"{m['policies'][key]['violating_cases']:,}",7,True,TEAL if i==0 else RED)
        label(c,222,y,'—' if prefix is None else str(prefix),7)
    label(c,4,20,'Full policy: 7/7 phases · 13 edges · completion depth 6',6.8,True)
    label(c,4,10,'11-step witness covers 9 actions. Counts are model properties.',6.5)
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
            'description':'Single-column vector reflows of supplied diagrams; supplied wide PDFs preserved.',
            'generator_sha256':sha(Path(__file__)),
            'inputs_sha256':{str(p.relative_to(BASE)):sha(p) for p in
              [BASE/'data/hazbot_mission_results.json',BASE/'data/hazbot_characterization.json',
               *[OUT/f'hazbot_{n}.pdf' for n in ('methodology','workflow','verification')]]},
            'outputs_sha256':{str(p.relative_to(BASE)):sha(p) for p in OUT.glob('*_column.pdf')}}
    (BASE/'data/compact_study_figures.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Built three single-column vector figures; supplied originals preserved.')

if __name__=='__main__':main()
