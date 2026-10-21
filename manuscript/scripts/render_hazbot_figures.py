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
        self.extra_symbols = []
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
                f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>'+svg_symbols()+(''.join(self.extra_symbols))+f'<defs>{markers}</defs><g font-family="Noto Sans,sans-serif">'+''.join(self.parts)+'</g></svg>\n')


def architecture():
    """Separate physical interfaces from software measurements and commands."""
    g = Drawing(1420,800)
    g.text(22,31,'HAZBOT / HARDWARE INTERFACES AND NATIVE COMPUTE',24,bold=True)
    g.text(1398,31,'Four subsystems around one Raspberry Pi',19,MUTED,anchor='end')
    g.route([(22,52),(1398,52)],PALE,arrow=False,width=1.4)
    # One explicit compute boundary. Device wiring and software flow use
    # different stroke grammar rather than relying on colour alone.
    g.rect(566,100,300,531,'#f5f9f6','#b8cdbf',radius=8)
    g.text(716,138,'RASPBERRY PI',25,bold=True,anchor='middle')
    g.text(716,164,'Native inference + I/O services',19,MUTED,anchor='middle')
    g.icon('pi',641,178,146)
    g.text(716,339,'RGB conversion / resize',20,anchor='middle')
    g.route([(716,312),(716,319)],BLUE,True,width=2.5)
    g.text(716,380,'INT8 TFLite detector',21,bold=True,anchor='middle')
    g.route([(716,346),(716,360)],BLUE,True,width=2.5)
    g.text(716,429,'Boxes + class + confidence',19.5,anchor='middle')
    g.route([(716,389),(716,408)],BLUE,True,width=2.5)
    g.text(716,485,'Bearing / range association',19.5,bold=True,anchor='middle')
    g.route([(716,438),(716,463)],BLUE,True,width=2.5)
    g.text(716,538,'Navigation / motion I/O',20.5,bold=True,anchor='middle')
    g.route([(716,494),(716,516)],TEAL,True,width=2.5)
    g.text(716,593,'ROS 2 + serial services',19.5,MUTED,anchor='middle')
    g.text(716,657,'Reference mission shown separately',18.5,MUTED,anchor='middle')
    # 01: direct camera wiring and the actual capture format. Model tensor
    # dimensions are read from its external file, so none are invented here.
    g.sector(25,93,'01','VISION / LOCAL ML',BLUE)
    g.icon('camera',59,132,171)
    g.text(146,330,'Pi Camera V2',22,bold=True,anchor='middle')
    g.route([(215,211),(540,211),(540,231),(658,231)],GRAY,arrow=False,width=3)
    g.text(365,194,'CSI ribbon',20,BLUE,anchor='middle')
    g.text(357,275,'640 × 480 capture',21,bold=True,anchor='middle')
    g.text(357,307,'Capture / inference on Pi',19.5,MUTED,anchor='middle')
    g.text(25,384,'Visual estimates: box / class / bearing',19.5,BLUE)
    # 02: the scanner MCU and USB-UART bridge transport samples; the Pi
    # performs parsing/association. CP2102 is not a navigation processor.
    g.sector(948,93,'02','RANGING / NAVIGATION',TEAL)
    g.icon('controller',991,145,108)
    g.icon('lidar',1202,125,164)
    g.route([(1212,209),(1090,209)],GRAY,arrow=True,width=3)
    g.text(1150,189,'Packets',19.5,TEAL,anchor='middle')
    g.text(1047,304,'Built-in ranging MCU',20,bold=True,anchor='middle')
    g.text(1283,330,'YDLidar X4',22,bold=True,anchor='middle')
    g.route([(999,218),(905,218),(905,242),(790,242)],GRAY,arrow=True,width=3)
    g.text(1039,269,'CP2102 USB–UART → USB',19,TEAL,anchor='middle')
    g.text(1124,379,'Scan parsing: angular range samples',19.5,TEAL,anchor='middle')
    g.route([(1123,391),(912,391),(912,479),(858,479)],TEAL,True,width=2.5)
    g.text(1124,424,'Clearance and target-range inputs',19,MUTED,anchor='middle')
    # 03: solid command interfaces retain physical direction. Dedicated
    # Arduino boards avoid conflicting servo and motor use of D9-D12.
    g.sector(25,492,'03','WHEEL DRIVE',GOLD)
    g.icon('arduino',67,585,110)
    g.icon('driver',254,585,110)
    g.icon('drive',433,581,115)
    g.route([(661,265),(575,265),(575,552),(123,552),(123,597)],GOLD,width=2.9)
    g.text(335,537,'Pi → drive MCU: direction commands',19.5,GOLD,anchor='middle')
    g.text(335,578,'USB serial / 9600 baud',19,MUTED,anchor='middle')
    g.route([(173,638),(265,638)],GOLD,width=2.9)
    g.text(220,618,'PWM / DIR',19,GOLD,anchor='middle')
    g.route([(358,638),(444,638)],GOLD,width=2.9)
    g.text(401,618,'Power',19,GOLD,anchor='middle')
    g.text(122,721,'Drive Arduino',21,bold=True,anchor='middle')
    g.text(308,721,'L298N driver',21,bold=True,anchor='middle')
    g.text(490,721,'DC wheel pair',21,bold=True,anchor='middle')
    g.text(25,750,'Separate low-level drive service; F / B / L / R / S',19,MUTED)
    # 04: commanded joint state is software state, not measured encoder or
    # contact feedback. No feedback loop is invented in this schematic.
    g.sector(948,492,'04','ARM / GRIPPER',RED)
    g.icon('arduino',957,585,110)
    g.icon('arm',1196,535,172)
    g.route([(781,281),(852,281),(852,552),(1013,552),(1013,597)],RED,width=2.9)
    g.text(1120,537,'Pi → arm MCU: joint commands',19.5,RED,anchor='middle')
    g.text(935,578,'USB, 115200 baud',19,MUTED,anchor='middle')
    g.route([(1063,639),(1208,639)],RED,width=2.9)
    g.text(1135,619,'Servo pulses',19,RED,anchor='middle')
    g.text(1011,721,'Arm Arduino',21,bold=True,anchor='middle')
    g.text(1282,721,'3 axes + gripper',21,bold=True,anchor='middle')
    g.text(948,750,'B / S / A / G channels; dedicated D9–D12',19,MUTED)
    g.route([(22,768),(1398,768)],PALE,arrow=False,width=1.4)
    g.route([(22,785),(70,785)],GRAY,arrow=False,width=3)
    g.text(82,792,'Physical interface',19,MUTED)
    g.route([(366,785),(414,785)],TEAL,True,width=2.5)
    g.text(426,792,'Software data flow',19,MUTED)
    g.route([(764,785),(812,785)],GOLD,width=2.7)
    g.text(824,792,'Pi → MCU command direction',19,MUTED)
    g.text(1398,792,'Schematic',19,MUTED,anchor='end')
    return g.svg('HazBot physical interfaces and Raspberry Pi native processing',
        'Solid links identify physical interfaces; dashed arrows identify software measurement/data flow. '
        'Camera V2 connects directly by CSI and captures 640 by 480 frames. RGB conversion/resizing, INT8 TFLite '
        'inference, box/class/confidence extraction and bearing/range association execute on Pi. '
        'The scanner built-in MCU supplies packets through CP2102 USB-UART and USB; parsing and navigation '
        'are Pi-side roles. This source-supported interface overview does not assert one validated angular schema. '
        'Separate drive and arm Arduino links use 9600 and 115200 baud respectively. The drive controls L298N '
        'PWM/direction and DC wheels; arm channels B/S/A/G drive base, shoulder, elbow and gripper. '
        'The reference mission is shown separately, not claimed to be integrated runtime. '
        'No inferred encoder/contact feedback, arbitrary hazard detector, calibrated performance or physical testing is shown.')


