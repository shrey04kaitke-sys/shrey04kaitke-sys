"""Builds assets/activity-graph.svg: an animated line chart of the last 60 days of
real public GitHub contributions. Run by .github/workflows/profile-cards.yml."""
import datetime as dt
import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "shrey04kaitke-sys")
TOKEN = os.environ.get("GH_TOKEN", "")
DAYS = 60
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "activity-graph.svg")


def fetch_counts():
    today = dt.date.today()
    start = today - dt.timedelta(days=DAYS - 1)
    q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
      contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    body = json.dumps({"query": q, "variables": {
        "u": USER,
        "f": start.isoformat() + "T00:00:00Z",
        "t": today.isoformat() + "T23:59:59Z"}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": "bearer " + TOKEN, "Content-Type": "application/json",
        "User-Agent": "profile-activity-graph"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    by_date = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}
    days = [start + dt.timedelta(days=i) for i in range(DAYS)]
    return days, [by_date.get(d.isoformat(), 0) for d in days]


def sample_counts():
    import random
    random.seed(1)
    today = dt.date.today()
    days = [today - dt.timedelta(days=DAYS - 1 - i) for i in range(DAYS)]
    return days, [random.choice([0, 0, 0, 1, 2, 5]) for _ in days]


def nice_max(m):
    for step in (3, 6, 12, 24, 48, 96, 192):
        if m <= step:
            return step
    return int(m) + 1


def build(days, counts):
    W, H = 1000, 380
    x0, x1, yb, yt = 70, 930, 300, 110
    top = nice_max(max(counts))
    n = len(counts)
    pts = []
    for i, c in enumerate(counts):
        x = x0 + (x1 - x0) * i / (n - 1)
        y = yb - (yb - yt) * c / top
        pts.append((x, y))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = d + f" L{x1} {yb} L{x0} {yb} Z"
    total = sum(counts)
    week = sum(counts[-7:])
    grid = ""
    for k in range(4):
        v = round(top * k / 3)
        y = yb - (yb - yt) * k / 3
        grid += (f'<line x1="{x0}" y1="{y:.0f}" x2="{x1}" y2="{y:.0f}" stroke="#94a3b8" stroke-opacity=".16" stroke-dasharray="2 6"/>'
                 f'<text class="ax" x="{x1+14}" y="{y+4:.0f}">{v}</text>')
    xl = ""
    for i in range(0, n, 10):
        x = x0 + (x1 - x0) * i / (n - 1)
        xl += f'<text class="ax" x="{x:.0f}" y="{yb+30}" text-anchor="middle">{days[i].strftime("%b %d")}</text>'
    lx, ly = pts[-1]
    svg = TEMPLATE
    for k, v in {"@W@": W, "@H@": H, "@PATH@": d, "@AREA@": area, "@GRID@": grid, "@XL@": xl,
                 "@TOTAL@": total, "@WEEK@": week, "@LASTX@": f"{lx:.0f}", "@LASTY@": f"{ly:.0f}",
                 "@LASTV@": counts[-1], "@RW@": W - 1, "@RH@": H - 1, "@LIVEX@": W - 92,
                 "@LIVETX@": W - 80}.items():
        svg = svg.replace(k, str(v))
    return svg


TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="@W@" height="@H@" viewBox="0 0 @W@ @H@" role="img" aria-label="Animated chart of my GitHub contributions over the last 60 days">
  <defs>
    <linearGradient id="ln" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset=".5" stop-color="#a78bfa"/><stop offset="1" stop-color="#f472b6"/></linearGradient>
    <linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a78bfa" stop-opacity=".30"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></linearGradient>
    <filter id="gw" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>
    <clipPath id="c"><rect width="@W@" height="@H@" rx="16"/></clipPath>
  </defs>
  <style>
    .t1 { font: 700 18px 'Courier New', Courier, monospace; fill: #e2e8f0; }
    .t2 { font: 500 18px 'Courier New', Courier, monospace; fill: #94a3b8; }
    .big { font: 800 40px 'Segoe UI', Arial, sans-serif; fill: #fbbf24; }
    .up { font: 700 16px 'Courier New', Courier, monospace; fill: #4ade80; }
    .live { font: 700 13px 'Courier New', Courier, monospace; fill: #4ade80; }
    .ax { font: 500 13px 'Courier New', Courier, monospace; fill: #94a3b8; }
    .draw, .glow { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 7s ease-in-out infinite; }
    @keyframes draw { 0% { stroke-dashoffset: 1; } 62% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: 0; } }
    .fill { animation: fillin 7s ease-in-out infinite; }
    @keyframes fillin { 0%,10% { opacity: 0; } 62%,92% { opacity: 1; } 100% { opacity: 0; } }
    .dotm { offset-path: path("@PATH@"); animation: travel 7s ease-in-out infinite; }
    @keyframes travel { 0% { offset-distance: 0%; opacity: 1; } 62% { offset-distance: 100%; opacity: 1; } 92% { offset-distance: 100%; opacity: 1; } 100% { offset-distance: 100%; opacity: 0; } }
    .ping { animation: ping 1.8s ease-out infinite; transform-box: fill-box; transform-origin: center; }
    @keyframes ping { 0% { transform: scale(.6); opacity: .7; } 100% { transform: scale(2.6); opacity: 0; } }
    .blink { animation: bl 1.6s ease-in-out infinite; }
    @keyframes bl { 0%,100% { opacity: 1; } 50% { opacity: .25; } }
    @media (prefers-reduced-motion: reduce) {
      .draw, .glow { animation: none !important; stroke-dashoffset: 0 !important; }
      .fill, .dotm, .ping, .blink { animation: none !important; }
    }
  </style>
  <g clip-path="url(#c)">
    <rect width="@W@" height="@H@" fill="#0b1020"/>
    <rect width="@W@" height="@H@" fill="#12163a" opacity=".55"/>
    <text class="t1" x="34" y="42">$SHREY</text><text class="t2" x="118" y="42">/ CONTRIBUTIONS · 1D · 60D range</text>
    <text class="big" x="34" y="92">@TOTAL@</text><text class="up" x="@TOTAL_X@" y="90">▲ new activity 7d: @WEEK@</text>
    <circle class="blink" cx="@LIVEX@" cy="36" r="4.5" fill="#4ade80"/><text class="live" x="@LIVETX@" y="41">LIVE</text>
    @GRID@
    <path class="fill" d="@AREA@" fill="url(#ar)"/>
    <path d="@PATH@" fill="none" stroke="#94a3b8" stroke-opacity=".22" stroke-width="2.5" stroke-linejoin="round"/>
    <path class="glow" pathLength="1" d="@PATH@" fill="none" stroke="url(#ln)" stroke-width="9" stroke-opacity=".55" stroke-linejoin="round" stroke-linecap="round" filter="url(#gw)"/>
    <path class="draw" pathLength="1" d="@PATH@" fill="none" stroke="url(#ln)" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>
    <g class="dotm"><circle class="ping" r="7" fill="#f472b6"/><circle r="6" fill="#fff"/><circle r="3.4" fill="#f472b6"/></g>
    @XL@
  </g>
  <rect x=".5" y=".5" width="@RW@" height="@RH@" rx="16" fill="none" stroke="#2a2f5c"/>
</svg>
"""


def main():
    if "--sample" in sys.argv:
        days, counts = sample_counts()
    else:
        days, counts = fetch_counts()
    svg = build(days, counts)
    # place the "new activity" label just after the big number
    digits = len(str(sum(counts)))
    svg = svg.replace("@TOTAL_X@", str(34 + 26 * digits + 16))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", os.path.abspath(OUT), "total", sum(counts))


if __name__ == "__main__":
    main()
