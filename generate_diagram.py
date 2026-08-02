"""
generate_diagram.py
Professional architecture diagram for Travel Disruption Agent
AWS colour scheme, no emoji dependency.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np

# ── AWS colour palette ─────────────────────────────────────────────────────
AWS_ORANGE   = "#FF9900"
AWS_DARK     = "#232F3E"
AWS_TEAL     = "#01A88D"
AWS_PURPLE   = "#8C4FFF"
AWS_GREEN    = "#1A7A3F"
AWS_RED      = "#BF0816"
AWS_BLUE     = "#0073BB"
LIGHT_TEAL   = "#E6F6F4"
LIGHT_ORANGE = "#FFF8EE"
LIGHT_PURPLE = "#F3EEFF"
LIGHT_GREY   = "#F5F5F5"
BORDER_GREY  = "#D0D0D0"
WHITE        = "#FFFFFF"
TEXT_DARK    = "#111111"
TEXT_MID     = "#555555"

fig, ax = plt.subplots(figsize=(20, 24))
ax.set_xlim(0, 20)
ax.set_ylim(0, 24)
ax.axis('off')
fig.patch.set_facecolor(WHITE)

# ── Primitives ─────────────────────────────────────────────────────────────
def rbox(ax, x, y, w, h, fc=WHITE, ec=BORDER_GREY, lw=1.5, r=0.25, z=2, alpha=1.0):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha)
    ax.add_patch(p)

def badge(ax, cx, cy, label, fc=AWS_ORANGE, tc=WHITE, fs=7.5, z=5):
    """Coloured pill badge for service abbreviation."""
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=fs, fontweight='bold', color=tc, zorder=z,
            bbox=dict(boxstyle='round,pad=0.25', fc=fc, ec='none'))

def service_box(ax, x, y, w, h,
                abbr, abbr_color,
                title, subtitle="",
                fc=WHITE, ec=BORDER_GREY, z=3):
    """Draw a service card: coloured abbreviation bar + title + subtitle."""
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=1.8, r=0.2, z=z)
    # coloured left stripe
    stripe = FancyBboxPatch((x, y), 0.22, h,
                            boxstyle="round,pad=0,rounding_size=0.15",
                            fc=abbr_color, ec='none', zorder=z+1)
    ax.add_patch(stripe)
    # abbreviation text rotated
    ax.text(x + 0.11, y + h/2, abbr,
            ha='center', va='center', fontsize=6.5, fontweight='bold',
            color=WHITE, rotation=90, zorder=z+2)
    # title
    cx = x + 0.22 + (w - 0.22) / 2
    ax.text(cx, y + h - 0.18, title,
            ha='center', va='top', fontsize=8.5, fontweight='bold',
            color=TEXT_DARK, zorder=z+1, wrap=True)
    if subtitle:
        ty = y + h - 0.42
        for line in subtitle.split('\n'):
            ax.text(cx, ty, line,
                    ha='center', va='top', fontsize=7.5, color=TEXT_MID, zorder=z+1)
            ty -= 0.2

def group(ax, x, y, w, h, title, fc=LIGHT_TEAL, ec=AWS_TEAL, lw=2.5,
          header_fc=AWS_TEAL, z=1):
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, r=0.35, z=z)
    rbox(ax, x, y+h-0.45, w, 0.45, fc=header_fc, ec=ec, lw=lw, r=0.2, z=z+1)
    ax.text(x + 0.4, y + h - 0.225, title,
            ha='left', va='center', fontsize=10, fontweight='bold',
            color=WHITE, zorder=z+2)

def varrow(ax, x, y1, y2, label="", lw=1.8, color=AWS_DARK, lo=(0.15, 0)):
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw), zorder=6)
    if label:
        mx, my = x + lo[0], (y1+y2)/2 + lo[1]
        ax.text(mx, my, label, ha='left', va='center', fontsize=7.5,
                color=color, fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.15', fc=WHITE, ec='none', alpha=0.9),
                zorder=7)

def harrow(ax, x1, x2, y, label="", lw=1.8, color=AWS_DARK, lo=(0, 0.12)):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw), zorder=6)
    if label:
        mx, my = (x1+x2)/2 + lo[0], y + lo[1]
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=7.5,
                color=color, fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.15', fc=WHITE, ec='none', alpha=0.9),
                zorder=7)

def diagonal_arrow(ax, x1, y1, x2, y2, label="", lw=1.8, color=AWS_DARK, lo=(0.1,0.1)):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle="arc3,rad=0"), zorder=6)
    if label:
        mx = (x1+x2)/2 + lo[0]
        my = (y1+y2)/2 + lo[1]
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=7.5,
                color=color, fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.15', fc=WHITE, ec='none', alpha=0.9),
                zorder=7)

# ══════════════════════════════════════════════════════════════════════════════
# TITLE BANNER
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 0.5, 22.8, 19, 1.0, fc=AWS_DARK, ec=AWS_DARK, lw=0, r=0.3, z=1)
ax.text(10, 23.42, "Travel Disruption Agent", ha='center', va='center',
        fontsize=22, fontweight='bold', color=WHITE, zorder=2)
ax.text(10, 23.05, "Amazon Bedrock AgentCore Harness   ·   Travel & Hospitality Industry",
        ha='center', va='center', fontsize=11, color=AWS_ORANGE, zorder=2)

# ══════════════════════════════════════════════════════════════════════════════
# AWS CLOUD BORDER
# ══════════════════════════════════════════════════════════════════════════════
rbox(ax, 0.5, 0.5, 19, 22.0, fc="#FAFAFA", ec=AWS_DARK, lw=2.5, r=0.5, z=0)
ax.text(1.1, 22.25, "AWS Cloud", ha='left', va='center',
        fontsize=10, fontweight='bold', color=AWS_DARK, zorder=2)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 1 — External actors  (y=20.5)
# ══════════════════════════════════════════════════════════════════════════════
SW, SH = 2.6, 1.3   # standard service box dimensions
R1Y = 20.3

# Outside the cloud
ax.text(5.0, 21.9, "External", ha='center', va='center',
        fontsize=8, color=TEXT_MID, fontstyle='italic')

service_box(ax, 1.8,  R1Y, SW, SH, "USER",  "#607D8B",
            "Disrupted Traveler", "", fc=LIGHT_ORANGE, ec="#607D8B")
service_box(ax, 5.3,  R1Y, SW, SH, "GDS",   "#607D8B",
            "Airline / GDS\nSystem", "", fc=LIGHT_ORANGE, ec="#607D8B")

harrow(ax, 4.0, 5.3, R1Y + SH/2, label="Cancel Flight", color=AWS_DARK)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 2 — Event ingestion  (y=18.0)
# ══════════════════════════════════════════════════════════════════════════════
R2Y = 18.0

service_box(ax, 2.0,  R2Y, SW, SH, "EB",   AWS_ORANGE,
            "Amazon\nEventBridge", "Flight Cancellation",
            fc=LIGHT_ORANGE, ec=AWS_ORANGE)
service_box(ax, 5.5,  R2Y, SW, SH, "SQS",  AWS_ORANGE,
            "Amazon SQS", "Disruption Queue",
            fc=LIGHT_ORANGE, ec=AWS_ORANGE)
service_box(ax, 9.0,  R2Y, SW, SH, "SFN",  AWS_ORANGE,
            "Step Functions", "InvokeHarness State",
            fc=LIGHT_ORANGE, ec=AWS_ORANGE)

# External → EventBridge (go straight down via EventBridge column, no diagonal cross)
varrow(ax, 2.0 + SW/2, R1Y, R2Y + SH,
       label="Flight Cancelled", color=AWS_DARK, lo=(0.15, 0))
harrow(ax, 4.6, 5.5, R2Y + SH/2, color=AWS_ORANGE)
harrow(ax, 9.0, 8.1, R2Y + SH/2, color=AWS_ORANGE)  # SFN → SQS

# ══════════════════════════════════════════════════════════════════════════════
# ROW 3 — AgentCore Harness group  (y=11.8)
# ══════════════════════════════════════════════════════════════════════════════
HX, HY, HW, HH = 1.0, 12.0, 18.0, 5.6
group(ax, HX, HY, HW, HH,
      "AgentCore Harness — Travel Disruption Agent",
      fc=LIGHT_TEAL, ec=AWS_TEAL, header_fc=AWS_TEAL)

# SQS → Harness
varrow(ax, 5.5 + SW/2, R2Y, HY + HH,
       label="Invoke Harness\n(runtimeSessionId)", color=AWS_TEAL, lw=2.2, lo=(0.2,0))

# Core row
CR_Y = 15.5
service_box(ax, 2.0,  CR_Y, SW+0.4, SH, "ORCH", AWS_TEAL,
            "Orchestrator Agent", "Claude Sonnet 4.6\nStrands Agent Loop",
            fc=WHITE, ec=AWS_TEAL)
service_box(ax, 6.2,  CR_Y, SW+0.4, SH, "MEM",  AWS_TEAL,
            "AgentCore Memory", "Short + Long-term\nPassenger Context",
            fc=WHITE, ec=AWS_TEAL)
service_box(ax, 10.4, CR_Y, SW+0.4, SH, "VM",   AWS_TEAL,
            "Isolated microVM", "per Session\nAgentCore Runtime",
            fc=WHITE, ec=AWS_TEAL)

harrow(ax, 4.4, 6.2, CR_Y + SH/2,
       label="Read/Write Context", color=AWS_TEAL)

# Tool row — aligned with integration row columns
TR_Y = 13.2
service_box(ax, 2.0,  TR_Y, SW, SH, "FLT",  AWS_PURPLE,
            "Flight Agent", "Rebook Flight\nGDS API",
            fc=LIGHT_PURPLE, ec=AWS_PURPLE)
service_box(ax, 7.0,  TR_Y, SW, SH, "NTF",  AWS_PURPLE,
            "Notify Agent", "SMS / Email\n/ Push",
            fc=LIGHT_PURPLE, ec=AWS_PURPLE)
service_box(ax, 11.5, TR_Y, SW, SH, "ESC",  AWS_RED,
            "Inline Function", "Human-in-Loop\nEscalation",
            fc="#FFF0F0", ec=AWS_RED)

# Orchestrator → tools
varrow(ax, 2.0 + SW/2,    CR_Y, TR_Y + SH, color=AWS_PURPLE, lw=1.8)
varrow(ax, 7.0 + SW/2,    CR_Y, TR_Y + SH, color=AWS_PURPLE, lw=1.8)
diagonal_arrow(ax, 2.0 + SW/2, CR_Y, 11.5 + SW/2, TR_Y + SH,
               label="tool_use", color=AWS_RED, lw=1.8, lo=(2.0, 0.1))

# ══════════════════════════════════════════════════════════════════════════════
# ROW 4 — Integration layer  (y=9.5)
# ══════════════════════════════════════════════════════════════════════════════
IR_Y = 9.5

# Integration row — 5 boxes evenly spaced across width 1.2 to 19.0
# Box positions: GW=1.5, DDB=4.6, SNS=7.7, SM=10.8, OBS=13.9
# Gateway group box covers GW+DDB
rbox(ax, 1.2, IR_Y - 0.2, 6.8, SH + 0.7, fc="#E8F8F5", ec=AWS_TEAL, lw=1.5, r=0.2, z=2)
ax.text(1.5, IR_Y + SH + 0.25, "AgentCore Gateway  ·  MCP / AWS_IAM",
        ha='left', va='center', fontsize=7.5, color=AWS_TEAL, fontweight='bold', zorder=3)

service_box(ax, 1.5,  IR_Y, SW, SH, "GW",  AWS_TEAL,
            "AgentCore\nGateway", "SigV4 / OAuth",
            fc=WHITE, ec=AWS_TEAL)
service_box(ax, 4.6,  IR_Y, SW, SH, "DDB", AWS_GREEN,
            "Amazon\nDynamoDB", "Passenger Profiles",
            fc=WHITE, ec=AWS_GREEN)
service_box(ax, 7.7,  IR_Y, SW, SH, "SNS", AWS_ORANGE,
            "Amazon SNS", "Traveler\nNotifications",
            fc=LIGHT_ORANGE, ec=AWS_ORANGE)
service_box(ax, 10.8, IR_Y, SW, SH, "SM",  AWS_RED,
            "Secrets\nManager", "API Keys / Token Vault",
            fc="#FFF0F0", ec=AWS_RED)
service_box(ax, 13.9, IR_Y, SW, SH, "OBS", AWS_TEAL,
            "AgentCore\nObservability", "Unified Trace View",
            fc=LIGHT_TEAL, ec=AWS_TEAL)

# Tools → Integration (straight down — Flight→GW, Notify→SNS)
varrow(ax, 2.0 + SW/2, TR_Y, IR_Y + SH, color=AWS_TEAL,   lw=1.8)
varrow(ax, 7.0 + SW/2, TR_Y, IR_Y + SH, color=AWS_ORANGE, lw=1.8)

# Integration row horizontal connections
harrow(ax, 4.1, 4.6,  IR_Y + SH/2, color=AWS_GREEN)          # GW → DDB
harrow(ax, 7.2, 7.7,  IR_Y + SH/2, color=AWS_ORANGE)         # DDB → SNS
harrow(ax, 10.3, 10.8, IR_Y + SH/2, color=AWS_RED)           # SNS → SM
harrow(ax, 13.4, 13.9, IR_Y + SH/2, color=AWS_TEAL)          # SM → OBS

# Harness → Observability (auto-trace diagonal)
diagonal_arrow(ax, 11.5 + SW/2, TR_Y, 13.9 + SW/2, IR_Y + SH,
               label="Auto-traced", color=AWS_TEAL, lw=1.8, lo=(0.5, 0.1))

# ══════════════════════════════════════════════════════════════════════════════
# ROW 5 — CloudWatch  (y=7.2)
# ══════════════════════════════════════════════════════════════════════════════
OB_Y = 7.2
service_box(ax, 12.6, OB_Y, SW + 0.8, SH, "CW", AWS_ORANGE,
            "Amazon\nCloudWatch", "Logs & Metrics",
            fc=LIGHT_ORANGE, ec=AWS_ORANGE)

varrow(ax, 13.9 + SW/2, IR_Y, OB_Y + SH, color=AWS_ORANGE, lw=1.8)

# ══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════════════════
LX, LY = 1.0, 5.5
rbox(ax, LX, LY, 18, 1.6, fc=WHITE, ec=BORDER_GREY, lw=1.2, r=0.2, z=2)
ax.text(LX + 0.3, LY + 1.35, "Legend", ha='left', va='center',
        fontsize=9, fontweight='bold', color=AWS_DARK, zorder=3)

legend_entries = [
    (AWS_TEAL,   LIGHT_TEAL,   "AgentCore: Harness / Gateway / Memory / Observability"),
    (AWS_PURPLE, LIGHT_PURPLE, "Lambda Tools: Flight Agent, Notify Agent"),
    (AWS_RED,    "#FFF0F0",    "Inline Function: Human-in-Loop Escalation"),
    (AWS_ORANGE, LIGHT_ORANGE, "AWS Services: EventBridge, SQS, SNS, CloudWatch"),
    (AWS_GREEN,  WHITE,        "Amazon DynamoDB"),
]
lxi = LX + 0.3
for ec_c, fc_c, lbl in legend_entries:
    rbox(ax, lxi, LY + 0.55, 0.35, 0.38, fc=fc_c, ec=ec_c, lw=1.8, r=0.08, z=3)
    ax.text(lxi + 0.5, LY + 0.74, lbl, ha='left', va='center',
            fontsize=7.8, color=TEXT_MID, zorder=3)
    lxi += 3.55

# ══════════════════════════════════════════════════════════════════════════════
# KEY FACTS BAR
# ══════════════════════════════════════════════════════════════════════════════
KY = 3.8
rbox(ax, 1.0, KY, 18, 1.4, fc=AWS_DARK, ec=AWS_DARK, lw=0, r=0.25, z=2)
facts = [
    ("~8 sec", "Recovery time\nper passenger"),
    ("0 lines", "Orchestration\ncode written"),
    ("microVM", "Isolated session\nper passenger"),
    ("30 days", "Memory retention\n(AgentCore)"),
    ("100%", "Decisions\nauditable"),
]
fx = 2.0
for val, lbl in facts:
    ax.text(fx, KY + 0.95, val, ha='center', va='center',
            fontsize=14, fontweight='bold', color=AWS_ORANGE, zorder=3)
    for i, line in enumerate(lbl.split('\n')):
        ax.text(fx, KY + 0.52 - i*0.22, line, ha='center', va='center',
                fontsize=7.5, color="#AAAAAA", zorder=3)
    if fx < 17:
        ax.plot([fx + 1.55, fx + 1.55], [KY + 0.2, KY + 1.15],
                color="#444444", lw=1, zorder=3)
    fx += 3.5

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
ax.text(10, 3.0, "github.com/weraponge/travel-disruption-agentcore   ·   "
                 "Built on Amazon Bedrock AgentCore Harness",
        ha='center', va='center', fontsize=8.5, color=TEXT_MID, fontstyle='italic',
        zorder=2)

# ── Save ──────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=0.2)
plt.savefig("travel-disruption-agentcore.png",
            dpi=180, bbox_inches='tight',
            facecolor=WHITE, edgecolor='none')
print("Saved: travel-disruption-agentcore.png")
