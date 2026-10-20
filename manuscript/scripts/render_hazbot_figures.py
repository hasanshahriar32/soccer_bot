#!/usr/bin/env python3
"""Reproducible original SVG hardware and mobile-manipulation illustrations.

This renderer only reads repository/proposal artifacts. It never imports or
operates the hardware stack. Physical interfaces are diagrammed separately from
native Pi compute and the unvalidated hazardous-material mission objective.
"""
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import subprocess

from hazbot_icons import icon_use, svg_symbols
from export_drawio import export_drawio

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'figures'
INK = '#253748'; MUTED = '#627483'; BLUE = '#34799c'; TEAL = '#16858d'
GOLD = '#a87935'; RED = '#ac5c52'; GRAY = '#9aaab6'; PALE = '#dce5eb'
EPOCH = str(int(datetime(2026,10,21,tzinfo=timezone.utc).timestamp()))


class Drawing:
    def __init__(self, width=1420, height=720):
        self.width, self.height = width, height
        self.parts = []
        self.rect(0,0,width,height,'white','none')

    def text(self,x,y,label,size=20,color=INK,bold=False,anchor='start'):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{anchor}">{escape(str(label))}</text>')

    def rect(self,x,y,width,height,fill='none',stroke=PALE,dashed=False,radius=4):
        dash = ' stroke-dasharray="7 5"' if dashed else ''
        self.parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>')

    def icon(self,name,x,y,size):
        self.parts.append(icon_use(name,x,y,size))

    def route(self,points,color=BLUE,dashed=False,arrow=True,width=2.8):
        dash = ' stroke-dasharray="7 5"' if dashed else ''
        marker = f' marker-end="url(#arrow{color[1:]})"' if arrow else ''
        pts = ' '.join(f'{x},{y}' for x,y in points)
        self.parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dash}{marker}/>')

    def sector(self,x,y,number,title,color):
        self.rect(x,y-22,31,31,color,'none',radius=3)
        self.text(x+15.5,y,number,20,'white',True,'middle')
        self.text(x+45,y,title,23,color,True)

    def svg(self,title,description):
        markers = ''.join(f'<marker id="arrow{c[1:]}" viewBox="0 0 12 10" refX="10" refY="5" markerWidth="8" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L10 5L1 9" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/></marker>' for c in (BLUE,TEAL,GOLD,RED,GRAY))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width/200}in" height="{self.height/200}in" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">'
                f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'+svg_symbols()+f'<defs>{markers}</defs><g font-family="Noto Sans,sans-serif">'+''.join(self.parts)+'</g></svg>\n')


