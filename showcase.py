"""
"Why Titan" showcase - Titan's USPs with animated, hand-drawn (SVG) product illustrations.

Everything here is plain HTML/CSS/SVG text that app.py puts on the page with st.markdown.
* Edit the CARDS list to change the products, taglines or facts.
* The drawings are original illustrations (not product photos).
"""

import math

# ---------------------------------------------------------------------------
# CSS: flip cards, stat strip, slimness bars and the small animations
# ---------------------------------------------------------------------------
CSS = """
<style>
@keyframes sc-rot  { to { transform: rotate(360deg); } }
@keyframes sc-rotr { to { transform: rotate(-360deg); } }
@keyframes sc-tw   { 0%,100% { opacity: .15; transform: scale(.55); } 50% { opacity: 1; transform: scale(1.1); } }
@keyframes sc-shine { 0% { transform: translateX(-170px); } 55%,100% { transform: translateX(210px); } }
@keyframes sc-dash { to { stroke-dashoffset: 0; } }
@keyframes sc-float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
@keyframes sc-grow { from { transform: scaleY(0); } to { transform: scaleY(1); } }
@keyframes sc-fadeup { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

.sc-hand  { transform-box: view-box; transform-origin: 100px 78px; animation: sc-rot 60s steps(60) infinite; }
.sc-hand-m { transform-box: view-box; transform-origin: 100px 78px; animation: sc-rot 3600s linear infinite; }
.sc-gear  { transform-box: fill-box; transform-origin: center; animation: sc-rot 9s linear infinite; }
.sc-gear.rev  { animation-name: sc-rotr; animation-duration: 5.5s; }
.sc-gear.fast { animation-duration: 3.5s; }
.sc-tw    { transform-box: fill-box; transform-origin: center; animation: sc-tw 2.4s ease-in-out infinite; }
.sc-tw.d2 { animation-delay: .8s; } .sc-tw.d3 { animation-delay: 1.6s; }
.sc-shine { animation: sc-shine 3.6s ease-in-out infinite; }
.sc-ecg   { stroke-dasharray: 140; stroke-dashoffset: 140; animation: sc-dash 2.4s linear infinite; }
.sc-float { animation: sc-float 4.2s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .sc-hand, .sc-hand-m, .sc-gear, .sc-tw, .sc-shine, .sc-ecg, .sc-float, .slab { animation: none !important; }
}

.sc-hero { padding: 22px 24px; border-radius: 18px; margin-bottom: 14px;
           background: radial-gradient(700px 240px at 0% 0%, rgba(212,175,55,.14), transparent 70%),
                       linear-gradient(135deg, rgba(255,255,255,.03), rgba(255,255,255,.01));
           border: 1px solid rgba(212,175,55,.22); }
.sc-hero h2 { margin: 0; font-size: 2rem; color: #F6EBCD; }
.sc-hero p { color: #CFC6B6; margin: 6px 0 0 0; font-size: .95rem; max-width: 900px; }

.stat-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 4px 0 18px 0; }
.stat { padding: 14px 16px; border-radius: 14px; background: rgba(212,175,55,.06); border: 1px solid rgba(212,175,55,.18);
        animation: sc-fadeup .7s ease both; }
.stat:nth-child(2) { animation-delay: .1s; } .stat:nth-child(3) { animation-delay: .2s; }
.stat:nth-child(4) { animation-delay: .3s; } .stat:nth-child(5) { animation-delay: .4s; }
.stat .s-big { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 2.1rem; color: #F1DFA6; font-weight: 700; line-height: 1; }
.stat .s-txt { color: #CFC6B6; font-size: .82rem; margin-top: 6px; line-height: 1.4; }
.stat .s-src { color: #857C6E; font-size: .68rem; margin-top: 4px; }

.flip-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(225px, 1fr)); gap: 14px; }
.flip { perspective: 1200px; height: 350px; outline: none; cursor: pointer; }
.flip-inner { position: relative; width: 100%; height: 100%; transition: transform .8s cubic-bezier(.2,.75,.25,1);
              transform-style: preserve-3d; }
.flip:hover .flip-inner, .flip:focus .flip-inner, .flip:focus-within .flip-inner { transform: rotateY(180deg); }
.face { position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden;
        border-radius: 18px; padding: 16px 18px; display: flex; flex-direction: column;
        border: 1px solid rgba(212,175,55,.22); overflow: hidden; }
.face.front { align-items: center; text-align: center; justify-content: space-between;
              background: radial-gradient(260px 200px at 50% 38%, rgba(212,175,55,.13), transparent 70%),
                          linear-gradient(170deg, #1B1711, #110E0A); }
.face.back { transform: rotateY(180deg); background: linear-gradient(160deg, #201B13, #120F0B); overflow-y: auto; }
.face svg { width: 100%; max-width: 230px; height: 168px; }
.f-tag { font-size: .66rem; letter-spacing: .18em; text-transform: uppercase; color: #C9B37A; font-weight: 700; }
.f-title { font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.4rem; color: #F6EBCD; font-weight: 700; line-height: 1.1; }
.f-line { color: #B9B0A0; font-size: .84rem; }
.f-hint { color: #857C6E; font-size: .68rem; letter-spacing: .06em; }
.face.back ul { margin: 8px 0 0 0; padding-left: 18px; }
.face.back li { color: #DCD3C3; font-size: .82rem; line-height: 1.45; margin-bottom: 5px; }
.face.back .b-src { margin-top: auto; color: #857C6E; font-size: .68rem; }

.slim-wrap { padding: 18px 20px; border-radius: 16px; background: rgba(255,255,255,.025); border: 1px solid rgba(237,230,216,.08); }
.slim-row { display: grid; grid-template-columns: 190px 1fr 80px; align-items: end; gap: 14px; margin: 10px 0; }
.slim-row .lbl { color: #EDE6D8; font-size: .88rem; font-weight: 600; text-align: right; padding-bottom: 2px; }
.slim-row .lbl span { display: block; color: #857C6E; font-weight: 400; font-size: .72rem; }
.slab { width: min(100%, 300px); border-radius: 4px; transform-origin: bottom; animation: sc-grow 1.1s cubic-bezier(.2,.8,.2,1) both;
        transition: filter .2s, transform .2s; }
.slab:hover { filter: brightness(1.25); }
.slim-row .mm { color: #F6EBCD; font-weight: 700; font-variant-numeric: tabular-nums; padding-bottom: 2px; }
.slim-note { color: #A99D86; font-size: .8rem; margin-top: 8px; }
.dyk { position: relative; height: 190px; padding: 18px 20px; border-radius: 16px; overflow: hidden;
       background: radial-gradient(400px 160px at 100% 0%, rgba(57,135,229,.10), transparent 70%), rgba(255,255,255,.025);
       border: 1px solid rgba(237,230,216,.08); }
.dyk .d-head { font-size: .7rem; letter-spacing: .18em; text-transform: uppercase; color: #C9B37A; font-weight: 700; }
.dyk .d-items { position: absolute; inset: 46px 20px 14px 20px; }
.dyk .d-item { position: absolute; inset: 0; opacity: 0; animation: sc-dyk 25s infinite; color: #EDE6D8;
               font-family: 'Cormorant Garamond', Georgia, serif; font-size: 1.45rem; line-height: 1.3; }
.dyk .d-item span { display: block; font-family: 'Inter', sans-serif; font-size: .74rem; color: #857C6E; margin-top: 6px; }
.dyk .d-item:nth-child(2) { animation-delay: 5s; } .dyk .d-item:nth-child(3) { animation-delay: 10s; }
.dyk .d-item:nth-child(4) { animation-delay: 15s; } .dyk .d-item:nth-child(5) { animation-delay: 20s; }
@keyframes sc-dyk { 0% { opacity: 0; transform: translateY(10px); } 3%, 17% { opacity: 1; transform: none; }
                    20%, 100% { opacity: 0; transform: translateY(-10px); } }
@media (max-width: 640px) { .slim-row { grid-template-columns: 120px 1fr 60px; } }
</style>
"""


