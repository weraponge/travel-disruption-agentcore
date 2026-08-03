"""
generate_diagram.py  — AWS blog standard architecture diagram style
White background · numbered layers · icon above label · minimal arrows
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch, Circle
from pathlib import Path

MEDIA = Path.home() / ".cache/awsdac/da2d30aaaa858e40cbd77fd47263bbe1-AWS-Architecture-Icons-Deck_For-Light-BG_02072025.pptx/ppt/media"

ICONS = {
    "user":          MEDIA / "image127.png",
    "gear":          MEDIA / "image170.png",
    "eventbridge":   MEDIA / "image304.png",
    "sqs":           MEDIA / "image290.png",
    "stepfn":        MEDIA / "image302.png",
    "bedrock":       MEDIA / "image425.png",
    "lambda":        MEDIA / "image35.png",
    "dynamodb":      MEDIA / "image622.png",
    "sns":           MEDIA / "image282.png",
    "secrets":       MEDIA / "image1448.png",
    "cloudwatch":    MEDIA / "image974.png",
    "gateway":       MEDIA / "image1302.png",
    "memory":        MEDIA / "image664.png",
    "observability": MEDIA / "image994.png",
    "inline_fn":     MEDIA / "image65.png",
    "runtime":       MEDIA / "image1208.png",
}

def load(key):
    p = ICONS.get(key)
    return mpimg.imread(str(p)) if p and p.exists() else None

# ── Colours ────────────────────────────────────────────────────────────────────
WHITE   = "#FFFFFF"
BLACK   = "#111111"
DGREY   = "#444444"
MGREY   = "#777777"
LGREY   = "#F4F4F4"
BORDER  = "#C8C8C8"
ORANGE  = "#FF9900"
TEAL    = "#007166"
TEAL_L  = "#EAF6F4"
RED     = "#C0392B"

# ── Canvas ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(17, 20))
ax.set_xlim(0, 17)
ax.set_ylim(0, 20)
ax.axis('off')
fig.patch.set_facecolor(WHITE)

# ── Helpers ────────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, fc=LGREY, ec=BORDER, lw=1.0, ls='-', r=0.2, z=1):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec, lw=lw, linestyle=ls, zorder=z)
    ax.add_patch(p)

def node(ax, cx, cy, icon_key, line1, line2="", line3="", isz=0.7, z=4):
    img = load(icon_key)
    if img is not None:
        ext = [cx-isz/2, cx+isz/2, cy, cy+isz]
        ax.imshow(img, extent=ext, zorder=z, aspect='auto')
    ax.text(cx, cy-0.05, line1, ha='center', va='top',
            fontsize=8.0, fontweight='bold', color=BLACK, zorder=z)
    ty = cy - 0.27
    for ln in [line2, line3]:
        if ln:
            ax.text(cx, ty, ln, ha='center', va='top',
                    fontsize=7.0, color=MGREY, zorder=z)
            ty -= 0.18

def dn(ax, x, y1, y2, c=DGREY, lw=1.5):
    """Straight down arrow."""
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=c, lw=lw,
                                mutation_scale=11), zorder=7)

def rt(ax, x1, x2, y, c=DGREY, lw=1.5, lbl=""):
    """Straight right arrow."""
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=c, lw=lw,
                                mutation_scale=11), zorder=7)
    if lbl:
        ax.text((x1+x2)/2, y+0.1, lbl, ha='center', va='bottom',
                fontsize=6.8, color=MGREY, zorder=7)

def badge(ax, x, y, num):
    """Layer number circle badge."""
    c = Circle((x, y), 0.25, color="#232F3E", zorder=6)
    ax.add_patch(c)
    ax.text(x, y, str(num), ha='center', va='center',
            fontsize=10, fontweight='bold', color=WHITE, zorder=7)

def layer_label(ax, x, y, text):
    ax.text(x, y, text, ha='center', va='center',
            fontsize=7.5, fontweight='bold', color="#232F3E",
            rotation=90, zorder=5)

# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
ax.text(8.5, 19.6, "Travel Disruption Agent",
        ha='center', fontsize=19, fontweight='bold', color=BLACK)
ax.text(8.5, 19.18, "Amazon Bedrock AgentCore Harness  ·  Travel & Hospitality",
        ha='center', fontsize=10, color=MGREY)
ax.plot([1.5, 15.5], [18.9, 18.9], color=ORANGE, lw=1.8)

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — Event Ingestion   y 16.8–18.6
# ══════════════════════════════════════════════════════════════════════════════
badge(ax, 0.55, 17.8, 1)
layer_label(ax, 0.18, 17.8, "Event Ingestion")

box(ax, 1.5, 16.8, 14.0, 1.9, fc=LGREY, ec=BORDER)

# nodes: external actors + AWS services across full width
node(ax, 2.9,  17.4, "user",        "Disrupted\nTraveler")
node(ax, 5.0,  17.4, "gear",        "Airline / GDS\nSystem")
node(ax, 7.2,  17.4, "eventbridge", "Amazon\nEventBridge", "Flight Cancellation")
node(ax, 9.8,  17.4, "sqs",         "Amazon SQS", "Disruption Queue")
node(ax, 12.4, 17.4, "stepfn",      "Step Functions", "InvokeHarness")

rt(ax, 3.42, 4.46, 17.75, lbl="Cancel Flight")
rt(ax, 5.54, 6.62, 17.75, lbl="Flight Cancelled")
rt(ax, 7.78, 9.22, 17.75)
ax.annotate("", xy=(9.8, 17.75), xytext=(12.4, 17.75),
            arrowprops=dict(arrowstyle='->', color=DGREY, lw=1.5,
                            mutation_scale=11), zorder=7)

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — AgentCore Harness   y 10.6–16.5
# ══════════════════════════════════════════════════════════════════════════════
badge(ax, 0.55, 13.5, 2)
layer_label(ax, 0.18, 13.5, "AgentCore Harness")

# Harness dashed border — tighter vertical space
box(ax, 1.5, 10.6, 14.0, 5.6, fc=TEAL_L, ec=TEAL, lw=1.8, ls='--')
ax.text(1.85, 16.05, "AgentCore Harness — Travel Disruption Agent",
        ha='left', va='center', fontsize=8.5, fontweight='bold', color=TEAL, zorder=5)

# SQS → Harness entry arrow (clean, no overlapping label)
dn(ax, 9.8, 16.8, 16.2, c=TEAL, lw=2.0)
ax.text(10.05, 16.52, "Invoke Harness  (runtimeSessionId)",
        ha='left', va='center', fontsize=7.0, color=TEAL, zorder=8)

# Core row  y=14.1
node(ax, 4.0,  14.1, "bedrock",  "Orchestrator Agent", "Claude Sonnet 4.6", "Strands Agent Loop")
node(ax, 7.8,  14.1, "memory",   "AgentCore Memory", "Short + Long-term", "Passenger Context")
node(ax, 11.6, 14.1, "runtime",  "Isolated microVM", "per Session", "AgentCore Runtime")

rt(ax, 4.55, 7.18, 14.46, lbl="Read/Write Context")

# Tools sub-row  y=11.7 — columns aligned with integration layer below
box(ax, 1.8, 11.0, 13.4, 2.0, fc=WHITE, ec=BORDER, lw=1.0, ls='--', r=0.15, z=2)
ax.text(2.0, 12.85, "Tools", ha='left', va='center',
        fontsize=7.5, color=MGREY, fontweight='bold', zorder=5)

# Flight Agent at x=4.0 (→ Gateway x=3.2), Notify at x=10.0 (→ SNS x=10.0)
node(ax, 4.0,  11.7, "lambda",    "Flight Agent",    "Rebook Flight")
node(ax, 10.0, 11.7, "lambda",    "Notify Agent",    "SMS / Email")
node(ax, 13.0, 11.7, "inline_fn", "Inline Function", "Human-in-Loop", "Escalation")

# Orchestrator → tools
dn(ax, 4.0,  14.1, 12.42)
dn(ax, 10.0, 14.1, 12.42)
dn(ax, 13.0, 14.1, 12.42, c=RED)
ax.text(13.2, 13.2, "tool_use", ha='left', va='center',
        fontsize=7.0, color=RED, fontstyle='italic', zorder=8)

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 3 — Integration   y 7.3–10.3
# ══════════════════════════════════════════════════════════════════════════════
badge(ax, 0.55, 8.8, 3)
layer_label(ax, 0.18, 8.8, "Integration Layer")

box(ax, 1.5, 7.3, 14.0, 3.0, fc=LGREY, ec=BORDER)

# Gateway sub-box
box(ax, 1.8, 7.6, 4.5, 2.4, fc=TEAL_L, ec=TEAL, lw=1.2, ls='--', r=0.15, z=2)
ax.text(2.0, 9.85, "AgentCore Gateway\nMCP / AWS_IAM",
        ha='left', va='center', fontsize=7.0, fontweight='bold', color=TEAL, zorder=5)

node(ax, 3.2,  8.2, "gateway",  "AgentCore\nGateway", "SigV4 / OAuth")
node(ax, 7.0,  8.2, "dynamodb", "Amazon\nDynamoDB",   "Passenger Profiles")
node(ax, 10.0, 8.2, "sns",      "Amazon SNS",         "Notifications")
node(ax, 13.2, 8.2, "secrets",  "Secrets Manager",    "API Keys /\nToken Vault")

# Tools → Integration (straight down, column-aligned)
dn(ax, 4.0,  11.0, 8.92)    # Flight → Gateway
dn(ax, 10.0, 11.0, 8.92)    # Notify → SNS

# Integration row horizontal
rt(ax, 3.72, 6.38, 8.56)
rt(ax, 7.55, 9.38, 8.56)
rt(ax, 10.55, 12.6, 8.56)

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 4 — Observability   y 4.2–7.0
# ══════════════════════════════════════════════════════════════════════════════
badge(ax, 0.55, 5.6, 4)
layer_label(ax, 0.18, 5.6, "Observability")

box(ax, 1.5, 4.2, 14.0, 2.8, fc=LGREY, ec=BORDER)

node(ax, 5.5,  4.8, "observability", "AgentCore\nObservability", "Unified Trace View", "Every Agent Decision")
node(ax, 10.0, 4.8, "cloudwatch",    "Amazon\nCloudWatch",       "Logs & Metrics")

# Layer 3 → 4
dn(ax, 5.5,  7.3, 5.52)
rt(ax, 6.05, 9.38, 5.16)

# Auto-trace — note inside diagram boundary
ax.text(14.0, 9.5, "Auto-traced\n(all decisions)",
        ha='center', va='center', fontsize=7.0, color=TEAL,
        fontstyle='italic', zorder=8,
        bbox=dict(boxstyle='round,pad=0.3', fc=TEAL_L, ec=TEAL, lw=0.8))
ax.annotate("", xy=(13.95, 9.8), xytext=(13.0+0.35, 11.0),
            arrowprops=dict(arrowstyle='->', color=TEAL, lw=1.2,
                            connectionstyle="arc3,rad=-0.2",
                            mutation_scale=9), zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════════════════
LY = 3.0
box(ax, 1.5, LY, 14.0, 1.0, fc=WHITE, ec=BORDER, lw=0.8)
ax.text(1.85, LY+0.78, "Legend", ha='left', va='center',
        fontsize=8, fontweight='bold', color=BLACK)

items = [
    (TEAL,  '--', "AgentCore (Harness, Gateway, Memory, Observability)"),
    (DGREY, '-',  "AWS Managed Services"),
    (RED,   '-',  "Human-in-Loop Escalation (tool_use → inline function)"),
]
lx = 1.85
for col, ls, lbl in items:
    ax.plot([lx, lx+0.55], [LY+0.32, LY+0.32], color=col, lw=1.8, linestyle=ls)
    ax.text(lx+0.7, LY+0.32, lbl, ha='left', va='center',
            fontsize=7.5, color=DGREY)
    lx += 4.6

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
ax.plot([1.5, 15.5], [2.75, 2.75], color=BORDER, lw=0.8)
ax.text(8.5, 2.45, "github.com/weraponge/travel-disruption-agentcore   ·   "
                   "Built on Amazon Bedrock AgentCore Harness",
        ha='center', va='center', fontsize=8, color=MGREY, fontstyle='italic')

plt.tight_layout(pad=0.3)
plt.savefig("travel-disruption-agentcore.png",
            dpi=180, bbox_inches='tight',
            facecolor=WHITE, edgecolor='none')
print("Saved: travel-disruption-agentcore.png")
