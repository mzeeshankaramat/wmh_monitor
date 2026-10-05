import csv
import collections
import datetime as dt
import statistics as s
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "wmh_occupancy.csv"
OUT_DIR = ROOT
MIN_READINGS = 5

groups = {"weekday": collections.defaultdict(list), "weekend": collections.defaultdict(list)}
with open(CSV, newline="") as f:
    for r in csv.DictReader(f):
        t = dt.datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M")
        kind = "weekend" if t.weekday() >= 5 else "weekday"
        groups[kind][t.hour].append(100 * int(r["occupancy"]) / int(r["max_capacity"]))


def label(h):
    return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"


SURFACE = "#FFFFFF"
INK = "#1F2328"
MUTED = "#6B7280"
GRID = "#E5E7EB"
BAR = "#2F6690"

for kind, by in groups.items():
    hours = [h for h in sorted(by) if len(by[h]) >= MIN_READINGS]
    means = [s.mean(by[h]) for h in hours]
    counts = [len(by[h]) for h in hours]

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ax.bar(range(len(hours)), means, color=BAR, width=0.7, zorder=3)
    for x, m in enumerate(means):
        ax.text(x, m + 0.5, f"{m:.0f}%", ha="center", va="bottom", fontsize=9, color=INK)

    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels([f"{label(h)}\nn={n}" for h, n in zip(hours, counts)], fontsize=8.5, color=MUTED)
    ax.set_ylabel("Average occupancy (% of capacity)", color=INK, fontsize=10)
    ax.set_xlabel("Hour of day (readings taken during that hour)", color=INK, fontsize=10)
    title = "Weekdays" if kind == "weekday" else "Weekends"
    ax.set_title(f"Average occupancy by hour, {title}", loc="left", color=INK, fontsize=13, fontweight="bold", pad=14)

    ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(axis="y", colors=MUTED, length=0, labelsize=9)
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0, max(means) * 1.12)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(decimals=0))

    plt.tight_layout()
    out = OUT_DIR / f"hourly_occupancy_{kind}s.png"
    plt.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    print("saved", out, "hours:", hours)