def architecture():
    g = Drawing()
    g.text(22,31,'HAZBOT  /  MODULAR MOBILE MANIPULATION',24,bold=True)
    g.text(1398,31,'Physical interfaces and onboard compute',19,MUTED,anchor='end')
    g.route([(22,52),(1398,52)],PALE,arrow=False,width=1.4)
    # A compact central computing spine, rather than a laptop or network hub.
    g.rect(566,100,288,466,'#f5f9f6','#b8cdbf',radius=10)
    g.text(710,141,'RASPBERRY PI',25,bold=True,anchor='middle')
    g.text(710,168,'Central edge computer',20,MUTED,anchor='middle')
    g.icon('pi',589,192,242)
    g.text(710,457,'Native vision / ML',21,bold=True,anchor='middle')
    g.text(710,486,'Range association',20,anchor='middle')
    g.text(710,514,'Navigation / mission I/O',20,anchor='middle')
    g.text(710,542,'ROS 2 + serial interfaces',19,MUTED,anchor='middle')
    # 01: direct CSI sensing; the model remains on the Pi, not in a camera.
    g.sector(25,93,'01','VISION & ONBOARD ML',BLUE)
    g.icon('camera',59,126,171)
    g.text(146,325,'Pi Camera V2',22,bold=True,anchor='middle')
    g.route([(215,202),(528,202),(528,290),(609,290)],BLUE)
    g.text(362,188,'Direct CSI ribbon',20,BLUE,anchor='middle')
    g.text(358,260,'RGB image stream',20,anchor='middle')
    g.text(358,293,'Inference runs on Pi',20,anchor='middle')
    g.text(257,324,'INT8 detector · local TFLite',19,MUTED)
    g.text(25,369,'Task-class output → candidate target',19,MUTED)
    # 02: scanner controller transports packets; navigation belongs to Pi.
    g.sector(948,93,'02','RANGING & NAVIGATION',TEAL)
    g.icon('controller',956,125,108)
    g.icon('lidar',1196,121,164)
    g.route([(1208,203),(1066,203)],TEAL)
    g.text(1136,183,'Scan packets',19,TEAL,anchor='middle')
    g.text(1011,287,'Sensor controller',21,bold=True,anchor='middle')
    g.text(1011,315,'Built-in ranging MCU',19,MUTED,anchor='middle')
    g.text(1278,326,'YDLidar X4',22,bold=True,anchor='middle')
    g.route([(962,213),(909,213),(909,286),(813,286)],TEAL)
    g.text(920,255,'USB serial',19,TEAL)
    g.text(948,369,'2-D ranges → clearance + target distance',19,MUTED)
    # 03: dedicated low-level drive MCU. This is not the arm controller.
    g.sector(25,437,'03','WHEEL DRIVE',GOLD)
    g.icon('arduino',67,500,110)
    g.icon('driver',254,500,110)
    g.icon('drive',433,496,115)
    g.route([(612,388),(537,388),(537,475),(123,475),(123,512)],GOLD)
    g.text(344,463,'USB serial · 9600 baud',19,GOLD,anchor='middle')
    g.route([(173,553),(265,553)],GOLD)
    g.text(220,533,'PWM + DIR',19,GOLD,anchor='middle')
    g.route([(358,553),(444,553)],GOLD)
    g.text(401,533,'Power',19,GOLD,anchor='middle')
    g.text(122,633,'Drive Arduino',21,bold=True,anchor='middle')
    g.text(308,633,'L298N driver',21,bold=True,anchor='middle')
    g.text(490,633,'DC wheel pair',21,bold=True,anchor='middle')
    g.text(25,667,'Differential mobility; separate motor controller',19,MUTED)
    # 04: four servo channels = base + shoulder + elbow + gripper.
    g.sector(948,437,'04','ROBOTIC ARM & GRIPPER',RED)
    g.icon('arduino',957,500,110)
    g.icon('arm',1196,464,178)
    g.route([(814,388),(894,388),(894,475),(1013,475),(1013,512)],RED)
    g.text(1120,463,'USB serial · 115200 baud',19,RED,anchor='middle')
    g.route([(1063,554),(1208,554)],RED)
    g.text(1135,534,'Servo pulses',19,RED,anchor='middle')
    g.text(1011,633,'Arm Arduino',21,bold=True,anchor='middle')
    g.text(1280,651,'3 axes + gripper',21,bold=True,anchor='middle')
    g.text(948,678,'B / S / A / G → four servo channels',19,MUTED)
    g.route([(22,693),(1398,693)],PALE,arrow=False,width=1.4)
    g.text(22,717,'Colored links denote physical interfaces; symbols are schematic, not to scale.',18.5,MUTED)
    return g.svg('HazBot Pi-centred architecture with four robot subsystems',
        'Raspberry Pi is the central compute device. Camera V2 connects through CSI and vision/ML executes natively on Pi. '
        'YDLidar X4 communicates through its built-in controller and USB-UART interface; navigation runs on Pi. '
        'A dedicated drive Arduino at 9600 baud controls L298N and DC wheels; a separate arm Arduino at 115200 baud '
        'controls base, shoulder, elbow and gripper servo channels. Current learned detector classes are tennis and cricket balls. '
        'This is a source-grounded system schematic, not proof of autonomous hazardous-material handling.')



