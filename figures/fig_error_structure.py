r"""Nature-format figure: human typing error is two processes, not one channel.

Specification: 183 mm double-column width, Arial, colourblind-safe (Okabe-Ito),
vector PDF with EMBEDDED fonts (pdf.fonttype=42 -> /FontFile2), 600 dpi PNG,
300 dpi LZW TIFF, bold lowercase panel letters, thin axes, outward ticks.

Saved WITHOUT bbox_inches='tight' so the PDF MediaBox is exactly 183 mm.

Every number traces to:
  trans_aware.json    transposition-aware class mix
  fig_data.json       cluster-bootstrap ratios + word-length curve
  h1h2.json           length and position profiles
  decisive.json       truncation control, correction latency
  error_structure2.json  backspace totals
Corrections from docs/ERROR_STRUCTURE_VERIFICATION.md are applied, including
the RETRACTED word-initial 3.7x claim and the one-event-per-error convention.
"""
import json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from pathlib import Path

HERE = Path(__file__).resolve().parent
MM = 1/25.4
W_MM, H_MM = 183.0, 120.0
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 6,
    'axes.labelsize': 6,
    'axes.titlesize': 6.5,
    'xtick.labelsize': 5.5,
    'ytick.labelsize': 5.5,
    'legend.fontsize': 5.5,
    'axes.linewidth': 0.5,
    'xtick.major.width': 0.5, 'ytick.major.width': 0.5,
    'xtick.major.size': 2, 'ytick.major.size': 2,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'figure.dpi': 600,
    # embed TrueType in the PDF (Nature requirement); default is Type 3
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})
BLUE, VERM, GREEN, PURPLE, ORANGE, SKY, YELLOW, BLACK = (
    '#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9','#F0E442','#000000')

ta  = json.load(open(HERE / 'data' / 'trans_aware.json'))
fd  = json.load(open(HERE / 'data' / 'fig_data.json'))
h   = json.load(open(HERE / 'data' / 'h1h2.json'))
dec = json.load(open(HERE / 'data' / 'decisive.json'))
es2 = json.load(open(HERE / 'data' / 'error_structure2.json'))
posdat = json.load(open(HERE / 'data' / 'pos_all_classes.json'))

# ONE EVENT PER ERROR for every class. Counting a transposition as 2 opcodes
# inflates it to 8.8%; as events it is 4.6%, comparable with the others.
_n = ta['cls']
cls = {'deletion': _n['del_align'], 'insertion': _n['ins_align'], 'case': _n['case'],
       'transposition': _n['transposition']/2.0, 'adjacent': _n['adjacent'],
       'other_sub': _n['other_sub']}
tot = sum(cls.values())

fig = plt.figure(figsize=(W_MM*MM, H_MM*MM))
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.72, wspace=0.52,
                       left=0.075, right=0.985, top=0.905, bottom=0.105)

def letter(ax, s):
    ax.text(-0.34, 1.26, s, transform=ax.transAxes, fontsize=8,
            fontweight='bold', va='top', ha='left')

def tidy(ax):
    for sp in ('top','right'): ax.spines[sp].set_visible(False)

def note(ax, txt, y=0.03, color='0.35'):
    ax.text(0.99, y, txt, transform=ax.transAxes, ha='right', va='bottom',
            fontsize=4.6, color=color, linespacing=1.3)

# ---------------- (a) measured composition ----------------
ax = fig.add_subplot(gs[0,0])
order = [('deletion','deletion',BLUE), ('insertion','insertion',SKY),
         ('case','case',ORANGE), ('transposition','transposition',GREEN),
         ('adjacent','adjacent key',VERM), ('other_sub','other',PURPLE)]
vals = [100*cls[k]/tot for k,_,_ in order]
y = np.arange(len(vals))[::-1]
ax.barh(y, vals, color=[c for _,_,c in order], height=0.66)
for yi, v in zip(y, vals):
    ax.text(v+0.7, yi, f'{v:.1f}', va='center', fontsize=5.5)
ax.set_yticks(y); ax.set_yticklabels([l for _,l,_ in order])
ax.set_xlabel('Share of surviving errors (%)'); ax.set_xlim(0, 41)
ax.set_title('Residual error composition', pad=6)
tidy(ax); letter(ax,'a')
note(ax, 'one event per error')

