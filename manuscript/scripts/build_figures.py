#!/usr/bin/env python3
"""Generate the active HazBot technical figures from frozen source analysis.

No robot runtime module, ROS node, socket, hardware interface or model inference
is imported. The earlier SoccerBot case study is retained in manuscript/archive.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
import numpy as np

from render_hazbot_figures import render as render_diagrams

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
OUT = BASE/'figures'
DATA = BASE/'data'
INK = '#253748'; MUTED = '#627483'; BLUE = '#34799c'; TEAL = '#16858d'
GOLD = '#a87935'; RED = '#ac5c52'; PALE = '#dce5eb'

plt.rcParams.update({
    'font.family':'DejaVu Sans','font.size':7,'axes.labelsize':7,
    'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42,
    'svg.fonttype':'none','svg.hashsalt':'hazbot-source-figures-v1',
    'axes.spines.top':False,'axes.spines.right':False,
    'axes.edgecolor':'#b1bec7','axes.linewidth':.65,'axes.labelcolor':INK,
    'text.color':INK,'xtick.color':MUTED,'ytick.color':MUTED,
    'hatch.linewidth':.4,'path.simplify':False,
})


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(fig,name):
    for extension in ('pdf','svg','png'):
        metadata = {}
        if extension == 'pdf':
            metadata = {'Creator':'HazBot reproducible source-derived figure renderer',
                        'Author':'','CreationDate':None,'ModDate':None}
        elif extension == 'svg':
            metadata = {'Date':None,'Creator':'HazBot reproducible source-derived figure renderer'}
        fig.savefig(OUT/f'{name}.{extension}',dpi=300,facecolor='white',metadata=metadata)
    plt.close(fig)


def workspace_plot(characterization):
    with (DATA/'hazbot_workspace.csv').open(newline='') as stream:
        rows = [row for row in csv.DictReader(stream) if abs(float(row['base_rad'])) < 1e-12]
    expected = characterization['workspace']['grid']['points_per_joint']**2
    assert len(rows) == expected == 1681
    x = np.array([float(row['wrist_x_m'])*1000 for row in rows])
    z = np.array([float(row['wrist_z_m'])*1000 for row in rows])
    below = np.array([int(row['below_base_ground_plane']) == 1 for row in rows])
    assert np.array_equal(below,z < 0)
    geometry = characterization['workspace']['geometry']
    shoulder = np.array(geometry['shoulder_origin_m'])*1000
    reach = (geometry['upper_link_length_m']+geometry['forearm_length_m'])*1000
    assert np.max(np.hypot(x-shoulder[0],z-shoulder[2])) <= reach+1e-8

    fig = plt.figure(figsize=(3.45,2.25))
    # A square metric panel preserves the physical circular link bound; an
    # adjacent annotation column keeps text off the sampled envelope.
    ax = fig.add_axes([.16,.22,.55,.68])
    ax.set_aspect('equal',adjustable='box')
    ax.axhspan(-60,0,facecolor='#fbf1ef',zorder=0)
    ax.add_patch(Circle((shoulder[0],shoulder[2]),reach,fill=False,
                        edgecolor='#92a4b1',linewidth=.85,linestyle=(0,(3,2)),zorder=1))
    ax.scatter(x[~below],z[~below],s=2.4,c=TEAL,edgecolors='none',alpha=.47,
               rasterized=False,zorder=3)
    ax.scatter(x[below],z[below],s=5.2,c=RED,edgecolors='none',alpha=.85,
               rasterized=False,zorder=4)
    ax.axhline(0,color=RED,linewidth=.75,zorder=2)
    ax.plot(shoulder[0],shoulder[2],marker='+',color=INK,markersize=7,
            markeredgewidth=1.25,linestyle='none',zorder=6)
    ax.set(xlim=(-110,310),ylim=(-55,365),xticks=[-100,0,100,200,300],
           yticks=[0,100,200,300],xlabel='Wrist x in base frame (mm)',
           ylabel='Wrist z (mm)')
    ax.tick_params(length=2.3,pad=2)
    ax.grid(color='#e9eef1',linewidth=.45,zorder=0)
    fig.text(.035,.965,'MODEL WRIST ENVELOPE / YAW = 0',fontsize=8.1,
             fontweight='bold',va='top')
    tx = .735
    fig.text(tx,.845,f'{len(rows):,} poses',fontsize=8.1,fontweight='bold')
    fig.text(tx,.770,'41 × 41 pitch grid',fontsize=7,color=MUTED)
    fig.text(tx,.640,'200 mm',fontsize=8.1,fontweight='bold')
    fig.text(tx,.565,'Link-sum bound',fontsize=7,color=MUTED)
    fig.text(tx,.435,'Wrist origin',fontsize=7.3,fontweight='bold')
    fig.text(tx,.360,'TCP not calibrated',fontsize=7,color=MUTED)
    fig.text(tx,.245,'Joint samples;',fontsize=7,color=MUTED)
    fig.text(tx,.170,'no collision filter',fontsize=7,color=MUTED)
    handles = [Line2D([],[],ls='none',marker='o',ms=3.2,color=TEAL,
                      label=f'z ≥ 0: {int((~below).sum()):,}'),
               Line2D([],[],ls='none',marker='o',ms=3.2,color=RED,
                      label=f'z < 0: {int(below.sum()):,}'),
               Line2D([],[],ls='none',marker='+',ms=5,color=INK,label='Shoulder')]
    fig.legend(handles=handles,loc='lower left',bbox_to_anchor=(.028,-.005),
               ncol=3,frameon=False,fontsize=7,handlelength=.7,
               handletextpad=.4,columnspacing=.8)
    save(fig,'hazbot_workspace')
    return {'input':'data/hazbot_workspace.csv','selection':'abs(base_rad) < 1e-12',
            'endpoint':'arm_wrist_link origin','frame':'base_link',
            'pose_count':len(rows),'below_ground_count':int(below.sum()),
            'above_or_on_ground_count':int((~below).sum()),
            'shoulder_frame_mm':shoulder.tolist(),'link_sum_bound_mm':reach,
            'equal_axis_scaling':True,'pose_id':[int(row['pose_id']) for row in rows],
            'wrist_x_mm':x.tolist(),'wrist_z_mm':z.tolist(),
            'below_ground':below.astype(int).tolist(),
            'interpretation':'Joint-space samples of ideal source wrist-origin geometry; not a Cartesian density, safe grasp workspace, trajectory, tool-centre-point reach, or measured physical performance.'}


def protocol_plot(characterization):
    wheel = characterization['protocols']['wheel']
    counts = wheel['exhaustive_output_counts']
    assert sum(counts.values()) == wheel['exhaustive_cases'] == 511**2
    assert [counts[k] for k in ('F','B','L','R')] == [255**2]*4
    assert counts['NO_COMMAND'] == 4*255 and counts['S'] == 1
    fig = plt.figure(figsize=(3.45,2.40))
    ax = fig.add_axes([.19,.27,.61,.61])
    ax.set_aspect('equal',adjustable='box')
    quadrants = [(-255,0,'L','#edf3f8'),(0,0,'F','#e9f5f2'),
                 (-255,-255,'B','#f3f0e8'),(0,-255,'R','#f8ece8')]
    for x0,y0,command,color in quadrants:
        ax.add_patch(Rectangle((x0,y0),255,255,facecolor=color,edgecolor='none',zorder=1))
        cx,cy = x0+127.5,y0+127.5
        ax.text(cx,cy+18,command,ha='center',va='center',fontsize=12,fontweight='bold')
        ax.text(cx,cy-51,f'{counts[command]:,}',ha='center',va='center',fontsize=7.4,color=MUTED)
    ax.axvline(0,color=GOLD,lw=1.1,zorder=3)
    ax.axhline(0,color=GOLD,lw=1.1,zorder=3)
    ax.plot(0,0,'o',color=INK,markeredgecolor='white',markeredgewidth=.7,ms=4,zorder=5)
    ax.set(xlim=(-255,255),ylim=(-255,255),xticks=[-255,0,255],yticks=[-255,0,255],
           xlabel='Left signed input',ylabel='Right signed input')
    ax.tick_params(length=2.3,pad=2)
    fig.text(.035,.965,'WHEEL GATEWAY / EXACT SIGN PARTITION',fontsize=8.1,fontweight='bold',va='top')
    fig.text(.035,.085,'Axes except origin: 1,020 silent input pairs',fontsize=7,color=GOLD)
    fig.text(.035,.025,'Origin: S (stop) · nonzero magnitudes discarded',fontsize=7,color=MUTED)
    save(fig,'hazbot_protocol')
    return {'source':'protocols.wheel in data/hazbot_characterization.json',
            'input_interval_each_wheel':wheel['exhaustive_input_interval_each_wheel'],
            'exhaustive_cases':wheel['exhaustive_cases'],'output_counts':counts,
            'quadrants':{'left<0,right>0':'L','left>0,right>0':'F',
                         'left<0,right<0':'B','left>0,right<0':'R'},
            'axis_cases':'Exactly one zero input: NO_COMMAND; both zero: S',
            'interpretation':'Isolated gateway code semantics; not motor-speed, physical braking, or robot trajectory measurements.'}


def main():
    OUT.mkdir(exist_ok=True)
    characterization = json.loads((DATA/'hazbot_characterization.json').read_text())
    for name,record in characterization['datasets'].items():
        assert digest(DATA/name) == record['sha256'], f'Characterization dataset mismatch: {name}'
    for record in characterization['source_bindings'].values():
        assert digest(ROOT/record['path']) == record['sha256'], f'Source evidence mismatch: {record["path"]}'
    records = {
        'study':'HazBot modular edge-centred mobile manipulation',
        'semantics':'Source-derived component architecture and ideal wrist geometry; constructed reference mission. No live robot, inference, collision feasibility, hazardous-object recognition or physical handling evaluation.',
        'diagrams':render_diagrams(),
        'workspace':workspace_plot(characterization),
        'protocol':protocol_plot(characterization),
    }
    (DATA/'figure_data.json').write_text(json.dumps(records,indent=2)+'\n')
    stems = {'hazbot_architecture':True,'hazbot_mission':True,'hazbot_arm_geometry':True,
             'hazbot_workspace':True,'hazbot_protocol':False}
    dimensions = {'hazbot_architecture':[7.1,3.6],'hazbot_mission':[7.1,1.62],
                  'hazbot_arm_geometry':[3.45,2.25],'hazbot_workspace':[3.45,2.25],
                  'hazbot_protocol':[3.45,2.4]}
    inputs = [DATA/name for name in ('hazbot_characterization.json','hazbot_workspace.csv',
                                    'hazbot_protocol.csv','hazbot_height_slabs.csv')]
    scripts = [Path(__file__).resolve(),BASE/'scripts/render_hazbot_figures.py',
               BASE/'scripts/hazbot_icons.py',BASE/'scripts/export_drawio.py']
    exports = [OUT/f'{stem}.{suffix}' for stem in stems for suffix in ('pdf','svg','png')]
    exports += [OUT/f'{stem}.drawio' for stem in ('hazbot_architecture','hazbot_mission','hazbot_arm_geometry')]
    exports += [DATA/'figure_data.json']
    source_bindings = {record['path']:record['sha256'] for record in characterization['source_bindings'].values()}
    source_bindings.update(records['diagrams']['source_sha256'])
    manifest = {
        'generator':'Original Python-authored SVG + librsvg diagrams; Matplotlib native-vector source-derived plots',
        'study':'HazBot source-derived architecture and geometric/interface characterization',
        'python_version':platform.python_version(),'matplotlib_version':matplotlib.__version__,
        'numpy_version':np.__version__,
        'librsvg_version':subprocess.check_output(['rsvg-convert','--version'],text=True).strip(),
        'settings':{'preview_dpi':300,'pdf_plot_fonttype':42,'svg_plot_fonttype':'none',
                    'svg_hashsalt':'hazbot-source-figures-v1','rasterized_plot_artists':False,
                    'diagram_primary_font':'Noto Sans','plot_primary_font':'DejaVu Sans',
                    'creation_and_modification_metadata':'Fixed diagram SOURCE_DATE_EPOCH; omitted plot timestamps'},
        'figures':{name:{'in_paper':paper,'dimensions_inches':dimensions[name]} for name,paper in stems.items()},
        'inputs_sha256':{str(path.relative_to(BASE)):digest(path) for path in inputs},
        'source_evidence_sha256':source_bindings,
        'scripts_sha256':{str(path.relative_to(BASE)):digest(path) for path in scripts},
        'outputs_sha256':{str(path.relative_to(BASE)):digest(path) for path in exports},
    }
    (DATA/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Generated five active HazBot PDF/SVG/PNG figure sets and three editable diagrams.')
    print('Main paper: architecture, reference mission, arm geometry and sagittal wrist envelope.')
    print('Bound figure inputs, source evidence, generators and exports: manuscript/data/figure_manifest.json')


if __name__ == '__main__':
    main()