def arm_geometry():
    """Draw the zero-coordinate URDF chain, rather than a generic wrist arm."""
    import xml.etree.ElementTree as ET
    urdf_path = BASE.parent / 'scripts' / 'robot.urdf'
    tree = ET.parse(urdf_path)
    joints = {joint.attrib['name']:joint for joint in tree.getroot().findall('joint')}
    def origin(name):
        return [float(v) for v in joints[name].find('origin').attrib['xyz'].split()]
    shoulder_x = origin('chassis_to_arm_mount')[0]
    shoulder_z = sum(origin(name)[2] for name in ('chassis_to_arm_mount','base_joint','shoulder_joint'))
    l1 = origin('elbow_joint')[2]
    l2 = origin('wrist_joint')[0]
    assert joints['wrist_joint'].attrib['type'] == 'fixed'
    g = Drawing(690,450)
    g.text(19,29,'ARM GEOMETRY / SOURCE REFERENCE',22,bold=True)
    g.text(19,57,'Zero joint coordinates; sagittal projection',19,MUTED)
    sx,sy = 195,302
    scale = 2000
    ex,ey = sx,sy-l1*scale
    wx,wy = ex+l2*scale,ey
    # Source joint origins give a right angle at zero, not a straight 2-link arm.
    g.rect(sx-14,ey,28,sy-ey,'#d0dce4',INK,radius=2)
    g.rect(ex,ey-14,wx-ex,28,'#d0dce4',INK,radius=2)
    g.route([(sx-5,sy-20),(sx-5,ey+10)],'#f9fbfc',arrow=False,width=4)
    g.route([(ex+16,ey-5),(wx-8,ey-5)],'#f9fbfc',arrow=False,width=4)
    g.icon('pedestal',sx-47,sy+6,94)
    g.icon('joint',sx-22,sy-22,44)
    g.icon('joint',ex-22,ey-22,44)
    g.rect(wx,wy-13,47,26,'#667d8d',INK,radius=1)
    # Parallel jaws are symbolic at the end frame, not another positioning axis.
    g.route([(wx+47,wy-8),(wx+62,wy-25),(wx+108,wy-25),(wx+108,wy-12)],GOLD,arrow=False,width=5)
    g.route([(wx+47,wy+8),(wx+62,wy+25),(wx+108,wy+25),(wx+108,wy+12)],GOLD,arrow=False,width=5)
    g.text(164,87,'Elbow q3',20,bold=True,anchor='end')
    g.text(225,306,'Shoulder q2',20,bold=True)
    g.text(420,58,'Fixed wrist',20,bold=True)
    g.route([(443,65),(443,75),(418,88)],GRAY,arrow=False,width=1.7)
    g.text(531,169,'Gripper qG',20,bold=True,anchor='middle')
    g.route([(530,148),(530,122),(505,122)],GRAY,arrow=False,width=1.7)
    # Dimension witness lines and segment labels in the same coordinate frame.
    g.route([(105,ey),(105,sy)],MUTED,arrow=False,width=1.6)
    for y in (ey,sy):
        g.route([(94,y),(117,y)],MUTED,arrow=False,width=1.6)
    g.text(87,192,'L1',20,bold=True,anchor='end')
    g.text(87,219,f'{l1*1000:g} mm',19,MUTED,anchor='end')
    g.route([(ex,170),(wx,170)],MUTED,arrow=False,width=1.6)
    for x in (ex,wx):
        g.route([(x,159),(x,181)],MUTED,arrow=False,width=1.6)
    g.text((ex+wx)/2,205,f'L2 = {l2*1000:g} mm',20,bold=True,anchor='middle')
    g.text(281,355,'Base yaw q1',20,bold=True)
    g.text(281,381,'Yaw rotates arm out of plane',19,MUTED)
    g.route([(241,351),(271,351)],GRAY,arrow=False,width=1.7)
    g.route([(20,400),(670,400)],PALE,arrow=False,width=1.4)
    g.text(20,424,f'Shoulder frame: x = {shoulder_x*1000:g} mm, z = {shoulder_z*1000:g} mm',19,MUTED)
    g.text(20,446,'3 positioning axes + gripper; no active wrist axis.',19,MUTED)
    metadata = {'source':'scripts/robot.urdf','source_sha256':sha256(urdf_path.read_bytes()).hexdigest(),
        'reference_joint_coordinates_rad':{'base_joint':0,'shoulder_joint':0,'elbow_joint':0},
        'positioning_joint_count':3,'wrist_joint_type':'fixed','gripper_channels':1,
        'segment_lengths_m':[l1,l2],'shoulder_frame_m':[shoulder_x,0,shoulder_z],
        'visual_geometry':'Source-scaled two positioning segments; pedestal and parallel jaws schematic',
        'reference_is_performance_result':False}
    return g.svg('Source-derived HazBot arm geometry at zero joint coordinates',
        'The shoulder-to-elbow link is 100mm vertical and elbow-to-fixed-wrist link is 100mm horizontal '
        'at zero coordinates. The shoulder origin is x100mm,z155mm relative to the base. '
        'Base yaw acts out of the sagittal plane. Three positioning axes and a separate gripper '
        'channel match the source; there is no independent wrist actuator. Parallel-jaw shape is schematic.'),metadata