# ---------------- (b) measured vs generator ----------------
ax = fig.add_subplot(gs[0,1])
meas = {k: 100*cls[k]/tot for k in cls}
syn  = {'deletion':20,'insertion':20,'case':0,'transposition':25,'adjacent':35,'other_sub':0}
keys = ['adjacent','transposition','deletion','insertion','case','other_sub']
lab  = ['adjacent','transposition','deletion','insertion','case','other']
x = np.arange(len(keys)); w = 0.38
ax.bar(x-w/2, [syn[k] for k in keys], w, color='0.72', label='N_en generator')
ax.bar(x+w/2, [meas[k] for k in keys], w, color=BLUE, label='measured')
for xi, k in zip(x, keys):
    ax.text(xi+w/2, meas[k]+0.9, f'{meas[k]:.0f}', ha='center', fontsize=5)
    if syn[k] > 0:
        ax.text(xi-w/2, syn[k]+0.9, f'{syn[k]}', ha='center', fontsize=5, color='0.3')
    else:
        ax.text(xi-w/2, 1.2, 'absent', ha='center', fontsize=4.4, color=VERM, rotation=90)
ax.axvspan(-0.5, 1.5, color=GREEN, alpha=0.08)
ax.axvspan(1.5, 3.5, color=BLUE, alpha=0.08)
ax.set_xticks(x); ax.set_xticklabels(lab, rotation=34, ha='right')
ax.set_ylabel('Share (%)'); ax.set_ylim(0, 44)
ax.set_title('Generator vs measurement', pad=6)
ax.text(0.17, 0.955, 'geometry', transform=ax.transAxes, ha='center', fontsize=5,
        color=GREEN, fontweight='bold')
ax.text(0.60, 0.955, 'structure', transform=ax.transAxes, ha='center', fontsize=5,
        color=BLUE, fontweight='bold')
ax.legend(frameon=False, loc='upper right', bbox_to_anchor=(1.03, 0.83), handlelength=1.1)
tidy(ax); letter(ax,'b')

# ---------------- (c) the double dissociation ----------------
ax = fig.add_subplot(gs[0,2])
L = np.array([2,3,4,5,6,8,10,12])
for key, lab_, col, mk in [('adjacent','adjacent key',VERM,'o'),
                           ('deletion','deletion',BLUE,'s'),
                           ('insertion','insertion',SKY,'^')]:
    ax.plot(L, fd['curve'][key], marker=mk, ms=2.8, lw=1.0, color=col, label=lab_)
ax.set_xlabel('Word length (characters)')
ax.set_ylabel('Errors per 1,000 characters')
ax.set_title('Geometry is length-blind; structure scales', pad=6)
ax.set_xticks(L); ax.set_ylim(0, 7.4); ax.set_xlim(1.4, 12.6)
ax.legend(frameon=False, loc='upper left', handlelength=1.4)
tidy(ax); letter(ax,'c')
ax.annotate('flat (0.98x)', xy=(11.0, 1.16), xytext=(6.3, 0.42), fontsize=5,
            color=VERM, arrowprops=dict(arrowstyle='-', lw=0.5, color=VERM))
ax.annotate('4.9x', xy=(12, 5.01), xytext=(9.0, 6.35), fontsize=5, color=SKY,
            arrowprops=dict(arrowstyle='-', lw=0.5, color=SKY))

# ---------------- (d) population-level ratios ----------------
ax = fig.add_subplot(gs[1,0])
bs = fd['bootstrap']
names = [('adjacent','adjacent key',VERM), ('deletion','deletion',BLUE), ('insertion','insertion',SKY)]
ys = np.arange(len(names))[::-1]
for yi, (k, lab_, col) in zip(ys, names):
    r, lo, hi = bs[k]['ratio'], bs[k]['lo'], bs[k]['hi']
    ax.plot([lo, hi], [yi, yi], color=col, lw=1.5, solid_capstyle='butt')
    ax.plot([r], [yi], marker='o', ms=4, color=col)
    ax.text(hi+0.08, yi, f'{r:.2f}', va='center', fontsize=5.5, color=col)
