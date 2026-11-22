"""Draw the README charts from results/local-model-trial.json (no plotting libraries needed).

    python tools/plot_results.py

Writes docs/images/agent-scores.svg, judge-calibration.svg and tool-use.svg.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((REPO_ROOT / "results" / "local-model-trial.json").read_text())
OUT = REPO_ROOT / "docs" / "images"

BG, PANEL, GRID, TEXT, MUTED = "#0b1220", "#111c33", "#243049", "#f1f5f9", "#94a3b8"
MODEL_COLORS = {"llama3.2": "#60a5fa", "qwen2.5:7b": "#2dd4bf", "llama3.1:8b": "#fbbf24"}
KIND_COLORS = {"reference": "#34d399", "trap": "#fbbf24", "non_answer": "#94a3b8"}
KIND_LABELS = {"reference": "correct reference answer", "trap": "confident wrong answer",
               "non_answer": "answer that found nothing"}
FONT = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def svg(width: int, height: int, title: str, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" font-family="{FONT}">\n'
            f'<title>{title}</title>\n<rect width="{width}" height="{height}" rx="18" fill="{BG}"/>\n{body}</svg>\n')


def text(x, y, s, size=13, fill=TEXT, anchor="start", weight="400"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>\n'


def legend(items, x, y):
    out, cx = "", x
    for label, color in items:
        out += f'<rect x="{cx}" y="{y - 11}" width="14" height="14" rx="3" fill="{color}"/>\n'
        out += text(cx + 22, y, label, 13, MUTED)
        cx += 40 + 7.2 * len(label)
    return out


def y_axis(x0, x1, y0, y1, top=100, step=25):
    out = ""
    for v in range(0, top + 1, step):
        y = y0 - (y0 - y1) * v / top
        out += f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{GRID}"/>\n'
        out += text(x0 - 10, y + 4, f"{v}%", 12, MUTED, "end")
    return out


def agent_scores() -> str:
    runs = DATA["agent_runs"]
    scenarios = ["ledger-drift", "signal-check", "root-cause"]
    models = list(MODEL_COLORS)
    W, H, x0, x1, y0, y1 = 900, 470, 80, 860, 390, 110
    body = text(40, 48, "Local agents on the three scenarios", 22, weight="700")
    body += text(40, 72, "Score as a share of the available points. One run per model and scenario, same judge for all.", 13, MUTED)
    body += legend([(m, c) for m, c in MODEL_COLORS.items()], 40, 98)
    body += y_axis(x0, x1, y0, y1)
    group_w = (x1 - x0) / len(scenarios)
    bar_w = 46
    for gi, sc in enumerate(scenarios):
        gx = x0 + gi * group_w + group_w / 2
        for mi, m in enumerate(models):
            r = next(r for r in runs if r["scenario"] == sc and r["model"] == m)
            bx = gx + (mi - 1) * (bar_w + 10) - bar_w / 2
            h = (y0 - y1) * r["percent"] / 100
            body += f'<rect x="{bx}" y="{y0 - h}" width="{bar_w}" height="{max(h, 2)}" rx="5" fill="{MODEL_COLORS[m]}"/>\n'
            body += text(bx + bar_w / 2, y0 - max(h, 2) - 8, f'{r["percent"]:.0f}%', 13, TEXT, "middle", "600")
            if r["status"] != "scored":
                note = "no answer" if "step limit" in r["status"] else "malformed"
                body += text(bx + bar_w / 2, y0 + 34, note, 11, MUTED, "middle")
        body += text(gx, y0 + 20, sc, 14, TEXT, "middle", "600")
    body += text(40, H - 18, "Single runs at temperature 0, judged by llama3.1:8b. Indicative only: no repeats, so no variance estimate.", 12, MUTED)
    return svg(W, H, "Agent scores by model and scenario", body)


def judge_calibration() -> str:
    cal = DATA["judge_calibration"]
    scores, th = cal["scores_percent"], cal["thresholds"]
    limits = {"reference": ("min", th["reference_min"]), "trap": ("max", th["trap_max"]),
              "non_answer": ("max", th["non_answer_max"])}
    judges = list(scores)
    W, H, x0, x1, y0, y1 = 900, 500, 80, 860, 390, 120
    body = text(40, 48, "Which model is fit to be the judge?", 22, weight="700")
    body += text(40, 72, "Average score each judge gives three answers of known quality. Short lines mark the required limit.", 13, MUTED)
    body += legend([(KIND_LABELS[k], c) for k, c in KIND_COLORS.items()], 40, 100)
    body += y_axis(x0, x1, y0, y1)
    group_w = (x1 - x0) / len(judges)
    bar_w = 52
    for gi, j in enumerate(judges):
        gx = x0 + gi * group_w + group_w / 2
        ok_all = True
        for ki, kind in enumerate(KIND_COLORS):
            avg = sum(scores[j][kind]) / len(scores[j][kind])
            direction, limit = limits[kind]
            ok = avg >= limit if direction == "min" else avg <= limit
            ok_all &= ok
            bx = gx + (ki - 1) * (bar_w + 12) - bar_w / 2
            h = (y0 - y1) * avg / 100
            body += f'<rect x="{bx}" y="{y0 - max(h, 2)}" width="{bar_w}" height="{max(h, 2)}" rx="5" fill="{KIND_COLORS[kind]}" opacity="{1 if ok else 0.45}"/>\n'
            body += text(bx + bar_w / 2, y0 - max(h, 2) - 8, f"{avg:.0f}%", 13, TEXT, "middle", "600")
            ly = y0 - (y0 - y1) * limit / 100
            body += f'<line x1="{bx - 5}" y1="{ly}" x2="{bx + bar_w + 5}" y2="{ly}" stroke="#f1f5f9" stroke-width="2" stroke-dasharray="4 3"/>\n'
        body += text(gx, y0 + 22, j, 14, TEXT, "middle", "600")
        body += text(gx, y0 + 42, "passes calibration" if ok_all else "fails calibration", 12,
                     "#34d399" if ok_all else MUTED, "middle", "600")
    body += text(40, H - 18, "Limits: reference at least 85%, wrong answer at most 40%, non-answer at most 15%. Faded bars missed their limit.", 12, MUTED)
    return svg(W, H, "Judge calibration by model", body)


def tool_use() -> str:
    runs = DATA["agent_runs"]
    cats = [("required", "required tool", "#2dd4bf"), ("distractor", "unneeded tool", "#fbbf24"), ("other", "other", "#94a3b8")]
    models = list(MODEL_COLORS)
    totals = {m: {c: sum(r["tools"][c] for r in runs if r["model"] == m) for c, _, _ in cats} for m in models}
    mx = max(sum(t.values()) for t in totals.values())
    W, H, x0, scale = 900, 370, 190, 620 / max(mx, 1)
    body = text(40, 48, "Which tools did each agent call?", 22, weight="700")
    body += text(40, 72, "All tool calls across the three scenarios. The unneeded tools are the distractors in each scenario's tool policy.", 13, MUTED)
    body += legend([(label, color) for _, label, color in cats], 40, 100)
    for i, m in enumerate(models):
        y = 140 + i * 62
        body += text(x0 - 16, y + 24, m, 14, TEXT, "end", "600")
        x = x0
        for key, _, color in cats:
            n = totals[m][key]
            if n:
                w = n * scale
                body += f'<rect x="{x}" y="{y}" width="{w}" height="38" rx="5" fill="{color}"/>\n'
                body += text(x + w / 2, y + 24, str(n), 14, BG, "middle", "700")
                x += w + 2
        body += text(x + 8, y + 24, f"{sum(totals[m].values())} calls", 12, MUTED)
    body += text(40, H - 18, "Tool use is recorded in each run's trajectory file. It is not scored automatically.", 12, MUTED)
    return svg(W, H, "Tool calls by category and model", body)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("agent-scores", agent_scores), ("judge-calibration", judge_calibration), ("tool-use", tool_use)):
        (OUT / f"{name}.svg").write_text(fn())
        print("wrote", OUT / f"{name}.svg")
