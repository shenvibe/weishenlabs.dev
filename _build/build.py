"""Builds weishenlabs.dev from content.json + shell.html.

Run from the repo root:  python3 _build/build.py
Writes index.html and journal/index.html. Edit content.json to add apps or journal entries.
"""
import datetime, html, json, math, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
C = json.loads((BUILD / "content.json").read_text())
SHELL = (BUILD / "shell.html").read_text()
INK = "#3b2f27"


# ---------- pixel sprites ----------

def sprite(rows, pal, ox=0, oy=0, cls=None):
    """Rows of characters -> SVG rects (horizontal runs merged). '.' is transparent;
    a palette value starting with '.' becomes a CSS class instead of a fill."""
    w = max(len(r) for r in rows)
    out = []
    for y, row in enumerate(rows):
        row = row.ljust(w, ".")
        x = 0
        while x < w:
            c = row[x]
            if c == ".":
                x += 1
                continue
            x2 = x
            while x2 < w and row[x2] == c:
                x2 += 1
            v = pal[c]
            attr = f'class="{v[1:]}"' if v.startswith(".") else f'fill="{v}"'
            out.append(f'<rect x="{ox+x}" y="{oy+y}" width="{x2-x}" height="1" {attr}/>')
            x = x2
    c = f' class="{cls}"' if cls else ""
    return f"<g{c}>" + "".join(out) + "</g>"


def icon(rows, pal, scale=4, cls="sprite"):
    w = max(len(r) for r in rows)
    h = len(rows)
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="{w*scale}" height="{h*scale}" '
            f'shape-rendering="crispEdges" aria-hidden="true">{sprite(rows, pal)}</svg>')


def circle(r, fill, rim, cut=None):
    n = 2 * r + 1
    rows = []
    for y in range(n):
        row = ""
        for x in range(n):
            d = math.hypot(x - r, y - r)
            if d > r + 0.2 or (cut and math.hypot(x - r - cut, y - r + 1) < r - 0.5):
                row += "."
            else:
                row += "r" if d > r - 1.1 else "f"
        rows.append(row)
    return rows, {"f": fill, "r": rim}


CLOUD = ["....WWWW........", "..WWWWWWWW.WWW..", ".WWWWWWWWWWWWWW.", "WWWWWWWWWWWWWWWW", "SWWWWWWWWWWWWWWS", ".SSSSSSSSSSSSSS."]
TREE = ["....LLLL....", "..LLLLLLLL..", ".LLLLLLDLLL.", "LLDLLLLLLLLL", "LLLLLLLLLDLL", "LLLLDLLLLLLL", ".LLLLLLLLLL.", "..LLLLDLLL..", "....LLLL....", ".....TT.....", ".....TT.....", "....TTTT...."]
TREE_PAL = {"L": "#5fa548", "D": "#3f7f3a", "T": "#7a5230"}
BARN = ["......KKKK......", "....KKKKKKKK....", "..KKKKKKKKKKKK..", "KKKKKKKKKKKKKKKK", ".RRRRRRRRRRRRRR.", ".RRWWRRRRRRWWRR.", ".RRWWRRRRRRWWRR.", ".RRRRRDDDDRRRRR.", ".RRRRRDXXDRRRRR.", ".RRRRRDDDDRRRRR."]
BARN_PAL = {"K": "#7a3b2e", "R": "#c8553d", "W": ".win", "D": "#6b3a24", "X": "#8a4a2c"}
SPROUT = ["L...L", "LL.LL", ".LGL.", "..G..", "..G.."]
SPROUT_PAL = {"L": "#8bd25a", "G": "#4f8f3a"}
CHICK = ["...R....", "..WWW...", "..WKWO..", "..WWW...", "WWWWWW..", "WWWWWWW.", ".WWWWW..", "..O.O..."]
CHICK_PAL = {"R": "#e2553f", "W": "#fffaf0", "K": INK, "O": "#f0a030"}
ROBOT = [
    "...YYYY...",
    "..YYYYYY..",
    "YYRRRRRRYY",
    "..GGGGGG..",
    "..GEGGEG..",
    "..GGGGGG..",
    "...GMMG...",
    ".BBBBBBBB.",
    "GBBBLLBBBG",
    "G.BBBBBB.G",
    "..BBBBBB..",
    "..K....K..",
    ".KK....KK.",
]
ROBOT_PAL = {"Y": "#e8c25a", "R": "#c8553d", "G": "#c9ccd1", "E": ".eye", "M": "#8a9099", "B": "#7f97ad", "L": ".chest", "K": INK}
PACKET = [".KKKKKKKKK.", "KPPPPPPPPPK", "KPPPPPPPPPK", "KPPPKKKPPPK", "KPPKPPPKPPK", "KPPPPPPKPPK", "KPPPPPKPPPK", "KPPPPKPPPPK", "KPPPPPPPPPK", "KPPPPKPPPPK", "KPPPPPPPPPK", ".KKKKKKKKK."]
PACKET_COLORS = {"yellow": "#f2c86b", "pink": "#f2a3b3", "blue": "#9ccfee", "green": "#a8dc7e"}
HEART = [".KK.KK.", "KRRKRRK", "KRRRRRK", ".KRRRK.", "..KRK..", "...K..."]
HEART_PAL = {"K": INK, "R": "#e2553f"}
CHEV = ["LD...", ".LD..", "..LD.", "...LD", "..LD.", ".LD..", "LD..."]
CHEV_PAL = {"L": "#8fd14f", "D": "#3f7f3a"}
GRASS = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8" shape-rendering="crispEdges"><rect width="8" height="8" fill="#79b555"/>'
         '<rect width="8" height="2" fill="#8fd14f"/><rect x="1" y="2" width="1" height="1" fill="#8fd14f"/><rect x="5" y="2" width="1" height="2" fill="#8fd14f"/>'
         '<rect x="3" y="5" width="1" height="1" fill="#5f9b44"/><rect x="6" y="6" width="1" height="1" fill="#5f9b44"/></svg>')
