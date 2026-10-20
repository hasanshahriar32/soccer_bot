#!/usr/bin/env python3
"""Code-native technical topology and observation-contract illustration.

No runtime robot code is imported or operated. Node and link labels are grounded
in the audited source; offline gate semantics come from the saved replay.
"""
from datetime import datetime, timezone
from html import escape
import os
from pathlib import Path
import subprocess

from technical_icons import icon_use, svg_symbols
from export_drawio import export_drawio

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'figures'
INK='#263645'; MUTED='#647582'; BLUE='#356d93'; TEAL='#008b91'
GOLD='#a67529'; RED='#a84b45'; GRAY='#8998a3'
EPOCH=str(int(datetime(2026,10,21,tzinfo=timezone.utc).timestamp()))

class Drawing:
    def __init__(self,width,height):
        self.width=width; self.height=height; self.parts=[]
        self.rect(0,0,width,height,'white','none')
    def text(self,x,y,label,size=20,color=INK,bold=False,anchor='start'):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{anchor}">{escape(str(label))}</text>')
    def rect(self,x,y,width,height,fill='#fbfcfd',stroke='#cbd6df',dashed=False):
        dash=' stroke-dasharray="7 5"' if dashed else ''
        self.parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{dash}/>')
    def icon(self,name,x,y,size=82):
        self.parts.append(icon_use(name,x,y,size))
    def route(self,points,color=BLUE,dashed=False,arrow=True,width=2.4):
        dash=' stroke-dasharray="7 5"' if dashed else ''
        marker=f' marker-end="url(#arrow{color[1:]})"' if arrow else ''
        pts=' '.join(f'{x},{y}' for x,y in points)
        self.parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dash}{marker}/>')
    def legend(self,x,y,label,color,dashed=False):
        self.route([(x,y-6),(x+35,y-6)],color,dashed)
        self.text(x+47,y,label,18.5,MUTED)
    def svg(self,title,description):
        markers=''.join(f'<marker id="arrow{c[1:]}" viewBox="0 0 12 10" refX="10" refY="5" markerWidth="8" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L10 5L1 9" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/></marker>' for c in (BLUE,TEAL,GOLD,RED,GRAY))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width/200}in" height="{self.height/200}in" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'+svg_symbols()+f'<defs>{markers}</defs><g font-family="Noto Sans,sans-serif">'+''.join(self.parts)+'</g></svg>\n')


def architecture(data):
    g=Drawing(1420,750)
    g.text(22,31,'DISTRIBUTED SOCCERBOT ARCHITECTURE',24,bold=True)
    g.text(1398,31,'Schematic components and logical paths',18.5,MUTED,anchor='end')
    g.rect(18,54,380,435)
    g.rect(440,54,962,435)
    g.text(36,84,'A  ROBOT EDGE',23,bold=True)
    g.text(460,84,'B  ROS 2 LAPTOP HUB',23,bold=True)
    # Physical component glyphs are schematic; repository Pi model labels vary.
    g.icon('camera',75,110,82); g.text(116,216,'Camera',20,bold=True,anchor='middle')
    g.icon('lidar',260,110,82); g.text(301,216,'YDLidar',20,bold=True,anchor='middle')
    g.route([(75,151),(55,151),(55,267),(180,267),(180,306)])
    g.text(72,245,'Camera I/O',18.5,MUTED)
    g.route([(342,151),(370,151),(370,283),(226,283),(226,306)])
    g.text(274,245,'USB serial',18.5,MUTED,anchor='middle')
    g.icon('sbc',150,306,104)
    g.text(210,442,'Raspberry Pi',21,bold=True,anchor='middle')
    g.text(220,468,'Sensor + motor gateway',18.5,MUTED,anchor='middle')
    # Distinct bridge variants; do not depict incompatible serial/JSON paths as
    # a single verified deployment. No local IP, hostname or credentials used.
    g.icon('bridge',494,130,70)
    g.icon('laptop',1320,78,65)
    g.text(535,228,'Image bridge',20,bold=True,anchor='middle')
    g.text(535,252,'HTTP / TCP JPEG',18,MUTED,anchor='middle')
    g.icon('bridge',494,327,70)
    g.text(535,421,'Scan bridge',20,bold=True,anchor='middle')
    g.text(535,445,'Serial / JSON variants',18,MUTED,anchor='middle')
    g.route([(254,334),(420,334),(420,165),(493,165)])
    g.route([(254,376),(420,376),(420,362),(492,362)])
    g.text(355,361,'LAN',18.5,MUTED,anchor='middle')
    g.icon('fusion',830,220,90)
    g.text(875,118,'Ball tracker',22,bold=True,anchor='middle')
    g.text(875,142,'Bearing + range',18.5,MUTED,anchor='middle')
    g.route([(565,165),(875,165),(875,219)])
    g.text(700,153,'/image_raw',20,BLUE,anchor='middle')
    g.route([(420,260),(829,260)])
    g.text(700,283,'Detections / TCP 8001',19,BLUE,anchor='middle')
    g.route([(565,362),(875,362),(875,311)])
    g.text(708,346,'/scan',20,BLUE,anchor='middle')
    g.route([(565,384),(1215,384),(1215,311)])
    g.text(1005,406,'/scan: whole-scan minimum',19,BLUE,anchor='middle')
    g.icon('controller',1170,220,90)
    g.text(1215,118,'Metric chaser',22,bold=True,anchor='middle')
    g.text(1215,142,f"{data['settings']['control_hz']} Hz nominal loop",19,MUTED,anchor='middle')
    g.route([(920,265),(1169,265)])
    g.text(1045,243,'/ball_position',19.5,BLUE,anchor='middle')
    g.text(1045,292,'Point: x, y, range [m]',18.5,MUTED,anchor='middle')
    g.rect(726,432,650,42,'#fff7f5','#e5b8b3')
    g.text(1051,460,'Pixel PD consumer: unit mismatch; excluded from replay',18.5,RED,anchor='middle')
    # Existing direct hardware command path; it is not gated in deployed code.
    g.route([(1260,265),(1390,265),(1390,506),(365,506),(365,394),(253,394)],GOLD)
    g.text(520,498,'Motor socket / TCP 9000',18.5,GOLD,anchor='middle')
    g.rect(18,527,645,188)
    g.text(212,553,'ACTUATOR PATH',22,bold=True)
    g.route([(172,413),(80,413),(80,567)],GOLD)
    g.icon('mcu',45,569,76); g.text(83,665,'Arduino',20,bold=True,anchor='middle')
    g.text(98,689,'Serial: 9600 baud',18,MUTED,anchor='middle')
    g.icon('driver',275,569,76); g.text(313,665,'L298N driver',20,bold=True,anchor='middle')
    g.icon('drive',510,566,82); g.text(551,665,'DC drive',20,bold=True,anchor='middle')
    g.route([(122,606),(274,606)],GOLD); g.text(198,589,'GPIO / PWM',18.5,GOLD,anchor='middle')
    g.route([(352,606),(509,606)],GOLD); g.text(432,589,'Drive',18.5,GOLD,anchor='middle')
    # Evaluated code is copied by AST into the harness, not connected to motors.
    g.route([(1260,292),(1373,292),(1373,491),(684,491),(684,610),(739,610)],TEAL,True)
    g.rect(706,527,696,188,'#f5fbfa',TEAL,True)
    g.text(725,553,'C  OFFLINE RESEARCH HARNESS',22,bold=True)
    g.icon('controller',740,574,70); g.text(775,665,'Source replay',19.5,bold=True,anchor='middle')
    g.icon('gate',1000,574,70); g.text(1035,665,'Age + validity',19.5,bold=True,anchor='middle')
    g.icon('capture',1240,574,70); g.text(1275,665,'Command log',19.5,bold=True,anchor='middle')
    g.route([(811,610),(998,610)],TEAL,True)
    g.text(905,596,'Requested Twist',18,TEAL,anchor='middle')
    g.route([(1072,610),(1238,610)],TEAL,True)
    g.text(1155,596,'Pass / zero',18,TEAL,anchor='middle')
    ticks=data['aggregate']['source']['ticks']; scenarios=data['settings']['scenarios']
    g.text(1054,695,f'{scenarios} constructed traces · {ticks} ticks/policy · motor calls bypassed',18.5,MUTED,anchor='middle')
    g.legend(28,742,'Sensor / ROS data',BLUE)
    g.legend(382,742,'Existing motor command paths',GOLD)
    g.legend(930,742,'Offline reference only',TEAL,True)
    return g.svg('SoccerBot source topology and evaluated boundary',
        'Schematic camera, LiDAR, Raspberry Pi, ROS 2 host and Arduino motor path. '
        'Solid paths are supported by source, not an end-to-end deployment claim. '
        'The dashed supervisor operates only in constructed offline replay; motor calls are bypassed.')