# ---------------------------------------------------------------------------
# little SVG helpers
# ---------------------------------------------------------------------------
def _gear(cx, cy, r, teeth, depth=4.5):
    """path of a gear with `teeth` teeth"""
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        rr = r if (i % 4) in (0, 1) else r - depth
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


def _ticks(cx, cy, r1, r2, color="#E9CF85", width=1.4, n=12):
    out = []
    for i in range(n):
        a = math.radians(i * 360 / n)
        out.append(f'<line x1="{cx + r1 * math.sin(a):.1f}" y1="{cy - r1 * math.cos(a):.1f}" '
                   f'x2="{cx + r2 * math.sin(a):.1f}" y2="{cy - r2 * math.cos(a):.1f}" '
                   f'stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')
    return "".join(out)


def _spark(x, y, s=6, cls="sc-tw", color="#FFF4D0"):
    return (f'<path class="{cls}" d="M{x},{y - s} L{x + s * .28},{y - s * .28} L{x + s},{y} L{x + s * .28},{y + s * .28} '
            f'L{x},{y + s} L{x - s * .28},{y + s * .28} L{x - s},{y} L{x - s * .28},{y - s * .28} Z" fill="{color}"/>')


# ---------------------------------------------------------------------------
# the drawings (all original illustrations)
# ---------------------------------------------------------------------------
def svg_edge():
    return f"""<svg viewBox="0 0 200 160" role="img" aria-label="Ultra-slim watch illustration">
<defs><linearGradient id="e-bz" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F4E2A8"/><stop offset=".5" stop-color="#B8862B"/><stop offset="1" stop-color="#6E4F17"/></linearGradient>
<radialGradient id="e-dl" cx=".45" cy=".35" r=".8"><stop offset="0" stop-color="#2D3540"/><stop offset="1" stop-color="#0D1014"/></radialGradient></defs>
<rect x="88" y="2" width="24" height="26" rx="5" fill="#3A2C1A"/><rect x="88" y="128" width="24" height="30" rx="5" fill="#3A2C1A"/>
<circle cx="100" cy="78" r="52" fill="url(#e-bz)"/><circle cx="100" cy="78" r="49.5" fill="url(#e-dl)"/>
{_ticks(100, 78, 41, 46, "#D9E1EA", 1.2)}
<text x="100" y="62" text-anchor="middle" font-family="Inter,sans-serif" font-size="7" letter-spacing="3" fill="#C9D3DD">EDGE</text>
<g class="sc-hand-m"><line x1="100" y1="80" x2="100" y2="40" stroke="#EEF2F6" stroke-width="1.6" stroke-linecap="round"/></g>
<line x1="100" y1="80" x2="124" y2="66" stroke="#EEF2F6" stroke-width="2.2" stroke-linecap="round"/>
<g class="sc-hand"><line x1="100" y1="86" x2="100" y2="34" stroke="#D4AF37" stroke-width=".8"/></g>
<circle cx="100" cy="78" r="2.2" fill="#D4AF37"/>
<g transform="translate(150,128)"><rect x="0" y="0" width="44" height="3.5" rx="1.5" fill="#D4AF37"/>
<text x="22" y="-4" text-anchor="middle" font-family="Inter,sans-serif" font-size="7" fill="#E9CF85">3.5 mm</text></g>
</svg>"""


