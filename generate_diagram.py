"""
generate_diagram.py
Professional architecture diagram using OFFICIAL AWS service icons.
Icons sourced from the AWS Architecture Icons pack (same source as awsdac).
No graphviz or emoji fonts required.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import os

# ── AWS colour palette ────────────────────────────────────────────────────────
AWS_ORANGE   = "#FF9900"
AWS_DARK     = "#232F3E"
AWS_TEAL     = "#01A88D"
AWS_PURPLE   = "#8C4FFF"
AWS_GREEN    = "#1A7A3F"
AWS_RED      = "#BF0816"
AWS_SLATE    = "#546E7A"
LIGHT_TEAL   = "#E6F6F4"
LIGHT_ORANGE = "#FFF8EE"
LIGHT_PURPLE = "#F3EEFF"
LIGHT_GREY   = "#F5F5F5"
BORDER_GREY  = "#D0D0D0"
WHITE        = "#FFFFFF"
TEXT_DARK    = "#111111"
TEXT_MID     = "#555555"

# ── Icon paths (from awsdac cache) ────────────────────────────────────────────
MEDIA = Path.home() / ".cache/awsdac/da2d30aaaa858e40cbd77fd47263bbe1-AWS-Architecture-Icons-Deck_For-Light-BG_02072025.pptx/ppt/media"

ICONS = {
    "bedrock":      MEDIA / "image425.png",   # Amazon Bedrock — Orchestrator
    "eventbridge":  MEDIA / "image304.png",   # Amazon EventBridge
    "sqs":          MEDIA / "image290.png",   # Amazon SQS
    "stepfn":       MEDIA / "image302.png",   # AWS Step Functions
    "lambda":       MEDIA / "image35.png",    # AWS Lambda
    "dynamodb":     MEDIA / "image622.png",   # Amazon DynamoDB
    "sns":          MEDIA / "image282.png",   # Amazon SNS
    "secrets":      MEDIA / "image1448.png",  # AWS Secrets Manager
    "cloudwatch":   MEDIA / "image974.png",   # Amazon CloudWatch
    "gateway":      MEDIA / "image1302.png",  # Gateway
    "agent":        MEDIA / "image1184.png",  # DataSync Agent — used for AgentCore Agent
    "runtime":      MEDIA / "image1208.png",  # Runtime
    "user":         MEDIA / "image127.png",   # User
    "memory":       MEDIA / "image664.png",   # Amazon MemoryDB — AgentCore Memory
    "observability":MEDIA / "image994.png",   # CloudWatch Synthetics — Observability
    "inline_fn":    MEDIA / "image65.png",    # Step Functions workflow — Inline Function
}

def load_icon(key):
    path = ICONS.get(key)
    if path and path.exists():
        return mpimg.imread(str(path))
    return None

# ── Canvas ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(22, 26))
ax.set_xlim(0, 22)
ax.set_ylim(0, 26)
ax.axis('off')
fig.patch.set_facecolor(WHITE)

# ── Primitives ────────────────────────────────────────────────────────────────
def rbox(ax, x, y, w, h, fc=WHITE, ec=BORDER_GREY, lw=1.5, r=0.25, z=2, alpha=1.0):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha)
    ax.add_patch(p)

def place_icon(ax, icon_key, cx, cy, size=0.75, z=5):
    img = load_icon(icon_key)
    if img is not None:
        ext = [cx - size/2, cx + size/2, cy - size/2, cy + size/2]
        ax.imshow(img, extent=ext, zorder=z, aspect='auto')

def service_card(ax, x, y, w, h, icon_key, line1, line2="", line3="",
                 fc=WHITE, ec=BORDER_GREY, accent=AWS_ORANGE,
                 icon_size=0.65, z=3):
    """Service card: accent top bar + AWS icon + label lines."""
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=1.8, r=0.2, z=z)
    # accent top stripe
    rbox(ax, x, y + h - 0.18, w, 0.18, fc=accent, ec='none', lw=0, r=0.1, z=z+1)
    cx = x + w / 2
    # icon centered
    icon_cy = y + h - 0.18 - icon_size/2 - 0.08
    place_icon(ax, icon_key, cx, icon_cy, size=icon_size, z=z+2)
    # text lines
    ty = y + h - 0.18 - icon_size - 0.22
    for line in [line1, line2, line3]:
        if line:
            ax.text(cx, ty, line, ha='center', va='top',
                    fontsize=8.0, fontweight='bold' if line == line1 else 'normal',
                    color=TEXT_DARK if line == line1 else TEXT_MID,
                    zorder=z+2)
            ty -= 0.2

def group_header(ax, x, y, w, h, title, fc=LIGHT_TEAL, ec=AWS_TEAL, lw=2.5,
                 header_fc=AWS_TEAL, z=1):
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, r=0.35, z=z)
    rbox(ax, x, y + h - 0.45, w, 0.45, fc=header_fc, ec=ec, lw=lw, r=0.2, z=z+1)
    ax.text(x + 0.45, y + h - 0.225, title,
            ha='left', va='center', fontsize=10.5, fontweight='bold',
            color=WHITE, zorder=z+2)

def varrow(ax, x, y1, y2, label="", lw=1.8, color=AWS_DARK, lo=(0.15, 0)):
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                mutation_scale=14), zorder=6)
    if label:
        ax.text(x + lo[0], (y1+y2)/2 + lo[1], label,
                ha='left', va='center', fontsize=7.5, color=color,
                fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.15', fc=WHITE, ec='none', alpha=0.9),
                zorder=7)

def harrow(ax, x1, x2, y, label="", lw=1.8, color=AWS_DARK, lo=(0, 0.13)):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                mutation_scale=14), zorder=6)
    if label:
        ax.text((x1+x2)/2 + lo[0], y + lo[1], label,
                ha='center', va='bottom', fontsize=7.5, color=color,
                fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.15', fc=WHITE, ec='none', alpha=0.9),
                zorder=7)

def darrow(ax, x1, y1, x2, y2, label="", lw=1.8, color=AWS_DARK, lo=(0.1, 0.1)):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle="arc3,rad=0",
                                mutation_scale=14), zorder=6)
    if label:
        mx = (x1+x2)/2 + lo[0]
        my = (y1+y2)/2 + lo[1]
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=7.5,
                color=color, fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.15', fc=WHITE, ec='none', alpha=0.9),
                zorder=7)

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
SW, SH = 2.8, 2.0   # standard card size
# Card x positions (5 columns across ~20 units)
CX = [1.5, 5.1, 8.7, 12.3, 15.9]   # left edge of each column

# ── Title banner ──────────────────────────────────────────────────────────────
rbox(ax, 0.5, 24.5, 21, 1.2, fc=AWS_DARK, ec=AWS_DARK, lw=0, r=0.3, z=1)
ax.text(11, 25.22, "Travel Disruption Agent", ha='center', va='center',
        fontsize=24, fontweight='bold', color=WHITE, zorder=2)
ax.text(11, 24.78, "Amazon Bedrock AgentCore Harness   ·   Travel & Hospitality",
        ha='center', va='center', fontsize=12, color=AWS_ORANGE, zorder=2)

# ── AWS Cloud border ──────────────────────────────────────────────────────────
rbox(ax, 0.5, 0.4, 21, 23.8, fc="#FAFAFA", ec=AWS_DARK, lw=2.5, r=0.5, z=0)
ax.text(1.2, 23.95, "AWS Cloud", ha='left', va='center',
        fontsize=10, fontweight='bold', color=AWS_DARK, zorder=2)

# ── Row 1: External actors  y=21.5 ───────────────────────────────────────────
R1Y = 21.4
ax.text(5.5, 23.6, "External", ha='center', fontsize=8,
        color=TEXT_MID, fontstyle='italic')

service_card(ax, 1.8, R1Y, SW, SH, "user",
             "Disrupted Traveler", "",
             fc=LIGHT_ORANGE, ec=AWS_SLATE, accent=AWS_SLATE)
service_card(ax, 5.4, R1Y, SW, SH, "user",
             "Airline / GDS", "System",
             fc=LIGHT_ORANGE, ec=AWS_SLATE, accent=AWS_SLATE)

harrow(ax, 4.6, 5.4, R1Y + SH/2, label="Cancel Flight", color=AWS_DARK)

# ── Row 2: Event ingestion  y=18.8 ───────────────────────────────────────────
R2Y = 18.8

# Cloud border label
service_card(ax, CX[0], R2Y, SW, SH, "eventbridge",
             "Amazon EventBridge", "Flight Cancellation",
             fc=LIGHT_ORANGE, ec=AWS_ORANGE, accent=AWS_ORANGE)
service_card(ax, CX[1], R2Y, SW, SH, "sqs",
             "Amazon SQS", "Disruption Queue",
             fc=LIGHT_ORANGE, ec=AWS_ORANGE, accent=AWS_ORANGE)
service_card(ax, CX[2], R2Y, SW, SH, "stepfn",
             "Step Functions", "InvokeHarness State",
             fc=LIGHT_ORANGE, ec=AWS_ORANGE, accent=AWS_ORANGE)

# Airline → EventBridge (straight down, same column)
varrow(ax, 5.4 + SW/2, R1Y, R2Y + SH,
       label="Flight\nCancelled", color=AWS_DARK, lo=(0.15, 0))
harrow(ax, CX[0]+SW, CX[1], R2Y+SH/2, color=AWS_ORANGE)        # EB → SQS
harrow(ax, CX[2]+SW/2, CX[1]+SW, R2Y+SH/2, color=AWS_ORANGE)   # SFN → SQS

# ── AgentCore Harness group  y=11.5 ──────────────────────────────────────────
HX, HY, HW, HH = 0.9, 11.5, 20.2, 7.0
group_header(ax, HX, HY, HW, HH,
             "AgentCore Harness — Travel Disruption Agent",
             fc=LIGHT_TEAL, ec=AWS_TEAL, header_fc=AWS_TEAL)

# SQS → Harness
varrow(ax, CX[1]+SW/2, R2Y, HY+HH,
       label="Invoke Harness\n(runtimeSessionId)", color=AWS_TEAL, lw=2.2, lo=(0.2,0))

# Core row  y=16.0
CR_Y = 16.0
service_card(ax, 1.5,  CR_Y, SW+0.4, SH, "bedrock",
             "Orchestrator Agent", "Claude Sonnet 4.6", "Strands Agent Loop",
             fc=WHITE, ec=AWS_TEAL, accent=AWS_TEAL)
service_card(ax, 5.6,  CR_Y, SW+0.4, SH, "memory",
             "AgentCore Memory", "Short + Long-term", "Passenger Context",
             fc=WHITE, ec=AWS_TEAL, accent=AWS_TEAL)
service_card(ax, 9.7,  CR_Y, SW+0.4, SH, "runtime",
             "Isolated microVM", "per Session", "AgentCore Runtime",
             fc=WHITE, ec=AWS_TEAL, accent=AWS_TEAL)

harrow(ax, 1.5+SW+0.4, 5.6, CR_Y+SH/2,
       label="Read/Write Context", color=AWS_TEAL)

# Tool row  y=13.2
TR_Y = 13.2
service_card(ax, 1.5,  TR_Y, SW, SH, "lambda",
             "Flight Agent", "Rebook Flight", "GDS API",
             fc=LIGHT_PURPLE, ec=AWS_PURPLE, accent=AWS_PURPLE)
service_card(ax, 8.2,  TR_Y, SW, SH, "lambda",
             "Notify Agent", "SMS / Email", "/ Push",
             fc=LIGHT_PURPLE, ec=AWS_PURPLE, accent=AWS_PURPLE)
service_card(ax, 12.1, TR_Y, SW, SH, "inline_fn",
             "Inline Function", "Human-in-Loop", "Escalation",
             fc="#FFF0F0", ec=AWS_RED, accent=AWS_RED)

# Orchestrator → tools
varrow(ax, 1.5+SW/2,  CR_Y, TR_Y+SH, color=AWS_PURPLE, lw=1.8)
varrow(ax, 8.2+SW/2,  CR_Y, TR_Y+SH, color=AWS_PURPLE, lw=1.8)
darrow(ax, 1.5+SW/2, CR_Y, 12.1+SW/2, TR_Y+SH,
       label="tool_use", color=AWS_RED, lw=1.8, lo=(2.0, 0.1))

# ── Integration row  y=8.8 ───────────────────────────────────────────────────
IR_Y = 8.8

# Gateway group box
rbox(ax, 0.8, IR_Y-0.3, 7.3, SH+0.8, fc="#E8F8F5", ec=AWS_TEAL, lw=1.5, r=0.2, z=2)
ax.text(1.1, IR_Y+SH+0.3, "AgentCore Gateway  ·  MCP / AWS_IAM",
        ha='left', va='center', fontsize=8, color=AWS_TEAL, fontweight='bold', zorder=3)

service_card(ax, 1.0,  IR_Y, SW, SH, "gateway",
             "AgentCore Gateway", "SigV4 / OAuth",
             fc=WHITE, ec=AWS_TEAL, accent=AWS_TEAL)
service_card(ax, 4.6,  IR_Y, SW, SH, "dynamodb",
             "Amazon DynamoDB", "Passenger Profiles",
             fc=WHITE, ec=AWS_GREEN, accent=AWS_GREEN)
service_card(ax, 8.2,  IR_Y, SW, SH, "sns",
             "Amazon SNS", "Traveler Notifications",
             fc=LIGHT_ORANGE, ec=AWS_ORANGE, accent=AWS_ORANGE)
service_card(ax, 11.8, IR_Y, SW, SH, "secrets",
             "Secrets Manager", "API Keys / Token Vault",
             fc="#FFF0F0", ec=AWS_RED, accent=AWS_RED)
service_card(ax, 15.4, IR_Y, SW, SH, "observability",
             "AgentCore Observability", "Unified Trace View",
             fc=LIGHT_TEAL, ec=AWS_TEAL, accent=AWS_TEAL)

# Tools → Integration
varrow(ax, 1.5+SW/2, TR_Y, IR_Y+SH, color=AWS_TEAL, lw=1.8)    # Flight → GW
varrow(ax, 8.2+SW/2, TR_Y, IR_Y+SH, color=AWS_ORANGE, lw=1.8)  # Notify → SNS

# Integration row horizontal
harrow(ax, 1.0+SW, 4.6, IR_Y+SH/2, color=AWS_GREEN)    # GW → DDB
harrow(ax, 4.6+SW, 8.2, IR_Y+SH/2, color=AWS_ORANGE)   # DDB → SNS
harrow(ax, 8.2+SW, 11.8, IR_Y+SH/2, color=AWS_RED)     # SNS → SM
harrow(ax, 11.8+SW, 15.4, IR_Y+SH/2, color=AWS_TEAL)   # SM → Obs

# Auto-trace diagonal from harness to Observability
darrow(ax, 12.1+SW/2, TR_Y, 15.4+SW/2, IR_Y+SH,
       label="Auto-traced", color=AWS_TEAL, lw=1.8, lo=(0.4, 0.1))

# ── CloudWatch  y=6.3 ────────────────────────────────────────────────────────
CW_Y = 6.3
service_card(ax, 14.0, CW_Y, SW+0.8, SH, "cloudwatch",
             "Amazon CloudWatch", "Logs & Metrics",
             fc=LIGHT_ORANGE, ec=AWS_ORANGE, accent=AWS_ORANGE)

varrow(ax, 15.4+SW/2, IR_Y, CW_Y+SH, color=AWS_ORANGE, lw=1.8)

# ── Legend ────────────────────────────────────────────────────────────────────
LY = 4.5
rbox(ax, 0.8, LY, 20.4, 1.6, fc=WHITE, ec=BORDER_GREY, lw=1.2, r=0.2, z=2)
ax.text(1.1, LY+1.38, "Legend", ha='left', va='center',
        fontsize=9, fontweight='bold', color=AWS_DARK, zorder=3)

legend_entries = [
    (AWS_TEAL,   LIGHT_TEAL,   "AgentCore: Harness / Gateway / Memory / Observability"),
    (AWS_PURPLE, LIGHT_PURPLE, "Lambda Tools: Flight Agent, Notify Agent"),
    (AWS_RED,    "#FFF0F0",    "Inline Function: Human-in-Loop"),
    (AWS_ORANGE, LIGHT_ORANGE, "AWS: EventBridge, SQS, SNS, CloudWatch"),
    (AWS_GREEN,  WHITE,        "Amazon DynamoDB"),
]
lxi = 1.1
for ec_c, fc_c, lbl in legend_entries:
    rbox(ax, lxi, LY+0.52, 0.38, 0.40, fc=fc_c, ec=ec_c, lw=2.0, r=0.08, z=3)
    ax.text(lxi+0.54, LY+0.72, lbl, ha='left', va='center',
            fontsize=8, color=TEXT_MID, zorder=3)
    lxi += 4.0

# ── Key facts bar ─────────────────────────────────────────────────────────────
KY = 2.8
rbox(ax, 0.8, KY, 20.4, 1.4, fc=AWS_DARK, ec=AWS_DARK, lw=0, r=0.25, z=2)
facts = [
    ("~8 sec",  "Recovery time\nper passenger"),
    ("0 lines", "Orchestration\ncode written"),
    ("microVM", "Isolated session\nper passenger"),
    ("30 days", "Memory retention\n(AgentCore)"),
    ("100%",    "Decisions\nauditable"),
]
fx = 2.2
for val, lbl in facts:
    ax.text(fx, KY+0.95, val, ha='center', va='center',
            fontsize=14, fontweight='bold', color=AWS_ORANGE, zorder=3)
    for i, line in enumerate(lbl.split('\n')):
        ax.text(fx, KY+0.52-i*0.22, line, ha='center', va='center',
                fontsize=7.5, color="#AAAAAA", zorder=3)
    if fx < 19:
        ax.plot([fx+1.7, fx+1.7], [KY+0.18, KY+1.18], color="#444444", lw=1, zorder=3)
    fx += 3.9

# ── Footer ────────────────────────────────────────────────────────────────────
ax.text(11, 2.1, "github.com/weraponge/travel-disruption-agentcore   ·   "
                 "Built on Amazon Bedrock AgentCore Harness",
        ha='center', va='center', fontsize=9, color=TEXT_MID,
        fontstyle='italic', zorder=2)

# ── Save ──────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0.2)
plt.savefig("travel-disruption-agentcore.png",
            dpi=180, bbox_inches='tight',
            facecolor=WHITE, edgecolor='none')
print("Saved: travel-disruption-agentcore.png")