def contract_gate(data):
    g=Drawing(690,468)
    g.text(20,31,'OBSERVATION CONTRACT AT EACH TICK',23,bold=True)
    g.text(20,58,'Illustrative logic of the offline full supervisor',18.5,MUTED)
    g.icon('clock',24,89,70)
    g.text(113,111,'1  Fresh scan receipt',21,bold=True)
    g.text(113,138,'Receipt exists; 0 ≤ age < timeout',19,MUTED)
    g.icon('lidar',24,178,70)
    g.text(113,200,'2  Usable range evidence',21,bold=True)
    lo,hi=data['settings']['source_range_validity_open_interval_m']
    g.text(113,227,f'Finite accepted ranges: {lo:g} < r < {hi:g} m',19,MUTED)
    g.icon('fusion',24,267,70)
    g.text(113,289,'3  Metric target payload',21,bold=True)
    g.text(113,316,'Finite target, absence or unobserved state',18.5,MUTED)
    for y in (124,213,302):
        g.route([(520,y),(574,y),(574,361)],TEAL)
    g.icon('gate',537,361,70)
    g.text(574,455,'Pass / zero',19,TEAL,anchor='middle')
    g.text(20,379,'Near-range stop is retained from the source.',18.5,MUTED)
    g.text(20,407,'A fresh invalid payload fails usability.',18.5,RED)
    g.text(20,435,'Receipt age does not measure capture age.',18.5,MUTED)
    return g.svg('Offline observation-contract logic',
        'Illustrative conditions, not measured geometry or deployed control. Fresh receipt, valid ranges '
        'and a nonmalformed metric target state are required. The existing near-range stop remains.')


def render(data):
    OUT.mkdir(exist_ok=True)
    metadata={}
    env=dict(os.environ,SOURCE_DATE_EPOCH=EPOCH)
    for name,body in [('architecture',architecture(data)),('contract_gate',contract_gate(data))]:
        source=OUT/f'{name}.svg'; source.write_text(body)
        subprocess.run(['rsvg-convert','--format=pdf1.5','--output',str(OUT/f'{name}.pdf'),str(source)],check=True,env=env)
        subprocess.run(['rsvg-convert','--format=png','--width='+('2130' if name=='architecture' else '1035'),
            '--output',str(OUT/f'{name}.png'),str(source)],check=True,env=env)
        metadata[name]=export_drawio(source,OUT/f'{name}.drawio')
    return metadata
