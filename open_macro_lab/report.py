"""Self-contained local HTML. SVG is generated from reviewed rows; no CDN or server."""

import csv
import html
import io
import json
import shutil
from decimal import Decimal
from pathlib import Path

from .core import canonical


def esc(value):
    return html.escape(str(value), quote=True)


def number(value, signed=False):
    if value is None:
        return "Unavailable"
    return format(Decimal(value), "+,.3f" if signed else ",.3f")


def scroll_open(label, kind):
    """Keep wide content keyboard-scrollable even without JavaScript enhancement."""
    return (f'<div class="{kind}-scroll scroll-area" data-scroll-kind="{kind}" '
            f'role="region" aria-label="{esc(label)}" tabindex="0">')


def chart(rows, series, label, zero=True, height=270):
    """Line gaps stay visible. Real date spacing, zero-based levels, explicit units."""
    from datetime import date
    width, left, right, top, bottom = 940, 75, 24, 22, 42
    values = [float(r[k]) for r in rows for k, _, _, _ in series if r[k] is not None]
    if not values:
        return '<p class="empty">No complete observations for this chart.</p>'
    lo, hi = min(values), max(values)
    if zero:
        lo, hi = min(0, lo), max(0, hi)
    span = hi - lo
    if span == 0:
        span = max(1, abs(hi) * 0.1)
    hi += span * .08
    if lo < 0:
        lo -= span * .08
    if hi == lo:
        hi = lo + 1
    start, end = date.fromisoformat(rows[0]["date"]), date.fromisoformat(rows[-1]["date"])
    days = max(1, (end-start).days)
    x = lambda day: left + (date.fromisoformat(day) - start).days / days * (width-left-right)
    y = lambda value: top + (hi-float(value)) / (hi-lo) * (height-top-bottom)
    pieces = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}. USD billions. Exact values in the history table."><title>{esc(label)}</title>']
    for i in range(5):
        val = lo + (hi-lo)*i/4
        yp = y(val)
        pieces.append(f'<line x1="{left}" y1="{yp:.2f}" x2="{width-right}" y2="{yp:.2f}" stroke="#dce2e5"/><text x="{left-12}" y="{yp+5:.2f}" text-anchor="end">{val:,.0f}</text>')
    for i in sorted(set((0, len(rows)//2, len(rows)-1))):
        r = rows[i]
        anchor = "start" if i == 0 else "end" if i == len(rows)-1 else "middle"
        pieces.append(f'<text x="{x(r["date"]):.2f}" y="{height-10}" text-anchor="{anchor}">{esc(r["date"])}</text>')
    for key, name, color, dash in series:
        commands, connected = [], False
        for r in rows:
            if r[key] is None:
                connected = False
                continue
            commands.append(("L" if connected else "M") + f'{x(r["date"]):.2f},{y(r[key]):.2f}')
            connected = True
        pieces.append(f'<path d="{" ".join(commands)}" fill="none" stroke="{color}" stroke-width="2.8" stroke-dasharray="{dash}"/>')
        valid = [r for r in rows if r[key] is not None]
        # A one-point history must still have a visible mark.
        if valid:
            last = valid[-1]
            pieces.append(f'<circle cx="{x(last["date"]):.2f}" cy="{y(last[key]):.2f}" r="4" fill="{color}"/>')
    pieces.append('</svg>')
    return scroll_open(label, "chart") + "".join(pieces) + '</div>'


def driver_chart(window, method):
    if not window:
        return '<p class="empty">The exact four-week endpoint is unavailable.</p>'
    contrib = window["contributions"]
    maximum = max([abs(float(v)) for v in contrib.values()] + [1])
    result = ['<svg class="chart driver-chart" viewBox="0 0 760 180" role="img" aria-label="Four-week accounting contributions in USD billions; exact values follow in table.">', '<line x1="440" y1="12" x2="440" y2="154" stroke="#75818c"/>']
    for i, (s, v) in enumerate(contrib.items()):
        value, yp = float(v), 20+i*45
        length = abs(value)/maximum*175
        start = 440 if value >= 0 else 440-length
        color = "#245c87" if value >= 0 else "#9a6424"
        result.append(f'<text x="0" y="{yp+20}">{esc(method["series"][s]["label"])}</text><rect x="{start:.2f}" y="{yp}" width="{length:.2f}" height="28" rx="2" fill="{color}"/><text x="750" y="{yp+20}" text-anchor="end">{number(v, True)}</text>')
    result.append('<text x="440" y="176" text-anchor="middle">0 · USD bn</text></svg>')
    return scroll_open("Four-week accounting contributions", "chart") + "".join(result) + '</div>'


CSS = """
:root{--ink:#182936;--muted:#526573;--paper:#f4f3ee;--white:#fff;--line:#d9dfdf;--blue:#245c87;--gold:#9a6424;--soft:#e9f0f4}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--blue);text-underline-offset:3px}a:hover{color:#123652}button{font:inherit;cursor:pointer}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #b97819;outline-offset:4px}.skip{position:absolute;top:-80px;background:white;padding:12px}.skip:focus{top:0}
.wrap{max-width:1320px;margin:auto;padding:0 40px}.top{border-bottom:1px solid var(--line);background:#fff}.masthead{display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:88px}.brand{display:flex;align-items:center;gap:14px}.mark{width:32px;height:32px;display:grid;grid-template-columns:1fr 1fr;gap:4px}.mark i{background:var(--blue)}.mark i:last-child{background:#b88a49}.brand strong{font-size:20px;letter-spacing:-.6px}.brand small{display:block;color:var(--muted);font-size:10px;letter-spacing:1.8px;text-transform:uppercase}nav{display:flex;gap:22px;font-size:13px}nav a{color:var(--ink);text-decoration:none}.intro{padding:45px 0 32px}.eyebrow{font-size:11px;letter-spacing:1.7px;text-transform:uppercase;font-weight:700;color:var(--muted)}.issuebar{display:flex;justify-content:space-between;align-items:center;gap:20px}.badge{display:inline-flex;padding:5px 10px;border:1px solid #9eb5c5;border-radius:3px;font-size:11px;font-weight:650;letter-spacing:.8px;text-transform:uppercase;background:#eff5f8}.badge.demo{background:#fff0d8;color:#744c1a;border-color:#c99550}h1{font-family:Georgia,serif;font-weight:400;font-size:clamp(36px,4.3vw,60px);letter-spacing:-1.9px;line-height:1.09;max-width:940px;margin:22px 0 18px}h2{font-size:25px;letter-spacing:-.7px;line-height:1.2;margin:0}h3{font-size:18px;line-height:1.35;margin:0 0 14px}p{margin:0 0 16px}.lede{color:var(--muted);max-width:800px;font-size:18px}.meta{color:var(--muted);font-size:12px}.notice{padding:17px 20px;border-left:3px solid var(--gold);background:#f7eddc;margin:18px 0}.notice p:last-child{margin:0}.metrics{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);background:#fff}.metric{padding:24px 26px;border-right:1px solid var(--line)}.metric:last-child{border:0}.metric-label{font-size:12px;color:var(--muted)}.value{font-size:clamp(25px,3vw,40px);font-weight:550;letter-spacing:-1.3px;margin:9px 0 4px;line-height:1.2;font-variant-numeric:tabular-nums}.unit{color:var(--muted);font-size:12px}.metric small{display:block;color:var(--muted);font-size:11px;margin-top:12px}
section{scroll-margin-top:20px;margin:42px 0}.section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:20px}.section-num{font-size:11px;letter-spacing:1px;color:var(--muted);margin-bottom:8px}.grid{display:grid;grid-template-columns:minmax(0,2fr) minmax(280px,1fr);gap:24px}.panel{background:var(--white);border:1px solid var(--line);padding:28px;min-width:0}.panel.blue{background:#e9f0f4;border-color:#cfdde6}.panel p:last-child{margin-bottom:0}.legend{display:flex;gap:20px;flex-wrap:wrap;font-size:12px;margin:12px 0 5px}.legend span:before{content:"";display:inline-block;width:22px;border-top:3px solid var(--blue);vertical-align:middle;margin-right:7px}.legend .reserve:before{border-top:3px dashed #9a6424}.chart{width:100%;height:auto;display:block;overflow:visible}.chart text{font:14px system-ui,sans-serif;fill:#526573}.chart path,.chart line{vector-effect:non-scaling-stroke}.chart-note{font-size:11px;color:var(--muted);margin:6px 0 0}.rangebar{display:flex;gap:5px;margin:8px 0 15px}.rangebar button{border:1px solid var(--line);border-radius:3px;background:white;padding:6px 12px;font-size:12px;color:var(--muted)}.rangebar button[aria-pressed=true]{background:var(--ink);color:white;border-color:var(--ink)}[hidden]{display:none!important}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.component{padding:20px 24px}.component .chart text{font-size:16px}.component h3{font-size:14px;margin:0}.component .current{font-size:24px;margin:6px 0;letter-spacing:-.8px}.formula{padding:16px;background:#f0f3f4;font:14px/1.7 ui-monospace,SFMono-Regular,monospace;margin:14px 0;overflow-wrap:anywhere}.recipe-number{font-size:11px;text-transform:uppercase;letter-spacing:1.2px;color:var(--blue);margin-bottom:12px}.definition{font-size:14px;color:var(--muted)}.table-scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}th{text-align:left;color:var(--muted);font-weight:600;background:#f2f4f4;font-size:11px}td,th{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}td.num,th.num{text-align:right;white-space:nowrap}.table-scroll td:first-child,.table-scroll th:first-child{white-space:nowrap}tbody tr:hover{background:#f5f7f8}caption{text-align:left;margin:0 0 12px;color:var(--muted);font-size:12px}.small{font-size:13px;color:var(--muted)}.pill{font-size:10px;letter-spacing:.6px;background:#e8eef2;padding:4px 6px;white-space:nowrap}.audit{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.audit .panel{padding:22px}.audit h3{font-size:14px}.audit p{font-size:13px;color:var(--muted)}details{border-top:1px solid var(--line);padding:14px 0}summary{cursor:pointer;font-size:13px;font-weight:650}details>div{padding-top:16px}.code{font:12px/1.8 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#eaf0f3;padding:18px;border-radius:3px}.hash{font:11px/1.6 ui-monospace,monospace;overflow-wrap:anywhere}.sources td{font-size:12px}.sources td:first-child{min-width:150px}.foot{border-top:1px solid var(--line);padding:28px 0 45px;color:var(--muted);font-size:12px;display:flex;gap:30px;justify-content:space-between}.foot p{max-width:800px}ul{padding-left:20px}li{margin-bottom:8px}.status{font-weight:650;color:var(--blue)}.empty{padding:16px;color:var(--muted)}.contribution-note{font-size:13px;color:var(--muted);padding-top:16px}
@media(max-width:900px){.wrap{padding:0 24px}.grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.metric:nth-child(2){border-right:0}.metric:nth-child(-n+2){border-bottom:1px solid var(--line)}nav{gap:14px}.audit{grid-template-columns:1fr}.chart text{font-size:16px}.panel{padding:22px}.section-head{align-items:start}}
@media(max-width:600px){.wrap{padding:0 16px}.masthead{align-items:start;padding-top:18px;padding-bottom:16px;flex-direction:column;gap:16px}nav{font-size:12px;flex-wrap:wrap}.intro{padding-top:28px}h1{letter-spacing:-1px}.issuebar{align-items:start;flex-direction:column;gap:12px}.lede{font-size:16px}.metric{padding:18px 14px}.value{font-size:27px}.pair{grid-template-columns:1fr;gap:16px}.panel{padding:18px}.section-head{flex-direction:column;gap:8px}h2{font-size:23px}.foot{flex-direction:column;gap:8px}.chart text{font-size:19px}.component .chart text{font-size:19px}.driver-chart text{font-size:18px}.driver-chart{min-width:510px}.driver-wrap{overflow:auto}}
@media print{body{background:white}.wrap{max-width:none;padding:0}.top nav,.rangebar{display:none}.panel,.metrics{break-inside:avoid}section{margin:24px 0}details{display:block}.foot{padding-bottom:0}a{color:inherit}.intro{padding-top:20px}h1{font-size:38px}}
.chart text{font-size:16px}.chart{min-width:580px}.scroll-area{overflow-x:auto;max-width:100%}.scroll-area:focus-visible{outline:3px solid #b97819;outline-offset:3px}.scroll-hint{font-size:13px;font-weight:600;color:var(--blue);background:var(--soft);padding:8px 10px;margin:8px 0;border-left:3px solid var(--blue)}.scroll-hint:before{content:"↔";margin-right:8px}@media(max-width:600px){.chart text{font-size:20px}.chart{min-width:580px}.driver-chart{min-width:550px}}@media print{.chart{min-width:0}.scroll-hint{display:none!important}.scroll-area{overflow:visible}}
"""


SCRIPT = """
const scrollAreas = Array.from(document.querySelectorAll(".scroll-area"), (area, index) => {
    const hint = document.createElement("p");
    hint.id = "scroll-hint-" + (index + 1);
    hint.className = "scroll-hint";
    hint.hidden = true;
    hint.textContent = "Scroll horizontally to see the full " + area.dataset.scrollKind + ".";
    area.before(hint);
    return {area, hint};
});
function updateScrollHints() {
    scrollAreas.forEach(({area, hint}) => {
        const overflows = area.clientWidth > 0 && area.scrollWidth > area.clientWidth + 1;
        hint.hidden = !overflows;
        area.tabIndex = overflows ? 0 : -1;
        if (overflows) area.setAttribute("aria-describedby", hint.id);
        else area.removeAttribute("aria-describedby");
    });
}
document.querySelectorAll("[data-range]").forEach(button => button.addEventListener("click", () => {
    document.querySelectorAll("[data-range]").forEach(b => b.setAttribute("aria-pressed", String(b === button)));
    document.querySelectorAll("[data-range-panel]").forEach(p => p.hidden = p.dataset.rangePanel !== button.dataset.range);
    updateScrollHints();
}));
document.querySelectorAll("details").forEach(details => details.addEventListener("toggle", updateScrollHints));
window.addEventListener("resize", updateScrollHints);
updateScrollHints();
"""


def render(payload):
    p, latest, method = payload, payload["latest"], payload["methodology"]
    synthetic = p["kind"] == "synthetic"
    four = p["windows"]["4"]
    badge = "Synthetic demonstration" if synthetic else "Official public data · saved snapshot"
    pieces = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; img-src data:; base-uri \'none\'; form-action \'none\'"><meta name="description" content="Two executable US liquidity research recipes with inspectable sources, calculations, and snapshot changes."><title>Open Macro Lab · {esc(latest["date"])} · {"Synthetic demo" if synthetic else "Research snapshot"}</title><style>{CSS}</style></head><body><a class="skip" href="#reading">Skip to research</a>',
              '<header class="top"><div class="wrap masthead"><div class="brand"><span class="mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span><div><strong>Open Macro Lab</strong><small>Executable research · provisional name</small></div></div><nav aria-label="Report navigation"><a href="#reading">Reading</a><a href="#drivers">Drivers</a><a href="#recipes">Recipes</a><a href="#changes">Changes</a><a href="#evidence">Evidence</a></nav></div></header><main class="wrap">',
              f'<div class="intro"><div class="issuebar"><span class="eyebrow">Research note 001 / United States</span><span class="badge {"demo" if synthetic else ""}">{badge}</span></div><h1>What changed in the Fed’s<br>balance sheet?</h1><p class="lede">A decomposable US liquidity proxy, checked against actual reserve balances. Two small recipes, with an inspectable path from source to conclusion.</p><p class="meta">Observation: <strong>{esc(latest["date"])}</strong> · Captured: {esc(p["captured_at"])} · Methodology {esc(method["version"])} · All displayed amounts in USD billions</p></div>']
    if synthetic:
        pieces.append('<div class="notice"><strong>SYNTHETIC DATA — not a market reading.</strong><p>The numbers, capture times, and revisions in this example were deliberately invented to demonstrate reproducibility and change attribution. They do not describe actual official revisions.</p></div>')
    if p["warnings"]:
        pieces.append('<div class="notice"><strong>Data quality notes</strong><ul>' + ''.join('<li>'+esc(w)+'</li>' for w in p["warnings"]) + '</ul></div>')
    metrics = [("Selected liquidity proxy", latest["liquidity"], False, "Assets − Treasury account − total reverse repos"),
               ("Four-week proxy change", four["liquidity"] if four else None, True, (four["start"] + " → " + four["end"]) if four else "Exact endpoint unavailable"),
               ("Observed reserve balances", latest["reserves"], False, "Wednesday levels · WRBWFRBL"),
               ("Proxy–reserve gap", latest["gap"], False, "Other balance-sheet items remain in the proxy")]
    pieces.append('<div class="metrics">' + ''.join(f'<div class="metric"><div class="metric-label">{esc(label)}</div><div class="value">{number(value,signed)}</div><div class="unit">USD bn</div><small>{esc(note)}</small></div>' for label,value,signed,note in metrics) + '</div>')
    pieces.append('<section id="reading"><div class="section-head"><div><div class="section-num">01 / Current reading</div><h2>Selected liquidity and reserve balances</h2></div><span class="small">Current-vintage history · no historical backtest</span></div><div class="grid"><div class="panel"><div class="legend"><span>Selected liquidity proxy</span><span class="reserve">Observed reserves</span></div><div class="rangebar" aria-label="History range"><button type="button" data-range="13" aria-pressed="false">13 weeks</button><button type="button" data-range="52" aria-pressed="true">52 weeks</button><button type="button" data-range="all" aria-pressed="false">All history</button></div>')
    for n in ("13", "52", "all"):
        rows = p["rows"] if n == "all" else p["rows"][-int(n):]
        pieces.append(f'<div data-range-panel="{n}" {"hidden" if n != "52" else ""}>' + chart(rows, [("liquidity", "Proxy", "#245c87", ""), ("reserves", "Reserves", "#9a6424", "7 5")], "Selected liquidity and reserves") + f'<p class="chart-note">{len(rows)} weekly observations · {esc(rows[0]["date"])} to {esc(rows[-1]["date"])} · USD bn · zero-based level scale</p></div>')
    pieces.append(f'</div><aside class="panel blue"><div class="eyebrow">Interpretation</div><h3 style="margin-top:12px">Read the components before the headline.</h3><p>{esc(p["interpretation"])}</p><p class="small">The subtraction is accounting, not a causal model. The proxy is neither global liquidity nor a measure of investable money.</p></aside></div></section>')
    pieces.append('<section id="drivers"><div class="section-head"><div><div class="section-num">02 / Accounting drivers</div><h2>Where the change came from</h2></div><span class="small">Calendar endpoint differences · same snapshot vintage</span></div><div class="grid"><div class="panel"><h3>Four-week contribution to the proxy</h3><div class="driver-wrap">' + driver_chart(four, method) + '</div><p class="contribution-note">An increase in assets adds to the proxy. An increase in the Treasury account or total reverse repos subtracts from it. Contributions sum exactly to the proxy change.</p></div><div class="panel"><h3>How to read this</h3><p>Treasury cash accumulation and reverse-repo balances occupy liability-side space. Holding other items fixed, their decline raises this proxy.</p><p class="small">Actual reserves can move differently as currency, other deposits, liabilities, and capital change. The second recipe measures that difference; it does not explain each omitted line.</p></div></div><div class="panel" style="margin-top:24px">'+scroll_open('Changes over 1, 4, and 13 weeks', 'table')+'<table><caption>Changes in USD bn. Four-week means exactly 28 days, not four surviving observations.</caption><thead><tr><th>Input / derived result</th><th class="num">1 week</th><th class="num">4 weeks</th><th class="num">13 weeks</th></tr></thead><tbody>')
    for s in method["series"]:
        pieces.append('<tr><td>'+esc(method["series"][s]["label"])+ ' · Δ input</td>' + ''.join('<td class="num">'+number(p["windows"][n]["input_deltas"][s] if p["windows"][n] else None,True)+'</td>' for n in ("1","4","13"))+'</tr>')
    for k,label in (("liquidity","Selected liquidity · Δ result"),("reserves","Reserves · Δ result"),("gap","Proxy–reserve gap · Δ result")):
        pieces.append('<tr><td><strong>'+label+'</strong></td>'+''.join('<td class="num">'+number(p["windows"][n][k] if p["windows"][n] else None,True)+'</td>' for n in ("1","4","13"))+'</tr>')
    pieces.append('</tbody></table></div><p class="chart-note">'+ ' · '.join(esc(n+'w: '+(p["windows"][n]["start"]+' → '+p["windows"][n]["end"] if p["windows"][n] else 'unavailable')) for n in ("1","4","13")) + '</p></div><details><summary>Inspect component histories · most recent 52 weeks</summary><div class="pair">')
    for s in method["series"]:
        rows = [{"date": r["date"], "value": str(Decimal(r["inputs"][s])/1000) if r["inputs"][s] is not None else None} for r in p["rows"][-52:]]
        pieces.append(f'<div class="panel component"><h3>{esc(method["series"][s]["label"])} · {s}</h3><div class="current">{number(Decimal(latest["inputs"][s])/1000)} <span class="unit">USD bn</span></div>'+chart(rows,[("value",s,"#245c87","")],method["series"][s]["label"],height=240)+'<p class="chart-note">Zero-based, independent panel scale. Compare exact values, not line slopes between panels.</p></div>')
    pieces.append('</div></details></section>')
    pieces.append('<section id="recipes"><div class="section-head"><div><div class="section-num">03 / Executable recipe notebook</div><h2>Two recipes. Explicit limits.</h2></div><a href="methodology.json" download>Download method JSON</a></div><div class="pair"><article class="panel"><div class="recipe-number">Recipe 01 / Selected balance-sheet liquidity</div><h3>Decompose a narrow US liquidity proxy</h3><div class="formula">'+esc(method["recipes"]["liquidity"]["formula"])+'</div><p class="definition">WALCL is consolidated Fed assets; WDTGAL is the Treasury general account; WLRRAL is <strong>total</strong> reverse-repo liabilities, including foreign official and international accounts. Each is millions of USD; divide by 1,000 once.</p><p class="definition">This definition intentionally differs from the common formula using only overnight reverse repos. It preserves one source, one observation basis, and a clear accounting perimeter.</p></article><article class="panel"><div class="recipe-number">Recipe 02 / Reserve cross-check</div><h3>Test the proxy against observed reserves</h3><div class="formula">'+esc(method["recipes"]["reserves"]["formula"])+'<br>'+esc(method["recipes"]["gap"]["formula"])+'</div><p class="definition">WRBWFRBL is the Wednesday reserve-balance level. G is the difference between the selected proxy and reserves. Its movement quantifies how much the proxy and actual reserves diverged.</p><p class="definition">The residual includes other liabilities and capital. It is not a statistical error and is not itself a measure of monetary accommodation. The weekly-average series WRESBAL is deliberately excluded.</p></article></div><details><summary>Alignment, dates, uncertainty, and economic limitations</summary><div class="panel"><p>All inputs must be USD millions, unadjusted, weekly Wednesday levels. We join on the exact observation date and retain absent weeks as missing. We never fill a holiday, copy a later value backward, or treat a missing value as zero.</p><p>A date in the CSV is the observation date. Historical publication timestamps are unknown in this release. Retrieval times and HTTP dates are capture evidence only. Charts use the latest values in the selected snapshot, including any revisions already present.</p><ul>'+''.join('<li class="definition">'+esc(v)+'</li>' for v in method["limitations"])+'</ul></div></details></section>')
    pieces.append('<details><summary>Inspect executed coefficients · output in USD billions</summary>'+scroll_open('Executed recipe coefficients', 'table')+'<table><caption>These saved coefficients are the executable definition. Each coefficient multiplies the native input, then the sum is divided by 1,000. Formula text is explanatory.</caption><thead><tr><th>Output</th>'+''.join('<th class="num">'+s+'</th>' for s in method['series'])+'</tr></thead><tbody>'+''.join('<tr><td>'+esc(method['recipes'][k]['name'])+'</td>'+''.join('<td class="num">'+esc(method['recipes'][k]['coefficients'].get(s,'0'))+'</td>' for s in method['series'])+'</tr>' for k in ('liquidity','reserves','gap'))+'</tbody></table></div></details>')
    c = p["comparison"]
    pieces.append('<section id="changes"><div class="section-head"><div><div class="section-num">04 / Why the reading changed</div><h2>Changes between saved snapshots</h2></div><span class="badge '+('demo' if synthetic else '')+'">'+('Synthetic revision example' if synthetic else 'Archive evidence')+'</span></div><div class="panel"><p>'+esc(c["message"])+'</p>')
    if c["status"] == "compared":
        pieces.append('<p class="meta">Prior capture: '+esc(c["previous_captured_at"])+ ' · '+esc(c["previous_id"])+'<br>Method: '+esc(c["previous_methodology_version"])+' → '+esc(method["version"])+(' · methodology changed' if c["methodology_changed"] else ' · unchanged')+'</p>')
        pieces.append(scroll_open('Detected observation changes', 'table')+'<table><caption>Classification counts are source-series/date cells, not independent economic releases.</caption><thead><tr><th>Detected change</th><th class="num">Cells</th></tr></thead><tbody>'+''.join('<tr><td>'+esc(k.replace('_',' '))+'</td><td class="num">'+str(v)+'</td></tr>' for k,v in c["counts"].items())+('</tbody></table></div>' if c["counts"] else '<tr><td>No parsed observation changes</td><td class="num">0</td></tr></tbody></table></div>'))
        if c["bridge"]:
            bridge=c["bridge"]
            pieces.append('<h3 style="margin-top:24px">Exact bridge for the headline</h3><p class="small">'+esc(bridge["old_date"])+' → '+esc(bridge["new_date"])+'. Apply prior-date data changes, then move the endpoint, then apply the new methodology. Order matters when both data and method change.</p>'+scroll_open('Headline change attribution', 'table')+'<table><thead><tr><th>Result · USD bn</th><th class="num">Before</th><th class="num">Prior data</th><th class="num">New endpoint</th><th class="num">Method</th><th class="num">After</th></tr></thead><tbody>')
            for k,label in (("liquidity","Selected liquidity"),("reserves","Reserves"),("gap","Gap")):
                b=bridge["recipes"][k]
                pieces.append('<tr><td>'+label+'</td>'+''.join('<td class="num">'+number(b[field],field not in ('before','after'))+'</td>' for field in ('before','prior_data_effect','new_observation_effect','methodology_effect','after'))+'</tr>')
            pieces.append('</tbody></table></div><p class="chart-note">Revisions elsewhere in history can leave this headline bridge at zero. The cell log below preserves those changes too.</p>')
        else:
            pieces.append('<p class="small">Bridge unavailable: comparable complete endpoints and consistent retrieval coverage are required. No effect has been invented.</p>')
        pieces.append('<details><summary>Inspect every changed observation ('+str(len(c["events"]))+')</summary>'+scroll_open('Changed observation ledger', 'table')+'<table><thead><tr><th>Series</th><th>Observation</th><th>Classification</th><th class="num">Before · USD m</th><th class="num">After · USD m</th></tr></thead><tbody>'+''.join('<tr><td>'+esc(e["series"])+'</td><td>'+esc(e["date"])+'</td><td>'+esc(e["kind"].replace('_',' '))+'</td><td class="num">'+number(e["before"])+'</td><td class="num">'+number(e["after"])+'</td></tr>' for e in c["events"])+'</tbody></table></div></details>')
    else:
        pieces.append('<p class="small">Capture again and pass <code>--previous</code> to detect newly observed dates, revised prior values, filled or removed observations, and versioned methodology changes. Weekly endpoint changes above are not revision evidence.</p>')
    pieces.append('</div></section>')
    pieces.append('<section id="evidence"><div class="section-head"><div><div class="section-num">05 / Evidence and reproducibility</div><h2>Inspect the publication</h2></div><a href="report.json" download>Full research payload ↗</a></div><div class="audit">')
    for label,key in (("Calculation confidence","arithmetic"),("Economic confidence","economic"),("Availability confidence","temporal")):
        pieces.append('<div class="panel"><h3>'+label+'</h3><p>'+esc(p["confidence"][key])+'</p></div>')
    pieces.append('</div><div class="panel" style="margin-top:24px"><h3>Input ledger</h3><p class="small">Age is measured against '+esc(p["as_of"])+'. Latest complete observation age: '+str(p["observation_age_days"])+ (' day' if p["observation_age_days"] == 1 else ' days')+'. Status: '+esc(p["status"].replace('_',' '))+'. This saved report does not refresh itself.</p>'+scroll_open('Source input ledger', 'table')+'<table class="sources"><thead><tr><th>Input / original source</th><th>Observation dates</th><th>Capture and publication</th><th>Raw evidence</th></tr></thead><tbody>')
    for source in p["sources"]:
        pieces.append(f'<tr><td><a href="https://fred.stlouisfed.org/series/{esc(source["series"])}">{esc(source["series"])}</a><br>{esc(source["label"])}<br>Board of Governors · H.4.1, via FRED<br><span class="small">USD millions · Wednesday level · NSA</span></td><td>{esc(source["first_observation"])} → {esc(source["last_observation"])}<br>Latest nonmissing: {esc(source["latest_valid_observation"])}<br>{source["observations"]} rows; {source["missing_values"]} explicit missing</td><td>Retrieved {esc(source["retrieved_at"])}<br><strong>Historical publication dates: unknown</strong><br>HTTP date is not a release timestamp.</td><td><a href="{esc(source["evidence_path"])}" download>Original CSV</a><br><span class="hash">SHA-256 {esc(source["sha256"])}</span></td></tr>')
    pieces.append('</tbody></table></div><p class="chart-note">Attribution: Board of Governors of the Federal Reserve System (US), H.4.1 Factors Affecting Reserve Balances; retrieved from FRED, Federal Reserve Bank of St. Louis, at the times above. '+('Synthetic example files are fabricated and are not supplied by these institutions. ' if synthetic else '')+'Selected source series are tagged Public Domain: Citation Requested. No institutional endorsement.</p><details><summary>Snapshot identity and reproducible command</summary><div><p class="hash">Snapshot '+esc(p["snapshot_id"])+'<br>Methodology SHA-256 '+esc(p["methodology_sha256"])+'<br>Engine source SHA-256 '+esc(p["engine_sha256"])+'</p><p><a href="evidence/'+esc(p["snapshot_id"])+'/manifest.json">Snapshot manifest</a> · <a href="history.csv" download>Aligned calculated history CSV</a> · <a href="methodology.json">Effective methodology</a></p><p class="small">With the package installed, run from this report directory. Without installation, follow the project README with python3 -m open_macro_lab from the project root.</p><div class="code">open-macro-lab report --snapshot evidence/'+esc(p["snapshot_id"])+(' --previous evidence/'+esc(c["previous_id"]) if c["status"]=='compared' else '')+' --methodology methodology.json --as-of '+esc(p["as_of"])+' --output reproduced</div></div></details><details><summary>Complete calculated observation table ('+str(len(p["rows"]))+' weeks)</summary>'+scroll_open('Calculated observation history', 'table')+'<table><thead><tr><th>Wednesday</th><th class="num">Assets</th><th class="num">Treasury</th><th class="num">Reverse repos</th><th class="num">Proxy</th><th class="num">Reserves</th><th class="num">Gap</th></tr></thead><tbody>')
    for r in p["rows"]:
        vals=[str(Decimal(r["inputs"][s])/1000) if r["inputs"][s] is not None else None for s in ("WALCL","WDTGAL","WLRRAL")]+[r[k] for k in ("liquidity","reserves","gap")]
        pieces.append('<tr><td>'+r["date"]+'</td>'+''.join('<td class="num">'+number(v)+'</td>' for v in vals)+'</tr>')
    pieces.append('</tbody></table></div></details></div></section><footer class="foot"><p><strong>Open Macro Lab</strong> · A local, executable research publication.<br>Research and education only. No live trading, investment recommendation, or demonstrated predictive edge. The project’s MIT license covers its code; source-data rights remain separate.</p><p>2 recipes · 4 inputs<br>No accounts · no remote assets</p></footer></main><script>' + SCRIPT + '</script></body></html>')
    return ''.join(pieces)


def write_report(payload, snapshot, previous, output):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    evidence = root / "evidence"
    evidence.mkdir(exist_ok=True)
    for snap in (snapshot, previous):
        if snap:
            destination=evidence / snap.id
            if not destination.exists():
                shutil.copytree(snap.path, destination)
            else:
                from .store import load_snapshot
                if load_snapshot(destination).manifest != snap.manifest:
                    raise ValueError("Existing evidence differs")
    (root / "report.json").write_bytes(canonical(payload))
    (root / "methodology.json").write_bytes(canonical(payload["methodology"]))
    out=io.StringIO()
    writer=csv.writer(out)
    writer.writerow(["observation_date", "kind", "assets_usd_bn", "tga_usd_bn", "total_rrp_usd_bn", "liquidity_usd_bn", "reserves_usd_bn", "gap_usd_bn"])
    for r in payload["rows"]:
        values=[str(Decimal(r["inputs"][s])/1000) if r["inputs"][s] is not None else "" for s in ("WALCL","WDTGAL","WLRRAL")]
        writer.writerow([r["date"],payload["kind"]]+values+[r[k] if r[k] is not None else "" for k in ("liquidity","reserves","gap")])
    (root / "history.csv").write_text(out.getvalue(),encoding="utf-8")
    (root / "index.html").write_text(render(payload),encoding="utf-8")
    return root / "index.html"