GRASS_URI = "data:image/svg+xml," + GRASS.replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace('"', "'")


def hills(base, a1, f1, p1, a2, f2, p2, fill):
    d = "M0 100"
    for x in range(321):
        h = round(base + a1 * math.sin(x / f1 + p1) + a2 * math.sin(x / f2 + p2))
        d += f"V{h}H{x+1}"
    return f'<path d="{d}V100Z" fill="{fill}"/>'


def scene():
    random.seed(7)
    sky = []
    stars = "".join(f'<rect x="{random.randint(0,319)}" y="{random.randint(20,55)}" width="1" height="1"/>' for _ in range(46))
    sky.append(f'<g class="stars" fill="#fff6c8">{stars}</g>')
    sky.append(sprite(*circle(6, "#ffd34d", "#f5b833"), 250, 26, "sun"))
    sky.append(sprite(*circle(5, "#fff3c4", "#e8d9a0", cut=3), 252, 27, "moon"))
    for i, (x, y) in enumerate([(20, 30), (130, 24), (220, 38)]):
        sky.append(f'<g class="cloud c{i+1}">{sprite(CLOUD, {"W": "#ffffff", "S": "#dbe9f5"}, x, y)}</g>')

    land = [hills(56, 6, 23, 0, 4, 9, 1, "#a9d38c"), hills(68, 5, 31, 2, 3, 13, 0, "#86c065")]
    for x, y in [(86, 66), (238, 64), (34, 67)]:
        land.append(sprite(TREE, TREE_PAL, x, y))
    land.append(sprite(BARN, BARN_PAL, 208, 72))
    land.append('<rect x="0" y="80" width="320" height="20" fill="#79b555"/>')
    tufts = "".join(f'<rect x="{x}" y="{y}" width="1" height="1"/><rect x="{x+2}" y="{y}" width="1" height="1"/><rect x="{x+1}" y="{y+1}" width="1" height="1"/>'
                    for x, y in [(random.randint(0, 316), random.randint(82, 97)) for _ in range(60)])
    land.append(f'<g fill="#5f9b44">{tufts}</g>')
    land.append('<rect x="118" y="84" width="80" height="14" fill="#9a6a3c"/>')
    land.append('<g fill="#80552f"><rect x="118" y="88" width="80" height="1"/><rect x="118" y="92" width="80" height="1"/><rect x="118" y="96" width="80" height="1"/></g>')
    for row, y in enumerate([84, 88, 92]):
        for j, x in enumerate(range(122 + (row % 2) * 4, 192, 9)):
            land.append(f'<g class="sway s{(row + j) % 3}">{sprite(SPROUT, SPROUT_PAL, x, y - 1)}</g>')
    fence = ['<g fill="#c9965a"><rect x="104" y="79" width="106" height="1"/><rect x="104" y="82" width="106" height="1"/>']
    for x in range(104, 211, 8):
        fence.append(f'<rect x="{x}" y="77" width="2" height="8"/><rect x="{x}" y="77" width="2" height="1" fill="#e3b679"/>')
    fence.append("</g>")
    land.append("".join(fence))
    land.append(f'<g class="chick"><g class="walk">{sprite(CHICK, CHICK_PAL, 86, 88)}</g></g>')
    land.append(f'<g class="robot"><g class="walk">{sprite(ROBOT, ROBOT_PAL, 140, 86)}</g></g>')
    lights = '<g class="lights"><rect x="211" y="77" width="2" height="2"/><rect x="219" y="77" width="2" height="2"/></g>'
    return (f'<svg class="scene" viewBox="0 0 320 100" preserveAspectRatio="xMidYMax slice" shape-rendering="crispEdges" aria-hidden="true">'
            f'<g class="sky">{"".join(sky)}</g><g class="land">{"".join(land)}</g>{lights}</svg>')