def svg_ceramic():
    links = "".join(f'<rect x="78" y="{y}" width="44" height="10" rx="3" fill="url(#c-lk)" stroke="#C9C9C9" stroke-width=".4"/>'
                    for y in list(range(-4, 26, 11)) + list(range(130, 168, 11)))
    return f"""<svg viewBox="0 0 200 160" role="img" aria-label="White ceramic watch illustration">
<defs><linearGradient id="c-lk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#CFCFCF"/><stop offset=".5" stop-color="#FFFFFF"/><stop offset="1" stop-color="#D6D6D6"/></linearGradient>
<radialGradient id="c-cs" cx=".4" cy=".3" r=".8"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".7" stop-color="#E7E7E7"/><stop offset="1" stop-color="#BDBDBD"/></radialGradient>
<linearGradient id="c-sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="c-clip"><circle cx="100" cy="78" r="50"/></clipPath></defs>
{links}
<circle cx="100" cy="78" r="50" fill="url(#c-cs)"/><circle cx="100" cy="78" r="41" fill="#F7F7F5" stroke="#D8D8D8"/>
{_ticks(100, 78, 34, 39, "#9C9C9C", 1.3)}
<line x1="100" y1="78" x2="100" y2="47" stroke="#2B2B2B" stroke-width="1.8" stroke-linecap="round"/>
<line x1="100" y1="78" x2="120" y2="88" stroke="#2B2B2B" stroke-width="2.4" stroke-linecap="round"/>
<g class="sc-hand"><line x1="100" y1="84" x2="100" y2="42" stroke="#B8862B" stroke-width=".8"/></g>
<circle cx="100" cy="78" r="2" fill="#2B2B2B"/>
<g clip-path="url(#c-clip)"><rect class="sc-shine" x="40" y="20" width="26" height="120" fill="url(#c-sh)" transform="rotate(20 100 78)"/></g>
</svg>"""