def arm_geometry():
    """Source coordinates, fixed wrist frame, limits and rotation directions."""
    import math
    import xml.etree.ElementTree as ET
    urdf_path = BASE.parent / 'scripts' / 'robot.urdf'
    tree = ET.parse(urdf_path)
    joints = {joint.attrib['name']:joint for joint in tree.getroot().findall('joint')}
    def origin(name):
        return [float(v) for v in joints[name].find('origin').attrib['xyz'].split()]
    limits = {name:[float(joints[name].find('limit').attrib[key]) for key in ('lower','upper')]
              for name in ('base_joint','shoulder_joint','elbow_joint')}
    shoulder_x = origin('chassis_to_arm_mount')[0]
    shoulder_z = sum(origin(name)[2] for name in ('chassis_to_arm_mount','base_joint','shoulder_joint'))
    l1 = origin('elbow_joint')[2]
    l2 = origin('wrist_joint')[0]
    assert joints['wrist_joint'].attrib['type'] == 'fixed'
    g = Drawing(690,510)
    g.text(19,29,'ARM / JOINT FRAMES AND WRIST ENVELOPE',22,bold=True)
    g.text(19,57,'Zero coordinates; sagittal projection (q1 = 0)',19,MUTED)
    sx,sy = 195,350
    scale = 2000
    ex,ey = sx,sy-l1*scale
    wx,wy = ex+l2*scale,ey
    g.rect(sx-14,ey,28,sy-ey,'#d0dce4',INK,radius=2)
    g.rect(ex,ey-14,wx-ex,28,'#d0dce4',INK,radius=2)
    g.route([(sx-5,sy-20),(sx-5,ey+10)],'#f9fbfc',arrow=False,width=4)
    g.route([(ex+16,ey-5),(wx-8,ey-5)],'#f9fbfc',arrow=False,width=4)
    g.icon('pedestal',sx-47,sy+6,94)
    g.icon('joint',sx-22,sy-22,44)
    g.icon('joint',ex-22,ey-22,44)
    g.rect(wx,wy-13,47,26,'#667d8d',INK,radius=1)
    g.route([(wx+47,wy-8),(wx+62,wy-25),(wx+108,wy-25),(wx+108,wy-12)],GOLD,arrow=False,width=5)
    g.route([(wx+47,wy+8),(wx+62,wy+25),(wx+108,wy+25),(wx+108,wy+12)],GOLD,arrow=False,width=5)
    g.text(164,137,'Elbow q3',20,bold=True,anchor='end')
    g.text(247,358,'Shoulder q2',20,bold=True)
    g.text(492,95,'Fixed wrist W',20,bold=True,anchor='middle')
    # Coordinate directions identify the analytical endpoint explicitly.
    g.route([(wx,wy),(wx+62,wy)],TEAL,width=1.9)
    g.route([(wx,wy),(wx,wy-52)],TEAL,width=1.9)
    g.text(wx+67,wy+7,'xW',18.5,TEAL)
    g.text(wx-8,wy-57,'zW',18.5,TEAL,anchor='end')
    g.route([(wx-5,wy),(wx+5,wy)],INK,arrow=False,width=2.5)
    g.route([(wx,wy-5),(wx,wy+5)],INK,arrow=False,width=2.5)
    g.text(550,208,'Gripper qG',20,bold=True,anchor='middle')
    g.route([(550,187),(550,174),(505,174)],GRAY,arrow=False,width=1.6)
    # Sampled arcs are native editable polylines, not raster annotations.
    def arc(cx,cy,rx,ry,start,end,color=BLUE):
        angles=[math.radians(start+(end-start)*i/20) for i in range(21)]
        g.route([(round(cx+rx*math.cos(a),3),round(cy+ry*math.sin(a),3)) for a in angles],color,width=1.9)
    arc(sx,sy,39,39,-90,-20)
    arc(ex,ey,40,40,5,73)
    arc(sx,sy+57,53,14,205,338)
    g.route([(105,ey),(105,sy)],MUTED,arrow=False,width=1.6)
    for y in (ey,sy):
        g.route([(94,y),(117,y)],MUTED,arrow=False,width=1.6)
    g.text(87,240,'L1',20,bold=True,anchor='end')
    g.text(87,267,f'{l1*1000:g} mm',19,MUTED,anchor='end')
    g.route([(ex,220),(wx,220)],MUTED,arrow=False,width=1.6)
    for x in (ex,wx):
        g.route([(x,209),(x,231)],MUTED,arrow=False,width=1.6)
    g.text((ex+wx)/2,255,f'L2 = {l2*1000:g} mm',20,bold=True,anchor='middle')
    # Small supporting inset: retained joint-space samples of wrist-origin
    # geometry, rather than a second large workspace panel in the paper.
    import csv
    workspace_path = BASE / 'data' / 'hazbot_workspace.csv'
    with workspace_path.open(newline='') as stream:
        workspace_rows = [row for row in csv.DictReader(stream)
                          if abs(float(row['base_rad'])) < 1e-12]
    assert len(workspace_rows) == 1681
    plot_x,plot_y,plot_size = 455,244,190
    xmin,xmax,zmin,zmax = -110,310,-55,365
    scale_px = plot_size/(xmax-xmin)
    assert (zmax-zmin) == (xmax-xmin)
    # All points remain native circle geometry inside a movable vector symbol.
    # Labels and axis lines remain native draw.io text/connectors.
    marks=[]
    below_count=0
    for row in workspace_rows:
        x,z = 1000*float(row['wrist_x_m']),1000*float(row['wrist_z_m'])
        below = int(row['below_base_ground_plane']) == 1
        assert below == (z < 0)
        below_count += int(below)
        cx,cy = (x-xmin)*scale_px,(zmax-z)*scale_px
        marks.append(f'<circle cx="{cx:.5f}" cy="{cy:.5f}" r="{1.02 if below else .72}" fill="{RED if below else TEAL}" fill-opacity="{.85 if below else .58}"/>')
    center_x=(shoulder_x*1000-xmin)*scale_px
    center_y=(zmax-shoulder_z*1000)*scale_px
    radius=(l1+l2)*1000*scale_px
    bound=f'<circle cx="{center_x:.5f}" cy="{center_y:.5f}" r="{radius:.5f}" fill="none" stroke="{GRAY}" stroke-width=".85" stroke-dasharray="3 2"/>'
    g.extra_symbols.append(f'<defs><symbol id="hazbot-wrist-envelope" viewBox="0 0 190 190">{bound}'+''.join(marks)+'</symbol></defs>')
    g.parts.append(f'<use href="#hazbot-wrist-envelope" x="{plot_x}" y="{plot_y}" width="{plot_size}" height="{plot_size}"/>')
    g.text(550,231,'Wrist envelope / yaw 0',17.5,bold=True,anchor='middle')
    # Sparse frame axes preserve a physically equal scale while keeping the
    # intentionally small inset readable beside the arm.
    ground_y=plot_y+(zmax-0)*scale_px
    g.route([(plot_x,ground_y),(plot_x+plot_size,ground_y)],RED,True,arrow=False,width=.85)
    g.route([(plot_x,plot_y),(plot_x,plot_y+plot_size),(plot_x+plot_size,plot_y+plot_size)],GRAY,arrow=False,width=1)
    for value in (0,200):
        tick_x=plot_x+(value-xmin)*scale_px
        tick_y=plot_y+(zmax-value)*scale_px
        g.route([(tick_x,434),(tick_x,438)],GRAY,arrow=False,width=1)
        g.route([(451,tick_y),(455,tick_y)],GRAY,arrow=False,width=1)
        g.text(tick_x,450,str(value),15.5,MUTED,anchor='middle')
        g.text(448,tick_y+5,str(value),15.5,MUTED,anchor='end')
    g.text(462,259,'z (mm)',15.5,MUTED)
    g.text(662,450,'x (mm)',15.5,MUTED,anchor='end')
    g.text(281,411,'Base yaw q1',20,bold=True)
    g.text(281,438,'Out-of-plane yaw',18.5,MUTED)
    g.route([(247,407),(271,407)],GRAY,arrow=False,width=1.7)
    # Orientation indicator, deliberately separate from the modeled origin.
    g.route([(54,421),(104,421)],GRAY,width=1.8)
    g.route([(54,421),(54,372)],GRAY,width=1.8)
    g.text(111,427,'xB',18.5,MUTED)
    g.text(44,367,'zB',18.5,MUTED,anchor='end')
    g.route([(20,460),(670,460)],PALE,arrow=False,width=1.4)
    g.text(20,485,f'Shoulder S = ({shoulder_x*1000:g}, 0, {shoulder_z*1000:g}) mm in base_link',19,MUTED)
    g.text(20,507,'W: fixed wrist origin; TCP / jaw reach uncalibrated.',19,MUTED)
    metadata = {'source':'scripts/robot.urdf','source_sha256':sha256(urdf_path.read_bytes()).hexdigest(),
        'reference_joint_coordinates_rad':{'base_joint':0,'shoulder_joint':0,'elbow_joint':0},
        'positioning_joint_count':3,'wrist_joint_type':'fixed','gripper_channels':1,
        'segment_lengths_m':[l1,l2],'shoulder_frame_m':[shoulder_x,0,shoulder_z],
        'fixed_wrist_origin_m':[shoulder_x+l2,0,shoulder_z+l1],'joint_limits_rad':limits,
        'workspace_inset':{'input':'data/hazbot_workspace.csv','sha256':sha256(workspace_path.read_bytes()).hexdigest(),
            'pose_count':len(workspace_rows),'below_ground_count':below_count,
            'selection':'abs(base_rad) < 1e-12','endpoint':'arm_wrist_link origin',
            'frame':'base_link','bounds_mm':{'x':[xmin,xmax],'z':[zmin,zmax]},
            'equal_axis_scaling':True,'size_inches':[.95,.95],
            'pose_ids':[int(row['pose_id']) for row in workspace_rows],
            'point_geometry':'Native SVG circles; vector symbol independently movable in draw.io; labels and axes are native editable cells',
            'red_points':'below the modeled base ground plane; retained, not feasibility filtered'},
        'visual_geometry':'Source-scaled positioning segments with frame directions; pedestal and jaws schematic',
        'rotation_arcs':'Positive joint-direction symbols, not measured joint displacements',
        'reference_is_performance_result':False}
    return g.svg('HazBot arm source geometry, joint limits and fixed wrist endpoint',
        'Zero-coordinate source geometry uses a vertical 100mm shoulder-to-elbow link and horizontal '
        '100mm elbow-to-fixed-wrist link. Shoulder S is x100mm,z155mm; fixed-wrist origin W is x200mm,z255mm. '
        'Local xW,zW and a base-axis orientation indicator are shown. A small equal-scale yaw-zero inset retains all 1681 sampled wrist origins; 67 below-ground points are red. Positive pitch arrows and base yaw '
        'are schematic rotation directions. Exact source radian limits remain in the figure metadata and paper method. '
        'There are three positioning axes plus a gripper channel, no active wrist, and no calibrated grasp TCP.'),metadata


