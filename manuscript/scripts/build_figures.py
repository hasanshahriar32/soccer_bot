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
from annotate_prototype import render as render_prototype, render_front, render_dashboard

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
        if extension == 'svg':
            path = OUT/f'{name}.svg'
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
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

    fig = plt.figure(figsize=(3.45,2.55))
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
        'prototype':render_prototype(),
        'front':render_front(),
        'dashboard':render_dashboard(),
    }
    (DATA/'figure_data.json').write_text(json.dumps(records,indent=2)+'\n')
    stems = {'hazbot_architecture':True,'hazbot_mission':True,'hazbot_arm_geometry':True,
             'hazbot_workspace':False,'hazbot_prototype':True,'hazbot_front':True,
             'hazbot_dashboard':True}
    dimensions = {name: records['diagrams']['figures'][name]['dimensions_inches']
                  for name in ('hazbot_architecture','hazbot_mission','hazbot_arm_geometry')}
    dimensions['hazbot_workspace'] = [3.45,2.55]
    dimensions['hazbot_prototype'] = records['prototype']['dimensions_inches']
    dimensions['hazbot_front'] = records['front']['dimensions_inches']
    dimensions['hazbot_dashboard'] = records['dashboard']['dimensions_inches']
    inputs = [DATA/name for name in ('hazbot_characterization.json','hazbot_workspace.csv',
                                    'hazbot_height_slabs.csv')]
    scripts = [Path(__file__).resolve(),BASE/'scripts/render_hazbot_figures.py',BASE/'scripts/annotate_prototype.py',
               BASE/'scripts/hazbot_icons.py',BASE/'scripts/export_drawio.py']
    exports = [OUT/f'{stem}.{suffix}' for stem in stems for suffix in ('pdf','svg','png')]
    exports += [OUT/f'{stem}.drawio' for stem in ('hazbot_architecture','hazbot_mission','hazbot_arm_geometry')]
    exports += [DATA/'figure_data.json', DATA/'prototype_annotation.json', DATA/'front_annotation.json']
    source_bindings = {record['path']:record['sha256'] for record in characterization['source_bindings'].values()}
    source_bindings.update(records['diagrams']['source_sha256'])
    assert records['prototype']['available'], 'Source prototype photo is required to refresh its annotation.'
    source_bindings[records['prototype']['source_path']] = records['prototype']['source_sha256']
    assert records['front']['available'], 'Front-view source photo is required.'
    source_bindings[records['front']['source_path']] = records['front']['source_sha256']
    manifest = {
        'generator':'Original Python-authored technical SVG + librsvg; Matplotlib source plots; original JPEG with vector annotations',
        'study':'HazBot source-derived architecture and geometric/interface characterization',
        'python_version':platform.python_version(),'matplotlib_version':matplotlib.__version__,
        'numpy_version':np.__version__,
        'librsvg_version':subprocess.check_output(['rsvg-convert','--version'],text=True).strip(),
        'settings':{'technical_preview_dpi':300,'photo_preview':'native input dimensions','pdf_plot_fonttype':42,'svg_plot_fonttype':'none',
                    'svg_hashsalt':'hazbot-source-figures-v1','rasterized_plot_artists':False,
                    'diagram_primary_font':'Noto Sans','plot_primary_font':'DejaVu Sans',
                    'creation_and_modification_metadata':'Fixed diagram SOURCE_DATE_EPOCH; omitted plot timestamps'},
        'figures':{name:{'in_paper':paper,'dimensions_inches':dimensions[name],
                        'media_type':'real photograph with vector annotations' if name in ('hazbot_prototype','hazbot_front') else 'vector technical figure'}
                   for name,paper in stems.items()},
        'inputs_sha256':{str(path.relative_to(BASE)):digest(path) for path in inputs},
        'source_evidence_sha256':source_bindings,
        'scripts_sha256':{str(path.relative_to(BASE)):digest(path) for path in scripts},
        'outputs_sha256':{str(path.relative_to(BASE)):digest(path) for path in exports},
    }
    (DATA/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Generated four technical vector sets, two compact photo annotations, and three editable diagrams.')
    print('Main paper: architecture, reference mission, arm with small wrist inset, and two compact annotated photographs.')
    print('Bound figure inputs, source evidence, generators and exports: manuscript/data/figure_manifest.json')


if __name__ == '__main__':
    main()