def svg_mechanical():
    return f"""<svg viewBox="0 0 200 160" role="img" aria-label="Skeleton mechanical watch with moving gears">
<defs><linearGradient id="m-bz" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E6E9EE"/><stop offset=".5" stop-color="#8E98A5"/><stop offset="1" stop-color="#4A525D"/></linearGradient></defs>
<rect x="88" y="2" width="24" height="26" rx="5" fill="#2A2621"/><rect x="88" y="128" width="24" height="30" rx="5" fill="#2A2621"/>
<circle cx="100" cy="78" r="53" fill="url(#m-bz)"/><circle cx="100" cy="78" r="48" fill="#0E0C0A"/>
<path class="sc-gear" d="{_gear(82, 66, 20, 14)}" fill="#C8972F" opacity=".95"/>
<circle cx="82" cy="66" r="6" fill="#0E0C0A"/>
<path class="sc-gear rev" d="{_gear(116, 84, 15, 11, 3.6)}" fill="#D9C08A" opacity=".9"/>
<circle cx="116" cy="84" r="4" fill="#0E0C0A"/>
<path class="sc-gear fast" d="{_gear(92, 100, 9, 8, 3)}" fill="#9AA4B1"/>
<circle cx="120" cy="56" r="8" fill="none" stroke="#C8972F" stroke-width="1.2"/>
<circle cx="120" cy="56" r="2" fill="#E6C66F"/>
{_ticks(100, 78, 42, 46, "#E6E9EE", 1.1)}
<line x1="100" y1="78" x2="100" y2="38" stroke="#F3F3F3" stroke-width="1.5" stroke-linecap="round"/>
<line x1="100" y1="78" x2="78" y2="92" stroke="#F3F3F3" stroke-width="2" stroke-linecap="round"/>
<circle cx="100" cy="78" r="2.2" fill="#D4AF37"/>
<text x="150" y="150" text-anchor="middle" font-family="Inter,sans-serif" font-size="7" fill="#C9B37A">2.2 mm movement</text>
</svg>"""