def mission_flow():
    """Expose exact reference transition commands and base/arm handoffs."""
    g = Drawing(1420,380)
    g.text(22,29,'REFERENCE MISSION / BASE–ARM CONTROL HANDOFF',23,bold=True)
    g.text(1398,29,'SURROGATE EVALUATION',20,MUTED,anchor='end')
    g.route([(22,48),(1398,48)],PALE,arrow=False,width=1.4)
    centers=[110,310,510,710,910,1110,1310]
    phases=[('SEARCH','rotate / hold',BLUE),('APPROACH','advance',BLUE),
            ('DOCK','verify handoff',TEAL),('GRASP','close_gripper',TEAL),
            ('CARRY','transport',GOLD),('PLACE','open_gripper',GOLD),
            ('COMPLETE','hold',TEAL)]
    # Preconditions above the inter-phase links; issued transition commands
    # below the links. In-phase actions remain below the phase names.
    guards=[('fresh + authorized','target','hold'),('at_pick_zone','','stop_base'),
            ('stopped + reachable','target','reach'),('grip_confirmed','','stow_arm'),
            ('at_drop_zone','','stop_base'),('release_confirmed','','hold')]
    for midpoint,(line1,line2,command) in zip([200,400,600,800,1000,1200],guards):
        g.text(midpoint,78,line1,19,INK,anchor='middle')
        if line2: g.text(midpoint,101,line2,19,MUTED,anchor='middle')
        g.route([(midpoint-43,155),(midpoint+43,155)],GRAY,width=2.4)
        g.text(midpoint,184,command,18.5,TEAL,anchor='middle')
    g.icon('camera',64,108,86); g.icon('object',112,150,48)
    g.icon('drive',266,110,88)
    g.icon('drive',466,113,82)
    g.route([(553,145),(553,178),(571,178)],GRAY,arrow=False,width=2.4)
    g.icon('arm',665,108,92)
    g.icon('drive',865,114,88); g.icon('object',888,110,44)
    g.icon('arm',1058,110,88); g.icon('container',1113,148,54)
    g.icon('container',1262,109,96)
    g.route([(1293,154),(1306,168),(1337,134)],TEAL,arrow=False,width=4.5)
    for x,(phase,action,color) in zip(centers,phases):
        g.text(x,237,phase,21.5,color,True,'middle')
        g.text(x,268,action,19.5,INK,anchor='middle')
    g.route([(22,290),(1398,290)],PALE,arrow=False,width=1.4)
    g.text(22,320,'Motion interlock:',19.5,INK,True)
    g.text(196,320,'base motion requires arm_stowed; arm actions require base_stopped.',19.5,MUTED)
    g.rect(22,342,67,25,'#fbf3e5','#d7c49f',radius=3)
    g.text(55.5,362,'HOLD',18.5,GOLD,True,'middle')
    g.text(105,362,'Blocked guards keep the phase; hold is abstract inhibition, not verified physical stopping.',19.5,MUTED)
    return g.svg('Reference mission transition guards, actions and base-arm handoffs',
        'Abstract reference model for nonhazardous surrogate evaluation, separate from runtime integration. '
        'Above-link text shows selected transition prerequisites; below-link text shows commands. '
        'At the pick zone APPROACH issues stop_base and enters DOCK. A stopped base plus fresh authorized '
        'reachable target and usable fresh scan permit reach and GRASP. GRASP closes the gripper until '
        'grip_confirmed; transition to CARRY issues stow_arm. CARRY transport cannot begin until arm_stowed, '
        'and at the drop zone it issues stop_base. PLACE opens the gripper under its full prerequisites; '
        'release confirmation reaches absorbing COMPLETE with hold. HOLD inhibits commands abstractly '
        'and can accompany acquisition/completion handoffs; blocked guards preserve the phase. It is not physical stopping or contact sensing.')


def render(data=None):
    """Return renderer metadata; generate deterministic SVG/PDF/PNG/draw.io."""
    OUT.mkdir(exist_ok=True)
    env = dict(os.environ,SOURCE_DATE_EPOCH=EPOCH)
    metadata = {'renderer':'Original Python-authored SVG; librsvg vector export',
        'font':'Noto Sans', 'data_used':'Hardware source, URDF, engineering report and user architecture clarification',
        'figures':{}}
    arm_svg,arm_data = arm_geometry()
    for name, body, dimensions in [('hazbot_architecture',architecture(),[7.1,4.0]),('hazbot_arm_geometry',arm_svg,[3.45,2.55]),('hazbot_mission',mission_flow(),[7.1,1.9])]:
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