# ---------- page sections ----------

def e(s):
    return html.escape(s, quote=False)


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")


STAGES = {"seed": ("🌰 Seed", ""), "sprout": ("🌱 Sprout", "sprout"), "harvest": ("🌾 Harvest", "live")}
BOOK = ["KKKKKKKKK.", "KBBBBBBBK.", "KBWWWWWBKK", "KBBBBBBBKK", "KBWWWWBBKK", "KBBBBBBBKK", "KBBBBBBBKK", "KKKKKKKKKK", ".KWWWWWWWK", "..KKKKKKKK"]
CUP = ["...W.W.....", "....W.W....", "...W.W.....", "KKKKKKKKK..", "KCCCCCCCKKK", "KCCRRCCCK.K", "KCRRRRCCK.K", "KCCRRCCCKKK", "KCCCCCCCK..", ".KCCCCCK...", "..KKKKK...."]
CUP_PAL = {"K": INK, "C": "#fffaf0", "R": "#e2553f", "W": "#c9b592"}
BOOK_PAL = {"K": INK, "B": "#c8553d", "W": "#f3e2b5"}

PAGES = [  # key, nav label, url, Japanese subtitle
    ("projects", "Projects", "/projects/", "プロジェクト"),
    ("journal", "Journal", "/journal/", "日記"),
    ("tip", "Tip jar", "/tip/", "チップ"),
    ("about", "About", "/about/", "自己紹介"),
]


def entries():
    return sorted(C["journal"], key=lambda j: j["date"], reverse=True)


def page_head(key, title, lede):
    ja = dict((k, j) for k, _, _, j in PAGES)[key]
    return (f'<h1 class="sec page-title"><span class="arrow" aria-hidden="true">▶</span>{title} <span class="ja" lang="ja">{ja}</span></h1>'
            f'<p class="lede">{lede}</p>')


def project_cards():
    cards = []
    for i, a in enumerate(C["projects"], 1):
        label, cls = STAGES[a["stage"]]
        art = icon(PACKET, {"K": INK, "P": PACKET_COLORS.get(a.get("color"), "#f2c86b")}, 5)
        title = e(a["title"])
        if a.get("url"):
            title = f'<a href="{a["url"]}">{title}</a>'
        cards.append(f'''<article class="slot px {cls}">
            <div class="art">{art}</div>
            <div class="meta"><span>No.{i:02d}</span><span class="tag">{label}</span></div>
            <h3>{title}</h3>
            <p>{e(a["text"])}</p>
          </article>''')
    return "\n          ".join(cards)