def svg_raga():
    # a pearl bracelet seen at an angle, with a small rose-gold watch at the front
    pearls = []
    for i in range(36):
        a = math.radians(i * 10)
        x, y = 100 + 70 * math.cos(a), 96 + 34 * math.sin(a)
        if y > 110 and abs(x - 100) < 26:     # hidden behind the watch head
            continue
        r = 3.2 + 1.6 * (y - 62) / 68          # pearls at the back look smaller
        pearls.append((y, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="url(#r-pr)"/>'))
    back = "".join(c for y, c in sorted(pearls) if y <= 96)
    front = "".join(c for y, c in sorted(pearls) if y > 96)
    return f"""<svg viewBox="0 0 200 160" role="img" aria-label="Women's watch with pearl bracelet">
<defs><radialGradient id="r-pr" cx=".35" cy=".3" r=".7"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".6" stop-color="#F1E6D6"/><stop offset="1" stop-color="#C9B79E"/></radialGradient>
<linearGradient id="r-rg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F6D5C3"/><stop offset=".5" stop-color="#C98B6B"/><stop offset="1" stop-color="#8A5440"/></linearGradient>
<radialGradient id="r-dl" cx=".4" cy=".35" r=".8"><stop offset="0" stop-color="#FBF4EE"/><stop offset="1" stop-color="#DCC9B9"/></radialGradient></defs>
<g class="sc-float">{back}{front}
<ellipse cx="100" cy="122" rx="27" ry="29" fill="url(#r-rg)"/><ellipse cx="100" cy="122" rx="22.5" ry="24.5" fill="url(#r-dl)"/>
{_ticks(100, 122, 17, 21, "#8A5440", 1, 12)}
<line x1="100" y1="122" x2="100" y2="105" stroke="#5B3628" stroke-width="1.4" stroke-linecap="round"/>
<line x1="100" y1="122" x2="111" y2="127" stroke="#5B3628" stroke-width="1.8" stroke-linecap="round"/>
<circle cx="100" cy="122" r="1.6" fill="#8A5440"/>
{_spark(132, 98, 5)}{_spark(64, 76, 4, "sc-tw d2")}{_spark(150, 70, 3.5, "sc-tw d3")}</g>
</svg>"""


def svg_tanishq():
    beads = []
    for i in range(21):
        t = i / 20
        x = 30 + 140 * t
        y = 20 + 70 * math.sin(math.pi * t)
        beads.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3.2 + 1.6 * math.sin(math.pi * t):.1f}" fill="url(#t-gd)"/>')
    return f"""<svg viewBox="0 0 200 160" role="img" aria-label="Gold necklace with gem pendant">
<defs><radialGradient id="t-gd" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#FFF0B8"/><stop offset=".55" stop-color="#D4A437"/><stop offset="1" stop-color="#8A6418"/></radialGradient>
<linearGradient id="t-gem" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF8FA3"/><stop offset=".5" stop-color="#C2183C"/><stop offset="1" stop-color="#6E0B22"/></linearGradient></defs>
<path d="M30,20 Q100,150 170,20" fill="none" stroke="#B8862B" stroke-width="1.2" opacity=".7"/>
{''.join(beads)}
<g class="sc-float"><path d="M100,92 L114,108 L100,140 L86,108 Z" fill="url(#t-gd)"/>
<path d="M100,99 L109,109 L100,131 L91,109 Z" fill="url(#t-gem)"/>
<path d="M100,99 L109,109 L100,113 Z" fill="#FFFFFF" opacity=".35"/></g>
{_spark(122, 104, 6)}{_spark(64, 64, 4.5, "sc-tw d2")}{_spark(142, 52, 4, "sc-tw d3")}
</svg>"""


def svg_ring():
    return f"""<svg viewBox="0 0 200 160" role="img" aria-label="Diamond ring">
<defs><linearGradient id="d-bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFF0B8"/><stop offset=".5" stop-color="#C8972F"/><stop offset="1" stop-color="#6E4F17"/></linearGradient>
<linearGradient id="d-st" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".5" stop-color="#CFE7FF"/><stop offset="1" stop-color="#8FB7E8"/></linearGradient></defs>
<g class="sc-float"><ellipse cx="100" cy="112" rx="44" ry="30" fill="none" stroke="url(#d-bd)" stroke-width="9"/>
<path d="M88,82 L94,72 L106,72 L112,82 Z" fill="url(#d-bd)"/>
<path d="M76,58 L88,44 L112,44 L124,58 L100,84 Z" fill="url(#d-st)" stroke="#E8F3FF" stroke-width=".8"/>
<path d="M76,58 L124,58 M88,44 L94,58 L100,84 M112,44 L106,58 L100,84 M94,58 L100,44 L106,58" stroke="#7FA6D6" stroke-width=".7" fill="none"/></g>
{_spark(132, 40, 7)}{_spark(68, 36, 5, "sc-tw d2")}{_spark(140, 76, 4, "sc-tw d3")}
</svg>"""


def svg_glasses():
    return """<svg viewBox="0 0 200 160" role="img" aria-label="Spectacles">
<defs><linearGradient id="g-ln" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7FB6E8" stop-opacity=".35"/><stop offset="1" stop-color="#1D3A57" stop-opacity=".55"/></linearGradient>
<linearGradient id="g-sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".7"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="g-cl"><rect x="22" y="56" width="66" height="50" rx="16"/><rect x="112" y="56" width="66" height="50" rx="16"/></clipPath></defs>
<g class="sc-float"><path d="M22,66 L6,58 M178,66 L194,58" stroke="#C8972F" stroke-width="4" stroke-linecap="round"/>
<rect x="22" y="56" width="66" height="50" rx="16" fill="url(#g-ln)" stroke="#D4AF37" stroke-width="4.5"/>
<rect x="112" y="56" width="66" height="50" rx="16" fill="url(#g-ln)" stroke="#D4AF37" stroke-width="4.5"/>
<path d="M88,72 Q100,62 112,72" fill="none" stroke="#D4AF37" stroke-width="4"/>
<g clip-path="url(#g-cl)"><rect class="sc-shine" x="10" y="40" width="22" height="90" fill="url(#g-sh)" transform="rotate(25 100 80)"/></g></g>
<circle cx="170" cy="118" r="3" fill="#199E70"/><text x="150" y="134" font-family="Inter,sans-serif" font-size="7" fill="#9FD9C2">smart</text>
</svg>"""


def svg_smart():
    return """<svg viewBox="0 0 200 160" role="img" aria-label="Smartwatch with heart-rate line">
<defs><linearGradient id="s-cs" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4A4F57"/><stop offset="1" stop-color="#16181C"/></linearGradient></defs>
<rect x="80" y="0" width="40" height="30" rx="6" fill="#2B2F36"/><rect x="80" y="128" width="40" height="32" rx="6" fill="#2B2F36"/>
<rect x="56" y="24" width="88" height="108" rx="24" fill="url(#s-cs)" stroke="#6B717B" stroke-width="1.5"/>
<rect x="64" y="32" width="72" height="92" rx="18" fill="#05080B"/>
<rect x="145" y="62" width="5" height="18" rx="2" fill="#6B717B"/>
<text x="100" y="62" text-anchor="middle" font-family="Inter,sans-serif" font-size="17" font-weight="700" fill="#EDE6D8">10:09</text>
<text x="100" y="74" text-anchor="middle" font-family="Inter,sans-serif" font-size="6.5" fill="#857C6E">MON · 26</text>
<path class="sc-ecg" d="M68,98 L82,98 L87,90 L92,106 L98,84 L104,110 L109,98 L132,98" fill="none" stroke="#3987E5" stroke-width="2" stroke-linejoin="round"/>
<text x="100" y="117" text-anchor="middle" font-family="Inter,sans-serif" font-size="7" fill="#9FC3F0">♥ 72 bpm</text>
</svg>"""


# ---------------------------------------------------------------------------
# card data  (title, tag, one-line tagline, drawing, facts, source)
# ---------------------------------------------------------------------------
CARDS = [
    ("Titan Edge", "Watches · since 2002", "3.5 mm of pure engineering", svg_edge,
     ["Launched in May 2002 — only <b>3.5 mm</b> thick and about <b>14 g</b>.",
      "The movement alone is just <b>1.15 mm</b>, battery included.",
      "Billed at launch as the world's slimmest watch — Titan's signature innovation."],
     "Source: Tata Group heritage note on Titan Edge"),
    ("Edge Ceramic", "Watches · ceramic", "The slimmest ceramic watch", svg_ceramic,
     ["Titan calls it the world's slimmest ceramic watch — <b>4.4 mm</b> thin.",
      "<b>Edge Ceramic Fusion</b> blends ceramic and steel into one seamless case (AR FY24).",
      "<b>Fastrack Cerame</b> became Fastrack's first ceramic watch (AR FY24)."],
     "Sources: Titan Company news; Annual Report 2023-24"),
    ("Edge Mechanical", "Watches · made in Hosur", "Mechanical art, ultra-thin", svg_mechanical,
     ["A <b>2.2 mm</b> mechanical movement — one of the slimmest commercially produced.",
      "<b>106</b> precision parts, <b>81</b> of them made in Titan's Hosur factory.",
      "<b>Edge Ultraslim</b> won the iF Design Award and was nominated at the GPHG, Geneva."],
     "Sources: Annual Reports 2022-23 and 2024-25"),
    ("Raga", "Watches · for women", "Where watches meet jewellery", svg_raga,
     ["Titan's women's watch brand, designed to be worn like jewellery.",
      "<b>Raga Power Pearls</b> turned the classic pearl into contemporary watch designs.",
      "<b>Raga Memoir</b>: timepieces inspired by memory and emotion."],
     "Sources: Annual Reports 2023-24 and 2024-25"),
    ("Tanishq", "Jewellery · since 1994", "Purity you can check", svg_tanishq,
     ["India's leading organised jewellery retailer — jewellery is ~90% of Titan's revenue.",
      "The <b>Karatmeter</b> lets customers check gold purity right in the store.",
      "Showcased the <b>Desert Diamonds</b> collection with Rahul Mishra at Paris Couture Week 2026."],
     "Sources: Titan investor presentation; AR 2025-26; Q4 FY26 release"),
    ("CaratLane & beYon", "Jewellery · new age", "Diamonds for a new generation", svg_ring,
     ["<b>CaratLane</b>: online-plus-store jewellery, ~99.99% owned since FY24 (₹4,621 cr buy-out).",
      "<b>beYon</b>: Titan's lab-grown diamond brand, launched in 2025.",
      "<b>Zoya Aeterna</b> won a German Design Award (AR FY25)."],
     "Sources: Annual Reports 2023-24, 2024-25; company releases"),
    ("Titan Eye+ · EyeX", "EyeCare", "Eyewear, made smart", svg_glasses,
     ["<b>Titan Eye+</b> runs ~880 eyewear stores across India and the GCC (Sep 2025).",
      "<b>Titan EyeX</b> smart glasses won two Red Dot Awards (2022) and a German Design Award (2023).",
      "Sunglasses and international brands are driving the latest growth."],
     "Sources: Q2 FY26 business update; Annual Report 2022-23"),
    ("Smart wearables", "Watches · digital", "From analog to smart", svg_smart,
     ["Titan entered India's <b>top 5 smart-watch</b> makers (IDC tracker, Feb 2023).",
      "Fastrack Revoltt and Titan smart watches with calling and fitness tracking.",
      "Honest note: smart-watch sales fell sharply in FY26 while analog watches kept growing."],
     "Sources: Q4 FY23 results release; Q4 FY26 results release"),
]

STATS = [
    ("49 mn", "Encircle loyalty members", "Annual Report 2025-26"),
    ("3,603", "stores in 440+ towns (Mar 2026)", "Annual Report 2025-26"),
    ("~27%", "share of India's analog-watch market", "Annual Report 2025-26"),
    ("50%+", "share in watches priced under ₹25,000", "Annual Report 2025-26"),
    ("~90%", "of revenue from jewellery (FY26)", "Segment note, AR 2025-26"),
]

# thickness comparison (mm) - label, sub-label, mm, colour
SLIM = [
    ("Credit / debit card", "ISO standard thickness", 0.76, "#6B717B"),
    ("Edge Mechanical movement", "the engine only (AR FY23)", 2.2, "#9AA4B1"),
    ("Titan Edge (2002)", "the whole watch", 3.5, "#D4AF37"),
    ("Edge Ceramic", "the whole watch", 4.4, "#F2F2F2"),
    ("Typical everyday watch", "approximate, for comparison", 10.0, "#5B4A2E"),
]

TIMELINE = [
    (1984, "Titan is born", "Joint venture of the Tata Group and TIDCO (Tamil Nadu)."),
    (1987, "First watches", "Watch-making starts at Hosur under the name Titan Watches."),
    (1994, "Tanishq", "Titan enters jewellery with Tanishq."),
    (2002, "Titan Edge", "3.5 mm — billed as the world's slimmest watch."),
    (2016, "CaratLane", "Titan takes a controlling stake in CaratLane."),
    (2017, "Taneira", "Women's ethnic-wear (saree) brand launched."),
    (2022, "Edge Mechanical", "Second generation of the ultra-slim mechanical Edge."),
    (2023, "CaratLane buy-out", "Stake raised to ~99.99% for ₹4,621 cr."),
    (2024, "Geneva stage", "Edge Ultraslim & Squircle nominated at the GPHG; iF Design Award."),
    (2025, "beYon", "Lab-grown diamond brand launched."),
    (2026, "Damas (GCC)", "67% stake in Damas Jewellery; FY26 revenue tops ₹87,500 cr."),
]


def stats_html():
    return '<div class="stat-strip">' + "".join(
        f'<div class="stat"><div class="s-big">{b}</div><div class="s-txt">{t}</div><div class="s-src">{s}</div></div>'
        for b, t, s in STATS) + "</div>"


def cards_html():
    out = []
    for title, tag, line, draw, facts, src in CARDS:
        facts_html = "".join(f"<li>{f}</li>" for f in facts)
        out.append(
            f'<div class="flip" tabindex="0"><div class="flip-inner">'
            f'<div class="face front"><div class="f-tag">{tag}</div>{draw()}'
            f'<div><div class="f-title">{title}</div><div class="f-line">{line}</div>'
            f'<div class="f-hint">↻ hover or tap to flip</div></div></div>'
            f'<div class="face back"><div class="f-tag">{tag}</div><div class="f-title">{title}</div>'
            f'<ul>{facts_html}</ul><div class="b-src">{src}</div></div>'
            f'</div></div>')
    return '<div class="flip-grid">' + "".join(out) + "</div>"


def slim_html(px_per_mm=9):
    rows = []
    for i, (lbl, sub, mm, color) in enumerate(SLIM):
        grad = (f"linear-gradient(180deg, {color}, rgba(0,0,0,.35))" if color != "#F2F2F2"
                else "linear-gradient(180deg, #FFFFFF, #BDBDBD)")
        rows.append(
            f'<div class="slim-row"><div class="lbl">{lbl}<span>{sub}</span></div>'
            f'<div><div class="slab" title="{lbl}: {mm:g} mm" style="height:{mm * px_per_mm:.1f}px;'
            f'background:{grad};animation-delay:{i * 0.12:.2f}s"></div></div>'
            f'<div class="mm">{mm:g} mm</div></div>')
    cards = 3.5 / 0.76
    return (f'<div class="slim-wrap">{"".join(rows)}'
            f'<div class="slim-note">Drawn to scale (side view). The 2002 Titan Edge is about '
            f'<b>{cards:.1f} credit cards</b> thick — roughly a third of an everyday watch.</div></div>')


DID_YOU_KNOW = [
    ("The first Titan Edge's movement was just 1.15 mm thick — battery included.", "Tata Group heritage note"),
    ("81 of the 106 parts in the Edge Mechanical movement are made in Titan's Hosur factory.", "Annual Report 2022-23"),
    ("About 1 in every 4 analog watches sold in India is a Titan Company watch (~27% share).", "Annual Report 2025-26"),
    ("Jewellery brings in roughly 9 of every 10 rupees of Titan's revenue.", "Segment note, FY26"),
    ("49 million people are members of Titan's Encircle loyalty programme.", "Annual Report 2025-26"),
]


def did_you_know_html():
    items = "".join(f'<div class="d-item">{t}<span>Source: {s}</span></div>' for t, s in DID_YOU_KNOW)
    return f'<div class="dyk"><div class="d-head">✦ Did you know?</div><div class="d-items">{items}</div></div>'