ax.axvline(1.0, color=BLACK, lw=0.6, ls=(0,(4,3)))
ax.set_yticks(ys); ax.set_yticklabels([l for _,l,_ in names])
ax.set_xlabel('Long/short word error-rate ratio'); ax.set_xlim(0.82, 3.75)
ax.set_title('Population-level, participant-clustered', pad=6)
tidy(ax); letter(ax,'d')
ax.text(0.985, 0.985, '95% CI, 2,000 participant-cluster\nbootstrap replicates; n = 20,000',
        transform=ax.transAxes, ha='right', va='top', fontsize=4.6, color='0.35',
        linespacing=1.3)

# ---------------- (e) position profile ----------------
ax = fig.add_subplot(gs[1,1])
pos = ['first','middle','last']
# ONE consistent numerator convention: every class is attributed to a position,
# matching the overall class mix. (An earlier version counted positions only in
# the replace/delete branches, silently dropping insertions -- flagged by the
# verifier.) Truncation excluded; case shown as its own series.
xs_ = np.arange(3); w = 0.36
_exp = posdat['expo']
allr = [1000*posdat['err_all'][p]/_exp[p] for p in pos]
ncr  = [1000*posdat['err_nocase'][p]/_exp[p] for p in pos]
ax.bar(xs_-w/2, allr, w, color='0.72', label='all errors')
ax.bar(xs_+w/2, ncr, w, color=BLUE, label='case excluded')
for xi, a, b in zip(xs_, allr, ncr):
    ax.text(xi-w/2, a+0.35, f'{a:.1f}', ha='center', fontsize=5)
    ax.text(xi+w/2, b+0.35, f'{b:.1f}', ha='center', fontsize=5, color=BLUE)
ax.set_xticks(xs_); ax.set_xticklabels(['first','middle','last'])
ax.set_xlabel('Position within word')
ax.set_ylabel('Errors per 1,000 characters')
ax.set_title('Word-first is capitalisation, not error', pad=6)
ax.set_ylim(0, 22.5)
ax.legend(frameon=False, loc='upper left', handlelength=1.1)
tidy(ax); letter(ax,'e')
ax.text(0.98, 0.985, 'truncated transcriptions excluded',
        transform=ax.transAxes, ha='right', va='top', fontsize=4.6, color='0.35')
ax.text(0.5, -0.40, 'a 3.7x word-initial effect was RETRACTED (counter artefact)',
        transform=ax.transAxes, ha='center', va='top', fontsize=4.6, color=VERM)

# ---------------- (f) correction vs survival ----------------
ax = fig.add_subplot(gs[1,2])
S = es2['sections']
bs_per = es2['backspaces']/S
surv_per = tot/S
bars = ax.bar([0,1], [bs_per, surv_per], 0.55, color=[GREEN, ORANGE])
for xi, v in zip([0,1], [bs_per, surv_per]):
    ax.text(xi, v+0.07, f'{v:.2f}', ha='center', fontsize=6.5)
ax.set_xticks([0,1])
ax.set_xticklabels(['errors repaired\n(backspaces)', 'errors surviving\n(final text)'])
ax.set_ylabel('Per sentence')
ax.set_title('The text is the residual of a control loop', pad=6)
ax.set_ylim(0, 3.75)
tidy(ax); letter(ax,'f')
ax.annotate('', xy=(0.93, surv_per+0.12), xytext=(0.07, bs_per+0.12),
            arrowprops=dict(arrowstyle='->', lw=0.7, color='0.35',
                            connectionstyle='arc3,rad=-0.32'))
ax.text(0.50, 2.86, f'{bs_per/surv_per:.1f}x more errors repaired\nthan survive',
        ha='center', fontsize=5.4, color='0.25', linespacing=1.35)
ax.text(0.99, 0.30, '63.6% of sentences contain\nat least one backspace',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=4.6, color='0.35',
        linespacing=1.3)

out = Path(r'E:\2026-AI4S\autoresearch\figures')
out.mkdir(parents=True, exist_ok=True)
fig.savefig(out/'fig_error_structure.pdf')                      # exact figsize, no tight bbox
fig.savefig(out/'fig_error_structure.png', dpi=600)
fig.savefig(out/'fig_error_structure.tiff', dpi=300,
            pil_kwargs={'compression': 'tiff_lzw'})
print('saved')