def journal_list(items):
    rows = "".join(f'<li><time datetime="{j["date"]}">{nice_date(j["date"])}</time><p>{e(j["text"])}</p></li>' for j in items)
    return f'<ol class="log">{rows}</ol>'


def home():
    sun = f'<svg class="hud-sun" viewBox="0 0 7 7" width="14" height="14" shape-rendering="crispEdges" aria-hidden="true">{sprite(*circle(3, "#ffd34d", "#f5b833"))}</svg>'
    moon = f'<svg class="hud-moon" viewBox="0 0 7 7" width="14" height="14" shape-rendering="crispEdges" aria-hidden="true">{sprite(*circle(3, "#fff3c4", "#e8d9a0", cut=2))}</svg>'
    icons = {
        "projects": icon(PACKET, {"K": INK, "P": "#f2c86b"}, 4),
        "journal": icon(BOOK, BOOK_PAL, 4),
        "tip": icon(ROBOT, ROBOT_PAL, 4),
        "about": icon(HEART, HEART_PAL, 5),
    }
    blurbs = {"projects": "What's growing on the farm", "journal": "Little updates, newest first",
              "tip": "Feed the robot farmer ☕", "about": "Who's behind all this"}
    menu = "".join(f'<a class="menu-item px" href="{url}"><span class="mi-art">{icons[k]}</span>'
                   f'<span class="mi-text"><span class="mi-label">{label} <span class="ja" lang="ja">{ja}</span></span>'
                   f'<span class="mi-blurb">{blurbs[k]}</span></span><span class="mi-go" aria-hidden="true">▶</span></a>'
                   for k, label, url, ja in PAGES)
    latest = entries()[0]
    return f'''
      <section class="hero" aria-labelledby="tagline">
        <h1 id="tagline">{e(C["tagline"])}</h1>
        <p class="by">by Wei Shen · fun little projects made with AI</p>
        <div class="screen">
          <div class="view" data-time="day">
            {scene()}
            <div class="hud" aria-label="Wei Shen's local time in Kuala Lumpur">{sun}{moon}<div><div class="z">Wei Shen's time 🇲🇾</div><div class="d">&nbsp;</div><div class="t">&nbsp;</div></div></div>
          </div>
          <div class="dialog px">
            <span class="name">Wei Shen</span>
            <p class="sr-only">{e(" ".join(C["dialog"]))}</p>
            <p class="typed" aria-hidden="true">{e(C["dialog"][0])}</p>
            <span class="more" aria-hidden="true"></span>
          </div>
        </div>
      </section>

      <nav class="menu" aria-label="Explore">{menu}</nav>
      <p class="latest"><span class="new">LIVE</span> My first project: <a href="https://tengoktren.weishenlabs.dev">TengokTren — watch the trains ▶</a></p>
      <p class="latest"><span class="new">NEW</span> <time datetime="{latest["date"]}">{nice_date(latest["date"])}</time> — {e(latest["text"])} <a href="/journal/">Read the journal ▶</a></p>'''


def projects_page():
    return f'''
      <section>
        {page_head("projects", "Projects", "Every project starts as a seed. <span class='stages'>🌰 Seed → 🌱 Sprout → 🌾 Harvest <em>(ready to play!)</em></span>")}
        <div class="slots">
          {project_cards()}
        </div>
      </section>'''


def journal_page():
    return f'''
      <section>
        {page_head("journal", "Farm Journal", "What's been happening on the farm, newest first.")}
        <div class="journal px">{journal_list(entries())}</div>
      </section>'''


