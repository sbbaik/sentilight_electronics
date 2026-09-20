"""F12: SentiLight system architecture and data flow (Electronics revision).
Client (text / speech-to-text) -> FastAPI model service (/predict/{model_id}, /predict_all) with model adapters ->
normalised five-value lighting tuple -> client maps model_id to a fixed bulb IP and issues Tasmota HTTP commands.
Also shows one utterance -> JSON output example and where K_eff and the evaluation live. Output: F12_system_architecture.{png,pdf}."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path
HERE = Path(__file__).resolve().parent
C = {"blue": "#2F6EBA", "orange": "#E07B39", "aqua": "#2BA3A6", "ink": "#1F2933", "ink2": "#52606D", "muted": "#9AA5B1", "panel": "#F5F7FA", "light": "#E8F0FA"}
import matplotlib.font_manager as fm
_k=[f.name for f in fm.fontManager.ttflist if any(x in f.name for x in ("Noto Sans CJK","NanumGothic","Noto Sans KR","NanumBarunGothic"))]
plt.rcParams.update({"font.family": ([_k[0]] if _k else []) + ["DejaVu Sans"], "font.size": 8.5})
fig = plt.figure(figsize=(9.0, 4.2), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 47); ax.set_axis_off()
def box(x, y, w, h, title, body="", fc=C["panel"], ec=C["muted"], tfs=9, bfs=7.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=tfs, fontweight="bold", color=C["ink"])
    if body: ax.text(x + 1.5, y + h - 5.6, body, ha="left", va="top", fontsize=bfs, color=C["ink"], linespacing=1.35)
def arrow(x1, y1, x2, y2, label="", ls="-", color=None):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.4, color=color or C["ink2"], linestyle=ls))
    if label: ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.4, label, ha="center", va="bottom", fontsize=7.2, color=C["ink2"])
# top row: pipeline
box(2, 30, 22, 14, "Client (edge hub)", "text input or speech-to-text\nsends the utterance to the service\nmaps model_id → bulb IP\n(config/frontend.yaml)")
box(30, 30, 32, 14, "Model service (FastAPI)", "POST /predict/{model_id}, /predict_all\nadapters: CompactLM (this paper), SBERT,\nremote LLMs (evaluation conditions)\nnormalises output → {H,S,B,Dimmer,CT}", fc=C["light"], ec=C["blue"])
box(68, 30, 30, 14, "Wi-Fi bulbs (Tasmota)", "HTTP command per bulb\nHSBColor / Dimmer / CT\nfive bulbs = five model conditions\nin the user evaluation")
arrow(24, 37, 30, 37, "utterance"); arrow(62, 37, 68, 37, "lighting tuple")
ax.text(75, 28.1, "client issues the Tasmota requests after the service replies", ha="center", fontsize=6.6, color=C["ink2"], style="italic")
# middle: example
box(2, 12.5, 46, 14.5, "Example", "input   \"회의 끝나고 집에 왔는데 우울해. 조명은 은은한 주황빛으로 해줄래\"\n            (\"came home after a meeting feeling down; make the light a soft orange\")\nCompactLM output (JSON)   {\"H\": 21, \"S\": 38, \"B\": 34, \"Dimmer\": 26, \"CT\": 358}\npolicy check   colour = orange, emotion = sadness, intensity = soft  (gold tuple computed by the policy)\n→ one of the K_eff = 240 executable tuples; exact-tuple match scores the row", bfs=6.9)
# right middle: K_eff & evaluation
box(52, 12.5, 46, 14.5, "Where the paper's quantities live", "K_eff: enumerate (colour+1)(emotion+1)×intensity lattice cells through the\n   executable policy π and device map f; merge identical tuples → 240\nDevelopment test (2,000 rows): used during the width / depth / vocabulary series\n   and model selection\nFinal hold-out (2,000 rows, new sentence frames, built after selection): used once\nDeployment: mixed 4/6/8-bit export, CPU latency through this service", fc=C["light"], ec=C["blue"], bfs=6.9)
# bottom: compact model box
box(2, 1.5, 96, 9, "Selected CompactLM (d = 384, L = 8, 4k natural-corpus tokenizer; 15.7 M parameters)", "pretraining 2,400 steps on a clean Korean corpus → SFT 4 epochs on policy rows → greedy JSON decoding → mixed 4/6/8-bit weight export (17.1 MB, load-time dequantisation) → CPU service, 95 ms median (4 threads)", bfs=7.0)
arrow(46, 30, 46, 27.2, "", color=C["muted"]); arrow(20, 12.5, 20, 10.6, "", color=C["muted"])
fig.savefig(HERE / "F12_system_architecture.png", dpi=300, bbox_inches="tight"); fig.savefig(HERE / "F12_system_architecture.pdf", bbox_inches="tight")
print("written F12")
