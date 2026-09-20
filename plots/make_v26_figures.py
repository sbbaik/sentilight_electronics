"""Figures introduced for the implementation-centred revision: the Chat-to-Action asymmetry, the study flow, the
selected model's architecture, the generalisation boundary and the implementation cost.

All numbers are taken from the frozen result files; nothing here is a new measurement.
Outputs F13…F17 as PNG and PDF.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path
HERE = Path(__file__).resolve().parent
_k = [f.name for f in fm.fontManager.ttflist if any(x in f.name for x in ("Noto Sans CJK", "NanumGothic", "NanumBarunGothic"))]
plt.rcParams.update({"font.family": ([_k[0]] if _k else []) + ["DejaVu Sans"], "font.size": 8.5})
C = {"blue": "#2F6EBA", "orange": "#E07B39", "teal": "#2BA3A6", "ink": "#1F2933", "ink2": "#52606D",
     "muted": "#9AA5B1", "panel": "#F5F7FA", "light": "#E8F0FA", "warm": "#FDF0E6", "red": "#C0392B"}

def box(ax, x, y, w, h, title, body="", fc=C["panel"], ec=C["muted"], tfs=9, bfs=7.4, ha="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.1", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h - 2.0, title, ha="center", va="top", fontsize=tfs, fontweight="bold", color=C["ink"])
    if body: ax.text(x + (w / 2 if ha == "center" else 1.4), y + h - 5.2, body, ha=ha, va="top", fontsize=bfs, color=C["ink"], linespacing=1.35)
def arrow(ax, x1, y1, x2, y2, label="", color=None, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, lw=1.4, color=color or C["ink2"], linestyle=ls))
    if label: ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.2, label, ha="center", va="bottom", fontsize=7.0, color=C["ink2"])
def save(fig, name):
    fig.savefig(HERE / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(HERE / f"{name}.pdf", bbox_inches="tight"); plt.close(fig); print("written", name)

# ---------------------------------------------------------------- F13 Chat-to-Action asymmetry
fig = plt.figure(figsize=(8.6, 3.3), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 38); ax.set_axis_off()
ax.text(2, 36.5, "A conversational assistant answers language with language", fontsize=8.6, color=C["ink2"], va="top", style="italic")
box(ax, 2, 23, 24, 10, "free-form utterance", "any wording, any length", fc=C["panel"])
box(ax, 34, 23, 24, 10, "conversational model", "", fc=C["light"], ec=C["blue"])
box(ax, 66, 23, 30, 10, "free-form reply", "output space as open as the input", fc=C["panel"])
arrow(ax, 26, 28, 34, 28); arrow(ax, 58, 28, 66, 28)
ax.plot([2, 96], [20.5, 20.5], color=C["muted"], lw=0.9, ls=(0, (4, 3)))
ax.text(2, 19.0, "A device controller answers language with one executable command", fontsize=8.6, color=C["ink2"], va="top", style="italic")
box(ax, 2, 3, 24, 12.5, "free-form utterance", "any wording, any length", fc=C["panel"])
box(ax, 34, 3, 24, 12.5, "compact model", "", fc=C["warm"], ec=C["orange"])
box(ax, 66, 3, 30, 12.5, "executable command", "one of the tuples the policy\nand the device admit", fc=C["warm"], ec=C["orange"])
arrow(ax, 26, 9, 34, 9, color=C["orange"]); arrow(ax, 58, 9, 66, 9, color=C["orange"])
ax.text(81, 1.2, "$K_{\\mathrm{eff}}$ = 240 reachable tuples", ha="center", fontsize=8.4, fontweight="bold", color=C["orange"])
save(fig, "F13_chat_to_action_asymmetry")

# ---------------------------------------------------------------- F14 study flow
fig = plt.figure(figsize=(9.2, 2.9), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 30); ax.set_axis_off()
steps = [("executable\npolicy", C["panel"], C["muted"]), ("enumerate\n$K_{\\mathrm{eff}}$ = 240", C["light"], C["blue"]),
         ("capacity and\nexposure\ncandidates", C["light"], C["blue"]), ("multi-seed\nseries", C["light"], C["blue"]),
         ("select 15.7 M\nmodel", C["warm"], C["orange"]), ("quantize\nand serve", C["warm"], C["orange"]),
         ("execute bulb\ncommand", C["warm"], C["orange"]), ("evaluate\ngeneralisation\nand interaction", C["panel"], C["muted"])]
w = 10.9; gap = 1.7; x = 1.2
for i, (t, fc, ec) in enumerate(steps):
    ax.add_patch(FancyBboxPatch((x, 8), w, 14, boxstyle="round,pad=0.3,rounding_size=1.1", fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, 15, t, ha="center", va="center", fontsize=8.0, color=C["ink"], linespacing=1.4,
            fontweight="bold" if i in (1, 4) else "normal")
    if i < len(steps) - 1: arrow(ax, x + w, 15, x + w + gap, 15)
    x += w + gap
ax.text(50, 4.5, "Sections 3.2 and 4.1  →  Sections 3.3, 4.2 and 4.3  →  Section 4.5  →  Sections 3.1 and 4.6  →  Sections 4.4 and 4.7",
        ha="center", fontsize=7.4, color=C["ink2"])
save(fig, "F14_study_flow")

# ---------------------------------------------------------------- F15 selected CompactLM architecture
fig = plt.figure(figsize=(6.4, 4.6), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 72); ax.set_axis_off()
box(ax, 6, 62, 88, 8, "input utterance → 4k natural-corpus tokenizer (V = 4,000)", "", fc=C["panel"])
box(ax, 6, 52, 88, 8, "token embedding, d = 384   (tied with the output projection)", "", fc=C["light"], ec=C["blue"])
ax.add_patch(FancyBboxPatch((6, 20), 88, 29, boxstyle="round,pad=0.3,rounding_size=1.1", fc="#FFFFFF", ec=C["blue"], lw=1.4))
ax.text(50, 47.0, "8 decoder blocks (L = 8)", ha="center", va="top", fontsize=9, fontweight="bold", color=C["ink"])
for i, (lab, yy) in enumerate((("RMSNorm → causal self-attention, 6 heads, rotary position embeddings", 40.0),
                              ("RMSNorm → SwiGLU feed-forward, inner width 1,024", 33.5))):
    ax.add_patch(FancyBboxPatch((11, yy - 4.2), 78, 5.6, boxstyle="round,pad=0.2,rounding_size=0.8", fc=C["light"], ec=C["blue"], lw=1.0))
    ax.text(50, yy - 1.4, lab, ha="center", va="center", fontsize=7.8, color=C["ink"])
ax.text(50, 25.5, "residual connections around each sub-layer; context 256 tokens", ha="center", fontsize=7.4, color=C["ink2"], style="italic")
ax.text(50, 22.2, "4d² in attention + 8d² in the gated feed-forward = 12d² per block", ha="center", fontsize=7.4, color=C["ink2"])
box(ax, 6, 10, 88, 8, "RMSNorm → output projection (tied weights) → greedy decoding", "", fc=C["light"], ec=C["blue"])
box(ax, 6, 0.5, 88, 8, "JSON tuple  {\"H\", \"S\", \"B\", \"Dimmer\", \"CT\"}", "", fc=C["warm"], ec=C["orange"])
for y in (62, 52, 49, 20, 10): arrow(ax, 50, y, 50, y - 2.0, color=C["muted"])
ax.text(50, 71.2, "Selected configuration: d = 384, L = 8, V = 4k, 15,698,304 parameters",
        ha="center", va="top", fontsize=9.2, fontweight="bold", color=C["ink"])
save(fig, "F15_compactlm_architecture")

# ---------------------------------------------------------------- F16 generalisation boundary
fig, ax = plt.subplots(figsize=(6.6, 3.4), dpi=100)
names = ["development test set\n(same generator as training)", "unseen-frame hold-out\n(32 new sentence frames)", "post hoc synthetic stress set\n(externally written paraphrases)"]
vals = [86.5, 58.7, 7.9]; errs = [1.8, 1.7, 0.6]
cols = [C["blue"], C["teal"], C["red"]]
bars = ax.bar(range(3), vals, yerr=errs, capsize=4, color=cols, width=0.56, edgecolor="white", linewidth=1.4)
for i, v in enumerate(vals):
    ax.text(i, v + errs[i] + 2.4, f"{v:.1f} %", ha="center", fontsize=10, fontweight="bold", color=cols[i])
ax.set_xticks(range(3)); ax.set_xticklabels(names, fontsize=7.6)
ax.set_ylabel("exact tuple match (%)"); ax.set_ylim(0, 100)
ax.axhline(0.4, color=C["muted"], lw=1.0, ls=(0, (4, 3)))
ax.text(2.42, 3.0, "chance 0.4 %", ha="right", fontsize=7.0, color=C["ink2"])
ax.annotate("", xy=(2.35, 93), xytext=(-0.35, 93), arrowprops=dict(arrowstyle="-|>", color=C["ink2"], lw=1.2))
ax.text(1.0, 95, "input distribution further from the training frames", ha="center", fontsize=7.8, color=C["ink2"])
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.grid(axis="y", color=C["muted"], alpha=0.25, lw=0.7); ax.set_axisbelow(True)
fig.tight_layout(); save(fig, "F16_generalisation_boundary")

# ---------------------------------------------------------------- F17 implementation cost
fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.9), dpi=100)
a = axes[0]
labels = ["selected model\nfp32", "selected model\nmixed 4/6/8-bit", "240-class head\nfp32"]
sizes = [62.8, 17.1, 63.2]; cols = [C["blue"], C["orange"], C["teal"]]
a.barh(range(3), sizes, color=cols, height=0.55, edgecolor="white", linewidth=1.2)
for i, v in enumerate(sizes): a.text(v + 1.5, i, f"{v:.1f} MB", va="center", fontsize=8.4, color=cols[i], fontweight="bold")
a.set_yticks(range(3)); a.set_yticklabels(labels, fontsize=7.6); a.invert_yaxis()
a.set_xlabel("model file (MB)"); a.set_xlim(0, 82); a.set_title("(a) stored size", fontsize=8.8, loc="left")
for sp in ("top", "right"): a.spines[sp].set_visible(False)
b = axes[1]
lat = [("selected model\nmixed 4/6/8-bit", 95, 105, C["orange"]), ("240-class head\nfp32", 3.4, 3.8, C["teal"])]
for i, (lab, med, p95, c) in enumerate(lat):
    b.barh(i, med, color=c, height=0.5, edgecolor="white", linewidth=1.2)
    b.plot([med, p95], [i, i], color=C["ink2"], lw=1.4)
    b.plot([p95], [i], marker="|", color=C["ink2"], ms=9)
    b.text(p95 + 3, i, f"{med:g} / {p95:g} ms", va="center", fontsize=8.4, color=c, fontweight="bold")
b.set_yticks(range(2)); b.set_yticklabels([l for l, *_ in lat], fontsize=7.6); b.invert_yaxis()
b.set_xlabel("CPU latency, median and 95th percentile (ms)"); b.set_xlim(0, 150)
b.set_title("(b) latency, 4 threads", fontsize=8.8, loc="left")
for sp in ("top", "right"): b.spines[sp].set_visible(False)
fig.tight_layout(); save(fig, "F17_implementation_cost")

# ---------------------------------------------------------------- F18 physical implementation (author-owned assets)
import matplotlib.image as mpimg
ASSET = HERE / "assets"
if (ASSET / "bulbs_photo.png").exists():
    fig = plt.figure(figsize=(8.4, 5.6), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 66); ax.set_axis_off()
    # panel (a): the processing path, drawn for this paper in English
    steps = [("utterance", "Android client\ntext or speech-to-text"), ("HTTP POST", "FastAPI service\n/predict/{model_id}\n/predict_all"),
             ("five-value tuple", "normalise and validate\n{H, S, B, Dimmer, CT}"), ("model_id → bulb IP", "Tasmota HTTP\nHSBColor / Dimmer / CT")]
    w = 21.0; gap = 3.0; x = 2.0
    for i, (lab, body) in enumerate(steps):
        ax.add_patch(FancyBboxPatch((x, 52), w, 11, boxstyle="round,pad=0.3,rounding_size=1.0",
                                    fc=C["light"] if i in (1, 2) else C["panel"], ec=C["blue"] if i in (1, 2) else C["muted"], lw=1.2))
        ax.text(x + w / 2, 58.6, body.split("\n")[0], ha="center", va="center", fontsize=8.0, fontweight="bold", color=C["ink"])
        ax.text(x + w / 2, 55.0, "\n".join(body.split("\n")[1:]), ha="center", va="center", fontsize=7.0, color=C["ink2"], linespacing=1.3)
        if i < 3:
            arrow(ax, x + w, 57.5, x + w + gap, 57.5)
            ax.text(x + w + gap / 2, 63.6, lab, ha="center", fontsize=6.6, color=C["ink2"])
        x += w + gap
    ax.text(2.0, 49.5, "(a) processing path of the reference implementation", fontsize=8.4, fontweight="bold", color=C["ink"], va="top")
    # panel (b): the five-bulb platform, author photograph
    img = mpimg.imread(ASSET / "bulbs_photo.png")
    axb = fig.add_axes([0.025, 0.085, 0.585, 0.635]); axb.imshow(img); axb.set_axis_off()
    ax.text(31.0, 1.6, "(b) the five-bulb platform, one bulb per model condition", ha="center", fontsize=8.4, fontweight="bold", color=C["ink"])
    # panel (c): the client screen, author screenshot
    img2 = mpimg.imread(ASSET / "app_screen.png")
    axc = fig.add_axes([0.655, 0.115, 0.285, 0.605]); axc.imshow(img2); axc.set_axis_off()
    ax.text(79.0, 4.2, "(c) client screen: recognised utterance\nand the command produced by each model", ha="center", va="top", fontsize=8.4, fontweight="bold", color=C["ink"], linespacing=1.3)
    save(fig, "F18_physical_implementation")

# ---------------------------------------------------------------- F19 multi-axis search, assembled from the verified series plots
from PIL import Image as _PIL
def _panel(path, h):
    im = _PIL.open(HERE / path).convert("RGB")
    w = int(im.width * h / im.height)
    return im.resize((w, h), _PIL.LANCZOS)
try:
    H = 900
    panels = [("F01_width_series_24k.png", "(a) width"), ("F03_depth_series.png", "(b) depth"), ("F04_vocabulary_series.png", "(c) vocabulary")]
    ims = [(_panel(f, H), lab) for f, lab in panels]
    pad, top = 26, 46
    W = sum(im.width for im, _ in ims) + pad * (len(ims) + 1)
    canvas = _PIL.new("RGB", (W, H + top + 70), "white")
    from PIL import ImageDraw, ImageFont
    dr = ImageDraw.Draw(canvas)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except Exception: font = ImageFont.load_default()
    try: font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 27)
    except Exception: font2 = font
    x = pad
    for im, lab in ims:
        canvas.paste(im, (x, top)); dr.text((x + 4, 8), lab, fill=(31, 41, 51), font=font); x += im.width + pad
    dr.text((pad + 4, H + top + 16),
            "(d) selected engineering configuration: d = 384, L = 8, 4k natural-corpus vocabulary, 15,698,304 parameters",
            fill=(224, 123, 57), font=font2)
    canvas.save(HERE / "F19_multi_axis_search.png", dpi=(300, 300))
    canvas.save(HERE / "F19_multi_axis_search.pdf", "PDF", resolution=300)
    print("written F19_multi_axis_search", canvas.size)
except Exception as e:
    print("F19 skipped:", e)
