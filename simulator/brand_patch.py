"""Apply FALAJ branding to a COPY of simulator_template.html.
Every change is an exact, asserted string replacement so it can be audited and ported.
Usage: python brand_patch.py <in_template> <mark_png> <favicon_png> <out_template>"""
import sys, base64, pathlib

src, mark_png, fav_png, out = sys.argv[1:5]
t = pathlib.Path(src).read_text(encoding="utf-8")
MARK = "data:image/png;base64," + base64.b64encode(pathlib.Path(mark_png).read_bytes()).decode()
FAV = "data:image/png;base64," + base64.b64encode(pathlib.Path(fav_png).read_bytes()).decode()

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, f"expected {count} x {old[:70]!r}, found {n}"
    t = t.replace(old, new)

# ---- [B1] <head>: title, favicon, fonts -------------------------------------------------
rep('<title>AERIVA Simulator</title>',
    '<title>FALAJ | فلج</title>\n<meta name="description" content="FALAJ | فلج: See demand before it lands. Hotel-demand simulator for Abu Dhabi.">\n'
    '<link rel="icon" type="image/png" href="' + FAV + '">')
rep('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">',
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Noto+Kufi+Arabic:wght@500;700&display=swap">')

# ---- [B2] colour + font tokens (:root, dark media query, [data-theme=dark]) ---------------
rep("""  --bg:#f3f1ea; --sf:#fffdf8; --sf2:#ebe8de; --ink:#16212b; --mut:#5d6872; --ln:#d9d5c8;
  --a:#2456c8; --a2:#dbe5fb; --b:#0a8272; --b2:#d3eee9; --am:#a8650a; --am2:#f7e8cc;
  --ok:#1b7a3d; --ok2:#d7efdd; --wn:#b3261e; --wn2:#f8dad7; --glow:#2456c8;
  --serif:'Fraunces',Georgia,'Times New Roman',serif; --sans:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',sans-serif; --mono:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;""",
"""  /* FALAJ brand palette (sampled from the logo files) */
  --oasis:#013429; --oasis-2:#0A4A3A; --oasis-3:#12634E; --oasis-ink:#022F27;
  --gold:#E3B25A; --gold-hi:#F8D47D; --gold-lo:#C3903C; --gold-txt:#8A6418; --teal:#0F7C88; --ivory:#F6F1E4;
  /* UI tokens */
  --bg:#F4F2EB; --sf:#FFFEFB; --sf2:#EEECE3; --ink:#0F2A22; --mut:#56675F; --ln:#DCD8CB;
  --a:#0F7C88; --a2:#DCEFF0; --b:#B08227; --b2:#F6ECD4; --am:#B85E0B; --am2:#FBE7D2;
  --ok:#1E7F45; --ok2:#DCEFE2; --wn:#B3261E; --wn2:#F8DAD7; --glow:#0F7C88; --kick:#8A6418;
  --shadow:0 1px 2px rgba(15,42,34,.05),0 10px 28px -20px rgba(15,42,34,.30);
  --serif:'Outfit','Plus Jakarta Sans','Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif;
  --sans:'Plus Jakarta Sans','Outfit','Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;
  --arab:'Noto Kufi Arabic','Segoe UI','Geeza Pro','Tahoma','Arial',sans-serif;""")
dark_old = """  --bg:#0e151c; --sf:#16202a; --sf2:#1d2935; --ink:#e8edf1; --mut:#97a4af; --ln:#2b3946;
  --a:#7ea6ff; --a2:#1c2c52; --b:#4fd1bd; --b2:#10332f; --am:#f0b45a; --am2:#3a2b10;
  --ok:#5fd18a; --ok2:#12341f; --wn:#ff8a80; --wn2:#3e1916; --glow:#7ea6ff; color-scheme:dark}"""
dark_new = """  --bg:#07150F; --sf:#0E211B; --sf2:#152D25; --ink:#E9F0EC; --mut:#9CB2A8; --ln:#24403A;
  --a:#56C6D2; --a2:#123A3E; --b:#E9C46A; --b2:#3A2E12; --am:#F0A85A; --am2:#3A2610;
  --ok:#5FD18A; --ok2:#12341F; --wn:#FF8A80; --wn2:#3E1916; --glow:#56C6D2; --kick:#E9C46A;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 12px 30px -20px rgba(0,0,0,.6); color-scheme:dark}"""
rep(dark_old, dark_new, count=2)

# ---- [B3] header markup -------------------------------------------------------------------
rep('    <div class="brand">AERIVA<small>Hotel-demand simulator · Abu Dhabi</small></div>',
    '    <div class="brand"><img id="fmark" class="fmark" src="' + MARK + '" alt="FALAJ mark" width="38" height="36">'
    '<span class="fwm"><span class="fwl"><span class="fwn">FALAJ</span><span class="fsep" aria-hidden="true"></span><span class="far" lang="ar" dir="rtl">فلج</span></span>'
    '<small><span class="ftg">See demand before it lands.</span><span class="fds"> · Hotel-demand simulator · Abu Dhabi</span></small></span></div>')

# ---- [B4] Market Radar brand band (markup only) -----------------------------------------
rep("""  <section class="pg" id="p0" aria-label="Market Radar"><div class="in">
    <p class="kick r" style="--i:0">Screen 1 · Market Radar</p>""",
"""  <section class="pg" id="p0" aria-label="Market Radar"><div class="in">
    <div class="fband r" style="--i:0"><div class="fb-l"><p class="fb-k">FALAJ <span lang="ar" dir="rtl" class="far">فلج</span> · UAE-born commercial intelligence</p><p class="fb-h">Connecting arrivals to opportunity</p><p class="fb-s">From aviation signals to sustainable destination growth.</p></div>
      <div class="fb-r"><p class="fb-t">See demand before it lands.</p><p class="fb-p">People, places, possibilities connected.</p></div>
      <svg class="fb-ch" viewBox="0 0 220 120" aria-hidden="true"><path d="M20 4v112" stroke="currentColor" stroke-width="10" fill="none"/><path d="M25 18c6 22 26 30 50 30h110M25 46c6 22 26 30 50 30h135M25 74c6 22 26 30 50 30h95" stroke="currentColor" stroke-width="7" fill="none" stroke-linecap="round"/><circle cx="196" cy="104" r="7" fill="currentColor"/></svg></div>
    <p class="kick r" style="--i:0">Screen 1 · Market Radar</p>""")

# ---- [B5] footer credit line -------------------------------------------------------------
rep('<span>No room rates</span></div></footer>',
    '<span>No room rates</span><span class="fcred"><span class="fcm" aria-hidden="true"></span><b>FALAJ</b> <span lang="ar" dir="rtl" class="far">فلج</span> · UAE-born commercial intelligence · See demand before it lands.</span></div></footer>')

# ---- [B6] FALAJ style layer (appended at the end of the <style> block) -------------------
CSS = r"""
/* ================= FALAJ brand layer (presentation only) ================= */
body{font-size:14.5px;letter-spacing:.003em}
.mono,.tile .v,.kpi .v,.dg .v,.hero,.dv-big,.dv-mid{font-variant-numeric:tabular-nums}
#blob{opacity:.08}
/* header: full-bleed oasis bar */
#top{position:relative;padding:10px 16px;gap:14px 18px;color:var(--ivory)}
#top::before{content:"";position:absolute;top:0;bottom:0;left:calc(50% - 50vw);right:calc(50% - 50vw);z-index:-1;
  background:radial-gradient(120% 180% at 0% 0%,#0B4A3A 0,var(--oasis) 55%,#01261E 100%);border-bottom:1px solid rgba(227,178,90,.45)}
.brand{display:flex;align-items:center;gap:11px;font:inherit;letter-spacing:0;color:var(--ivory);min-width:0}
.fmark{width:38px;height:36px;object-fit:contain;flex:none;filter:drop-shadow(0 2px 6px rgba(0,0,0,.35))}
.fwm{display:flex;flex-direction:column;min-width:0}
.fwl{display:flex;align-items:center;gap:10px;line-height:1}
.fwn{font:600 18px/1 var(--serif);letter-spacing:.42em;margin-right:-.42em;color:#fff}
.fsep{width:1px;height:16px;background:rgba(227,178,90,.6)}
.far{font-family:var(--arab);font-weight:700;letter-spacing:0}
.fwl .far{font-size:17px;color:var(--gold-hi);line-height:1;transform:translateY(-1px)}
.brand small{display:block;font:500 10.5px/1.3 var(--sans);color:rgba(246,241,228,.72);letter-spacing:.06em;text-transform:none;margin-top:5px;white-space:normal}
#tabs{background:rgba(255,255,255,.07);box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}
#tabs button{color:rgba(246,241,228,.78);font-weight:600}
#tabs button:hover{color:#fff}
#tabs button.cur{color:var(--oasis-ink)}
#tabs button b{color:inherit}
#pill{background:linear-gradient(180deg,var(--gold-hi),var(--gold));box-shadow:0 4px 14px -6px rgba(227,178,90,.8)}
#top .blk.live{background:rgba(255,255,255,.06)!important;border-color:rgba(227,178,90,.45)!important;border-radius:999px!important;padding:4px 10px!important;font:600 11.5px var(--sans)!important;letter-spacing:.03em}
#top .blk.live .status[style*="--wn"]{color:#F4C7B8!important}
#top .blk.live .status[style*="--ok"]{color:#9BE7B8!important}
#stage{margin-top:0}
.in{padding-top:16px}
/* brand band on Market Radar */
.fband{position:relative;overflow:hidden;display:flex;justify-content:space-between;align-items:flex-end;gap:12px 28px;flex-wrap:wrap;
  background:linear-gradient(115deg,#01261E 0,var(--oasis) 45%,#0B4A3A 100%);color:var(--ivory);border-radius:16px;padding:16px 22px 15px;margin:0 0 16px;
  box-shadow:inset 0 0 0 1px rgba(227,178,90,.22),var(--shadow)}
.fband p{margin:0}
.fb-l,.fb-r{position:relative;z-index:1;min-width:0}
.fb-k{font:600 10.5px var(--sans);letter-spacing:.16em;text-transform:uppercase;color:var(--gold-hi)}
.fb-k .far{font-size:11px;letter-spacing:0}
.fb-h{font:600 clamp(19px,2.5vw,26px)/1.15 var(--serif);letter-spacing:.06em;text-transform:uppercase;margin-top:6px!important;color:#fff;text-wrap:balance}
.fb-s{font-size:13.5px;color:rgba(246,241,228,.8);margin-top:4px!important}
.fb-s::before{content:"";display:block;width:44px;height:2px;background:var(--gold);margin:0 0 8px;border-radius:2px}
.fb-r{text-align:right;padding-right:150px}
.fb-t{font:600 16px var(--serif);color:var(--gold-hi)}
.fb-p{font:600 10px var(--sans);letter-spacing:.2em;text-transform:uppercase;color:rgba(246,241,228,.75);margin-top:5px!important}
.fb-ch{position:absolute;right:16px;top:50%;width:132px;transform:translateY(-50%);color:var(--gold);opacity:.30;z-index:0}
@media(max-width:720px){.fb-r{text-align:left;padding-right:0}.fb-ch{width:96px;top:16px;transform:none;opacity:.18}.fband{padding:14px 16px}}
/* type + headings */
.kick{color:var(--kick);font-weight:600;letter-spacing:.12em}
h2{font:600 clamp(23px,3.1vw,33px)/1.12 var(--serif);letter-spacing:-.005em}
h3{font:700 11px var(--sans);letter-spacing:.09em;color:var(--mut)}
.lede{font-size:14.5px}
/* cards, tiles */
.card{border-radius:14px;box-shadow:var(--shadow);padding:15px 17px}
.card.flat{box-shadow:none}
.tile{border-radius:12px;box-shadow:var(--shadow);position:relative;overflow:hidden;padding:11px 13px 11px 15px}
.tile::before{content:"";position:absolute;left:0;top:10px;bottom:10px;width:3px;border-radius:0 3px 3px 0;background:linear-gradient(var(--gold-hi),var(--gold-lo))}
.tile .k,.kpi .k,.dg .k,.hcell .k,.dv-tile .k{font-weight:600;letter-spacing:.07em}
.kpi{padding-left:12px;border-left:2px solid var(--gold)}
.dg>div,.hcell{border-radius:11px}
/* controls */
.btn{font-weight:600}
.btn:hover{border-color:var(--gold)}
.btn.pri{background:var(--oasis);color:#fff;border-color:var(--oasis)}
.btn.pri:hover{border-color:var(--gold);box-shadow:0 6px 16px -10px rgba(1,52,41,.8)}
.seg button.sel{background:var(--oasis);color:var(--gold-hi)}
.chip:hover{border-color:var(--gold)}
.more{color:var(--a);font-weight:600}
.ctl input:focus,.ctl select:focus,.fld input:focus,.fld select:focus,.news textarea:focus{outline-color:var(--gold)}
/* tables */
table{font-variant-numeric:tabular-nums}
th{font-weight:700;letter-spacing:.07em;border-bottom:1.5px solid var(--ln);background:var(--sf2)}
th:first-child{border-top-left-radius:8px}th:last-child{border-top-right-radius:8px}
tr:hover td{background:color-mix(in srgb,var(--sf2) 55%,transparent)}
tr.me td{background:var(--b2)}
/* radar scope in oasis tones, gold sweep */
:root{--scope:#03201A;--scope2:#0B3A2E;--ring:#2E6152;--ringt:#9CC9B8;--sweep:#E9C46A;--gA:#5FD18A;--gB:#56C6D2;--gC:#F0B45A;--lab:#E6EFEA}
.scope{box-shadow:inset 0 0 0 1px rgba(227,178,90,.18),0 18px 50px -30px rgba(0,0,0,.6)}
.sleg{color:#A9C4BA}
/* decision card (on screen) */
.dv{border-radius:18px;box-shadow:var(--shadow),0 24px 60px -40px rgba(1,52,41,.55)}
.dv-hd{background:linear-gradient(115deg,#01261E 0,var(--oasis) 50%,#0B4A3A 100%);color:var(--ivory);border-bottom:2px solid var(--gold);position:relative;padding-left:82px}
.dv-hd::before{content:"";position:absolute;left:22px;top:50%;width:44px;height:42px;transform:translateY(-50%);background:var(--fmark) center/contain no-repeat;filter:drop-shadow(0 2px 6px rgba(0,0,0,.35))}
.dv-k{color:var(--gold-hi);opacity:1}
.dv-t{font-weight:600;color:#fff}
.dv-g{font-family:var(--serif);box-shadow:0 0 0 3px rgba(255,255,255,.15)}
.dv-hero{border-color:var(--gold)!important}
.dv-ft{background:var(--sf2)}
.dv-ft::after{content:"FALAJ \00B7  See demand before it lands.";float:right;font-weight:600;color:var(--kick);letter-spacing:.04em}
@media(max-width:720px){.dv-hd{padding-left:70px}.dv-hd::before{left:16px;top:20px;transform:none;width:38px;height:36px}.dv-ft::after{float:none;display:block;margin-top:4px}}
/* footer credit */
#lim div{align-items:center}
.fcred{margin-left:auto;color:var(--mut);font-weight:500;letter-spacing:.02em;display:inline-flex;align-items:center;gap:6px}
.fcred b{color:var(--ink)!important;text-transform:none!important;letter-spacing:.3em!important;font-family:var(--serif)}
.fcred .far{color:var(--kick);font-size:11.5px}
.fcm{width:14px;height:13px;background:var(--fmark) center/contain no-repeat;display:inline-block}
@media(max-width:620px){.fcred{margin-left:0}}
@media(max-width:480px){.brand small{font-size:10px}}
/* header layout: status pill sits beside the brand, tabs stay right */
#top{max-width:1400px}
#top .brand{order:0}#top .blk.live{order:1;margin-left:4px!important}#tabs{order:2}
@media(max-width:820px){#top{gap:10px 12px;padding:10px 16px 12px}#top .blk.live{margin-left:auto!important;padding:3px 9px!important;font-size:10.5px!important}
  .fds{display:none}.fwn{font-size:16px;letter-spacing:.36em;margin-right:-.36em}.fmark{width:32px;height:30px}
  .fband{padding:13px 16px;margin-bottom:12px}.fb-ch{display:none}.fb-h{font-size:18px;letter-spacing:.04em}.fb-s{font-size:12.5px}.fb-t{font-size:14px}.fb-r{padding-right:0}
  .fcred{display:none}}
"""
rep("\n</style>", CSS + "</style>")
# mark available to CSS as a custom property (one copy of the image, reused)
rep('<div id="blob"></div>', '<div id="blob"></div>\n<style>:root{--fmark:url("' + MARK + '")}</style>')

# ---- [B7] presentational JS constants ------------------------------------------------------
rep("var BLOB=['#2456c8','#0a8272','#16212b','#a8650a'],BLOBD=['#7ea6ff','#4fd1bd','#97a4af','#f0b45a'];",
    "var BLOB=['#0F7C88','#B08227','#12634E','#B85E0B'],BLOBD=['#56C6D2','#E9C46A','#5FD18A','#F0A85A'];")
rep("var CONF={A:['High confidence','var(--ok)','#1b7a3d'],B:['Medium confidence','var(--a)','#2456c8'],C:['Low confidence','var(--am)','#a8650a']};",
    "var CONF={A:['High confidence','var(--ok)','#1E7F45'],B:['Medium confidence','var(--a)','#0F7C88'],C:['Low confidence','var(--am)','#B85E0B']};")
# visible label that named the old blue colour
rep('<span style="color:var(--a)">Blue</span> = market-level skill', '<span style="color:var(--a)">Teal</span> = market-level skill')

# ---- [B8] Decision Card text + PNG/PDF export --------------------------------------------
rep("return ['AERIVA DECISION CARD',", "return ['FALAJ | فلج · DECISION CARD',")
rep("var P={bg:'#fffdf8',ink:'#16212b',mut:'#5d6872',ln:'#d9d5c8',sf2:'#f0ede4',up:'#1b7a3d',dn:'#b3261e',cc:M.conf[2]}",
    "var P={bg:'#FFFEFB',ink:'#0F2A22',mut:'#56675F',ln:'#DCD8CB',sf2:'#EEECE3',up:'#1E7F45',dn:'#B3261E',cc:M.conf[2]}")
rep("""  s+='<rect width="'+W+'" height="'+H+'" fill="'+P.sf2+'"/><rect x="0" y="0" width="'+W+'" height="120" fill="'+P.ink+'"/>';
  s+=tx(40,44,'AERIVA · DECISION CARD · '+M.scen+' · '+c.grade,16,'#c9d1d8',500)+tx(40,92,M.title,40,'#ffffff',700);""",
"""  s+='<defs><linearGradient id="fhd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#01261E"/><stop offset=".5" stop-color="#013429"/><stop offset="1" stop-color="#0B4A3A"/></linearGradient></defs>';
  s+='<rect width="'+W+'" height="'+H+'" fill="'+P.sf2+'"/><rect x="0" y="0" width="'+W+'" height="120" fill="url(#fhd)"/><rect x="0" y="120" width="'+W+'" height="3" fill="#E3B25A"/>';
  var fm_=document.getElementById('fmark');if(fm_)s+='<image href="'+fm_.src+'" x="34" y="24" width="76" height="72" preserveAspectRatio="xMidYMid meet"/>';
  s+=tx(130,44,'FALAJ · DECISION CARD · '+M.scen+' · '+c.grade,16,'#F8D47D',600)+tx(130,92,M.title,40,'#ffffff',700);""")
rep('height="10" rx="3" fill="#0a8272"/>', 'height="10" rx="3" fill="#B08227"/>')
rep("  s+=tx(40,H-18,'Limits: association, not causation · Abu Dhabi hotels only · occupancy estimated, not measured · no room rates',14,P.mut);",
    "  s+=tx(40,H-18,'Limits: association, not causation · Abu Dhabi hotels only · occupancy estimated, not measured · no room rates',14,P.mut)+tx(W-40,H-18,'FALAJ · See demand before it lands.',14,'#8A6418',700,'end');")
rep("save('AERIVA_Decision_Card.png',b)", "save('FALAJ_Decision_Card.png',b)")
rep("save('AERIVA_Decision_Card.pdf',pdf.output('blob'))", "save('FALAJ_Decision_Card.pdf',pdf.output('blob'))")

pathlib.Path(out).write_text(t, encoding="utf-8")
print("wrote", out, len(t))