def tip_page():
    return f'''
      <section>
        {page_head("tip", "Tip Jar", "Totally optional. Every bit helps the farm keep growing.")}
        <div class="tip">
          <div class="tip-pitch px">
            <div class="bot">{icon(ROBOT, ROBOT_PAL, 8, "robot-big")}</div>
            <div>
              <h2>Feed the robot farmer 🤖</h2>
              <p>Most of these projects get built with Claude and ChatGPT. Tips go to their subscriptions — basically the robot farmer's salary.</p>
              <p class="small">Any amount is great. Even RM1 keeps him watering the crops ☕</p>
            </div>
          </div>
          <div class="pay px">
            <div class="tabs" role="tablist" aria-label="How to tip">
              <button role="tab" id="tab-my" aria-controls="panel-my" aria-selected="true">🇲🇾 Malaysia</button>
              <button role="tab" id="tab-intl" aria-controls="panel-intl" aria-selected="false" tabindex="-1">🌏 International</button>
            </div>
            <div class="tip-pane" id="panel-my" role="tabpanel" aria-labelledby="tab-my">
              <div class="qr-head">Touch 'n Go eWallet · DuitNow QR</div>
              {qr_block()}
              <div class="qr-name">TAN WEI SHEN</div>
              <p class="small">Scan with TNG or any Malaysian banking app.</p>
              <a class="btn" href="/assets/tip-qr.png" download="weishenlabs-tip-qr.png">Save QR image</a>
              <p class="small hint">On your phone? Save it, then use “scan from gallery” in your TNG app.</p>
            </div>
            <div class="tip-pane" id="panel-intl" role="tabpanel" aria-labelledby="tab-intl">
              <div class="qr-head kofi-head">Ko-fi · from anywhere</div>
              <div class="cup">{icon(CUP, CUP_PAL, 8, "sprite")}</div>
              <p>Buy the robot farmer a coffee on Ko-fi.</p>
              <p class="small">Pay with card, Apple Pay or Google Pay — no account needed.</p>
              <a class="btn" href="{C["kofi"]}" target="_blank" rel="noopener">Tip on Ko-fi ☕</a>
              <p class="small">{C["kofi"].replace("https://", "")}</p>
            </div>
          </div>
        </div>
      </section>'''


def about_page():
    a = C["about"]
    rows = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in a["status"])
    paras = "".join(f"<p>{e(p)}</p>" for p in a["paragraphs"])
    return f'''
      <section>
        {page_head("about", "About Me", "The person (and robot) behind the farm.")}
        <div class="about">
          <div class="status">
            <div class="title">{icon(HEART, HEART_PAL, 3, "heart")}<span>STATUS</span></div>
            <dl>{rows}</dl>
          </div>
          <div class="about-text px">{paras}</div>
        </div>
      </section>'''


QR_CSS = 0


def qr_block():
    if not QR_CSS:
        return '<div class="qr-missing">QR coming soon</div>'
    return f'<img class="qr" src="/assets/tip-qr.png" width="{QR_CSS}" height="{QR_CSS}" alt="DuitNow QR code for tipping Wei Shen">'


def nav(active):
    return "".join(f'<a href="{url}"' + (' aria-current="page"' if k == active else "") + f">{label}</a>" for k, label, url, _ in PAGES)


def render(title, description, body, out, active=None):
    page = (SHELL.replace("{{TITLE}}", title).replace("{{DESCRIPTION}}", description)
            .replace("{{CHEV}}", icon(CHEV, CHEV_PAL, 4, "chev")).replace("{{GRASS}}", GRASS_URI)
            .replace("{{NAV}}", nav(active)).replace("{{BODY}}", body)
            .replace("{{DIALOG}}", json.dumps(C["dialog"], ensure_ascii=False)))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print("wrote", out.relative_to(ROOT), f"{len(page)//1024} KB")


if __name__ == "__main__":
    qr_path = ROOT / "assets" / "tip-qr.png"
    if qr_path.exists():
        from PIL import Image
        QR_CSS = Image.open(qr_path).width // 2
    render("weishenlabs", "A tiny farm of fun little projects by Wei Shen, made with AI tools.", home(), ROOT / "index.html")
    render("Projects · weishenlabs", "Fun little projects growing on the weishenlabs farm.", projects_page(), ROOT / "projects" / "index.html", "projects")
    render("Farm Journal · weishenlabs", "What's been happening on the weishenlabs farm.", journal_page(), ROOT / "journal" / "index.html", "journal")
    render("Tip Jar · weishenlabs", "Tip the robot farmer behind weishenlabs via TNG / DuitNow.", tip_page(), ROOT / "tip" / "index.html", "tip")
    render("About · weishenlabs", "About Wei Shen — accounting & finance grad who got hooked on AI.", about_page(), ROOT / "about" / "index.html", "about")