def mission_flow():
    """Seven reference phases; failed guards hold the current phase in place."""
    g = Drawing(1420,324)
    g.text(22,29,'REFERENCE COORDINATION MODEL',23,bold=True)
    g.text(1398,29,'SURROGATE EVALUATION',20,MUTED,anchor='end')
    g.route([(22,48),(1398,48)],PALE,arrow=False,width=1.4)
    centers = [110,310,510,710,910,1110,1310]
    phases = [
        ('SEARCH','Fresh target','Authorized class',BLUE),
        ('APPROACH','Scan valid + fresh','Clear path / stowed',BLUE),
        ('DOCK','Base stopped','Target in reach',TEAL),
        ('GRASP','Grip confirmed','Before transport',TEAL),
        ('CARRY','Arm stowed','Fresh clear route',GOLD),
        ('PLACE','In drop zone','Base stopped',GOLD),
        ('COMPLETE','Release confirmed','Task closed',TEAL),
    ]
    # Native component glyphs carry the story; there are no enclosing stage
    # boxes, and HOLD is explicitly a per-phase action rather than a new state.
    g.icon('camera',59,63,90)
    g.icon('object',111,109,52)
    g.icon('drive',263,66,94)
    g.icon('drive',463,69,88)
    g.route([(557,105),(557,145),(575,145)],GRAY,arrow=False,width=2.4)
    g.icon('arm',662,64,98)
    g.icon('drive',860,69,94)
    g.icon('object',885,66,48)
    g.icon('arm',1053,66,94)
    g.icon('container',1113,106,58)
    g.icon('container',1257,65,102)
    g.route([(1290,114),(1304,129),(1337,93)],TEAL,arrow=False,width=5)
    for left,right in zip(centers[:-1],centers[1:]):
        g.route([(left+57,125),(right-58,125)],GRAY,arrow=True,width=2.4)
    for x,(phase,line1,line2,color) in zip(centers,phases):
        g.text(x,197,phase,21.5,color,True,'middle')
        g.text(x,231,line1,19.5,INK,anchor='middle')
        g.text(x,257,line2,19.5,MUTED,anchor='middle')
    g.route([(22,280),(1398,280)],PALE,arrow=False,width=1.4)
    g.rect(22,296,67,25,'#fbf3e5','#d7c49f',radius=3)
    g.text(55.5,316,'HOLD',18,GOLD,True,'middle')
    g.text(105,316,'Failed prerequisite → remain in the current phase; advance only after valid evidence.',19.5,MUTED)
    return g.svg('Seven-phase reference mission for surrogate mobile manipulation',
        'An executable abstract reference coordination model, not the deployed hardware runtime. '
        'SEARCH, APPROACH, DOCK, GRASP, CARRY, PLACE and COMPLETE form seven phases. '
        'Authorized fresh target evidence enables approach; valid fresh scans, clear route and '
        'stowed arm permit base motion. Docking requires a stopped base and reachable target. '
        'Grip confirmation precedes transport. Placement requires drop zone and stopped base; '
        'release confirmation ends the mission. A failed prerequisite produces HOLD in the '
        'same phase and does not introduce an eighth phase. Icons illustrate task roles, not '
        'measured performance or classification of hazardous materials.')

def render(data=None):
    """Return renderer metadata; generate deterministic SVG/PDF/PNG/draw.io."""
    OUT.mkdir(exist_ok=True)
    env = dict(os.environ,SOURCE_DATE_EPOCH=EPOCH)
    metadata = {'renderer':'Original Python-authored SVG; librsvg vector export',
        'font':'Noto Sans', 'data_used':'Hardware source, URDF, engineering report and user architecture clarification',
        'figures':{}}
    arm_svg,arm_data = arm_geometry()
    for name, body, dimensions in [('hazbot_architecture',architecture(),[7.1,3.6]),('hazbot_arm_geometry',arm_svg,[3.45,2.25]),('hazbot_mission',mission_flow(),[7.1,1.62])]:
        source = OUT / f'{name}.svg'
        source.write_text(body)
        subprocess.run(['rsvg-convert','--format=pdf1.5','--output',str(OUT/f'{name}.pdf'),str(source)],check=True,env=env)
        subprocess.run(['rsvg-convert','--format=png','--width='+('1035' if name=='hazbot_arm_geometry' else '2130'),'--output',str(OUT/f'{name}.png'),str(source)],check=True,env=env)
        editor = export_drawio(source,OUT/f'{name}.drawio')
        # The shared exporter uses historical document titles; set a neutral
        # new project title in the generated XML without touching that module.
        import xml.etree.ElementTree as ET
        xml_path = OUT/f'{name}.drawio'
        tree = ET.parse(xml_path)
        diagram = tree.getroot().find('diagram')
        diagram.set('id',name); diagram.set('name',{'hazbot_architecture':'HazBot architecture','hazbot_arm_geometry':'HazBot arm geometry','hazbot_mission':'HazBot reference mission'}[name])
        ET.indent(tree,space='  ')
        tree.write(xml_path,encoding='utf-8',xml_declaration=True)
        editor['sha256'] = sha256(xml_path.read_bytes()).hexdigest()
        metadata['figures'][name] = {'dimensions_inches':dimensions, 'editable':editor,
            'sha256':{ext:sha256((OUT/f'{name}.{ext}').read_bytes()).hexdigest() for ext in ('svg','pdf','png','drawio')}}
    metadata['figures']['hazbot_arm_geometry']['geometry'] = arm_data
    metadata['figures']['hazbot_mission']['reference'] = {'phases':['SEARCH','APPROACH','DOCK','GRASP','CARRY','PLACE','COMPLETE'],'phase_count':7,'failed_guard_action':'HOLD in the current phase','evidence_scope':'Executable abstract reference model for surrogate evaluation; not deployed runtime'}
    metadata['source_sha256'] = {str(path.relative_to(BASE.parent)):sha256(path.read_bytes()).hexdigest() for path in [BASE.parent/'scripts/robot.urdf',BASE.parent/'scripts/arm_server.py',BASE.parent/'scripts/arduino_arm_controller/arduino_arm_controller.ino',BASE.parent/'motor_control/README.md',BASE.parent/'scripts/detect_live_picamera2.py',BASE.parent/'proposal_resources/Autonomous-Mobile-Manipulator-Engineering-Exam-Report.pdf',BASE.parent/'proposal_resources/HazBot_Presentation.pptx.pdf']}
    metadata['generator_sha256'] = {path.name:sha256(path.read_bytes()).hexdigest() for path in [Path(__file__),Path(__file__).with_name('hazbot_icons.py'),Path(__file__).with_name('export_drawio.py')]}
    return metadata


if __name__ == '__main__':
    print(json.dumps(render(),indent=2))
