#!/usr/bin/env python3
"""الخطوة 7: يبني مشروع HyperFrames (index.html) من moments.json + chunks.json + clip.mp4.
الاستخدام: python3 build_reel.py <work> <project_dir>
- لو مجلد المشروع مش موجود: بيعمله (npx hyperframes init) وبينسخ الخطوط والأصوات والفيديو وthree.js.
- الستايل: Editorial Grain — ورق دافي، حبر، أحمر واحد، حبيبات، كابشن شريط ورق،
  كاميرا بتتحرك طول الفيديو، تلوين للقصة، عنصر صغير كل ~3 ثواني، مجسمات ثري دي، ومشهد خريطة.
- أوضاع الكاميرا: full (وجهك ملء الشاشة) · band (الفيديو بينزل تحت والرسمة فوق) · page (صورة ملصوقة بصفحة مجلة) · map (مشهد ثري دي كامل).
أنواع اللحظات وحقولها: references/moments.md"""
import sys, os, json, glob, shutil, subprocess, html as H

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(HERE)
W, P = sys.argv[1], sys.argv[2]
M = json.load(open(os.path.join(W, 'moments.json'), encoding='utf8'))
C = json.load(open(os.path.join(W, 'chunks.json'), encoding='utf8'))
clip = os.path.join(W, 'clip.mp4')
VDUR = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', clip], capture_output=True, text=True).stdout)
moms = sorted(M.get('moments', []), key=lambda m: m.get('t0', m.get('t', 0)))
end = next((m for m in moms if m['type'] == 'end'), None)
TOTAL = round(max(VDUR, (end['t0'] + M.get('endHold', 1.9)) if end else VDUR), 3)

# ---------- مشروع HyperFrames ----------
if not os.path.exists(os.path.join(P, 'hyperframes.json')):
    import tempfile
    env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS='1')
    tmp = tempfile.mkdtemp(); name = os.path.basename(os.path.abspath(P)) or 'reel'
    r = subprocess.run(['npx', '--yes', 'hyperframes@0.8.122', 'init', name, '--non-interactive', '--resolution', 'portrait'], cwd=tmp, env=env, capture_output=True, text=True)
    if r.returncode: sys.exit('✗ hyperframes init فشل:\n' + (r.stderr or r.stdout)[-800:])
    os.makedirs(P, exist_ok=True)
    for f in os.listdir(os.path.join(tmp, name)):
        s_, d_ = os.path.join(tmp, name, f), os.path.join(P, f)
        if not os.path.exists(d_): shutil.move(s_, d_)
for d in ('fonts', 'sfx'):
    os.makedirs(os.path.join(P, d), exist_ok=True)
for f in glob.glob(os.path.join(SK, 'assets', 'fonts', '*')):
    shutil.copy(f, os.path.join(P, 'fonts'))
for f in glob.glob(os.path.join(SK, 'assets', 'sfx', '*.wav')):
    shutil.copy(f, os.path.join(P, 'sfx'))
for f in ('three.min.js', 'scene3d.js'):
    shutil.copy(os.path.join(SK, 'assets', f), os.path.join(P, f))
dst = os.path.join(P, 'clip.mp4')
if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(clip):
    shutil.copyfile(clip, dst)

# ---------- الخطوط: ثمانية لو موجود، وإلا بدائل مفتوحة ----------
fonts = sorted(os.listdir(os.path.join(P, 'fonts')))
def pick(*keys):
    for f in fonts:
        n = f.lower()
        if all(k in n for k in keys): return f
    return None
ts_r, ts_b = pick('thmanyah', 'sans', 'regular'), pick('thmanyah', 'sans', 'bold')
td_r, td_b = pick('thmanyah', 'serif', 'regular'), pick('thmanyah', 'serif', 'bold')
if ts_b and td_b:
    sans = [(ts_r or ts_b, 400), (ts_b, 700)]; serif = [(td_r or td_b, 400), (td_b, 700)]; fontname = 'ثمانية'
else:
    sans = [('IBMPlexSansArabic-Regular.ttf', 400), ('IBMPlexSansArabic-Bold.ttf', 700)]
    serif = [('Amiri-Regular.ttf', 400), ('Amiri-Bold.ttf', 700)]; fontname = 'IBM Plex Sans Arabic + Amiri'
ff = ''.join(f'@font-face{{font-family:"RSans";src:url(fonts/{f});font-weight:{w};font-display:block}}' for f, w in sans if f)
ff += ''.join(f'@font-face{{font-family:"RSerif";src:url(fonts/{f});font-weight:{w};font-display:block}}' for f, w in serif if f)

th = {'paper': '#efe8dc', 'paper2': '#e4dac8', 'ink': '#1a1a1a', 'red': '#c2412d', 'mut': '#6b6259'}
th.update(M.get('theme', {}))
e = lambda s: H.escape(str(s))
r3 = lambda x: round(float(x), 3)

# ---------- نوافذ الأوضاع ----------
MODE = {'list': 'band', 'ledger': 'band', 'doors': 'band', 'share': 'band', 'people': 'band', 'quote': 'page', 'strike': 'page', 'stack': 'page'}
wins = []
for m in moms:
    md = MODE.get(m['type'])
    if not md: continue
    t1 = m['map']['t0'] if (m['type'] == 'stack' and m.get('map')) else m['t1']
    if wins and wins[-1][2] == md and m['t0'] - wins[-1][1] < 0.05: wins[-1][1] = t1
    else: wins.append([m['t0'], t1, md])
    if m['type'] == 'stack' and m.get('map'): wins.append([m['map']['t0'], m['map']['t1'], 'map'])
wins.sort()
hide = [(a, b) for a, b, _ in wins] + ([(end['t0'] - 0.1, TOTAL + 1)] if end else [])

def inwin(t): return any(a <= t < b for a, b in hide)
caps = []
for c in C:
    s, en = c['s'], c['e']
    if inwin((s + c['w'][-1]['s']) / 2) or inwin(s + 0.05): continue
    for a, b in hide:
        if s < a < en: en = a
    caps.append({'s': r3(s), 'e': r3(en), 'w': c['w']})
for x, y in zip(caps, caps[1:]): x['e'] = r3(min(x['e'], y['s'] - 0.07))

# ---------- الكاميرا ----------
FX, FY = M.get('face', [540, 560])
cam = M.get('camera', 'auto')
KEYS = []
if isinstance(cam, list):
    KEYS = [list(k) for k in cam]
else:
    # تلقائي: حدث كاميرا كل ~2.2-3.5 ث على بداية جملة، بنمط متكرر؛ وداخل الشرائط/الصفحات بنرجع للحجم الطبيعي
    CYC = [('cut', 1.06), ('ease', 1.00), ('cut', 1.10), ('ease', 1.03), ('cut', 1.00), ('whip', 1.06), ('ease', 1.00), ('cut', 1.08), ('ease', 1.00)]
    KEYS.append([0.0, 'cut', 1.0, FX, FY - 40])
    last, j = 0.0, 0
    win_edges = [(a, b) for a, b, _ in wins]
    def near_edge(t): return any(a - 0.5 <= t <= a + 0.3 or b - 0.3 <= t <= b + 0.3 for a, b in win_edges)
    def in_mode(t): return any(a <= t < b for a, b in win_edges)
    for c in C:
        t = c['s']
        if t - last < 2.2 or in_mode(t) or near_edge(t) or t > TOTAL - 1.5: continue
        kind, sc = CYC[j % len(CYC)]; j += 1
        KEYS.append([r3(t), kind, sc, FX, FY - (40 if sc >= 1.08 else 0)]); last = t
    for a, b in win_edges:
        KEYS.append([r3(a), 'ease', 1.0, FX, FY]); KEYS.append([r3(b), 'ease', 1.0, FX, FY])
for m in moms:                       # punch = دفعة زوم على الوجه (بتنضاف لأي كاميرا)
    if m['type'] == 'punch':
        KEYS.append([r3(m['t']), 'ease', m.get('scale', 1.10), FX, FY - 80])
        if m.get('until'): KEYS.append([r3(m['until']), 'ease', 1.0, FX, FY])
KEYS.sort(key=lambda k: k[0])
ded = []
for k in KEYS:
    if ded and k[0] - ded[-1][0] < 0.3: ded[-1] = k
    else: ded.append(k)
KEYS = ded

# ---------- بناء اللحظات ----------
HT, JS, ACC, SFX = [], [], [], list(M.get('sfx', []))
S3D = {'objects': list(M.get('objects', [])), 'crowd': None, 'map': None,
       'paper': int(th['paper'].lstrip('#'), 16), 'red': int(th['red'].lstrip('#'), 16)}
ICON = {'right': 0, 'left': 180, 'up': -90, 'down': 90}
def arrow(deg):
    return f'<svg viewBox="0 0 64 64" style="transform:rotate({deg}deg)"><path d="M8 32h42M36 16l16 16-16 16" stroke="{th["ink"]}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CHECK = f'<svg viewBox="0 0 52 52"><path d="M12 27l9 9 19-20" stroke="{th["paper"]}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CROSS = f'<svg viewBox="0 0 52 52"><path d="M15 15l22 22M37 15L15 37" stroke="{th["paper"]}" stroke-width="7" fill="none" stroke-linecap="round"/></svg>'

for i, m in enumerate(moms):
    k, g = m['type'], f'm{i}'
    if k == 'punch': continue
    if k == 'chapter':
        side = 'right:108px' if m.get('side', 'right') == 'right' else 'left:108px'
        HT.append(f'<div class="chap ar" dir="rtl" id="{g}" style="{side}"><span class="n"><bdi dir="ltr">{e(m.get("n", ""))}</bdi></span><span class="bar"></span><span class="t">{e(m["text"])}</span></div>')
        JS.append(f'chap("#{g}",{m["t0"]},{m["t1"]});'); continue
    if k == 'card':
        sub = m.get('sub', '')
        subh = f'<bdi dir="ltr">{e(sub)}</bdi>' if m.get('subLtr') else e(sub)
        HT.append(f'<div class="card ar" dir="rtl" id="{g}" style="top:{m.get("y", 1090)}px"><div class="a">{e(m["title"])}</div>' + (f'<div class="b">{subh}</div>' if sub else '') + '</div>')
        JS.append(f'tl.fromTo("#{g}",{{y:30,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{m["t0"]});tl.to("#{g}",{{opacity:0,duration:.25}},{m["t1"] - .25});'); continue

    body, js, grp_end = [], [], m.get('t1')
    if k == 'list':
        if m.get('small'): body.append(f'<div class="at sans4" style="top:176px;font-size:36px" id="{g}s">{e(m["small"]["text"])}</div>'); js.append(f'rise("#{g}s",{m["small"]["t"]});')
        if m.get('title'): body.append(f'<div class="at serif" style="top:214px;font-size:96px" id="{g}h">{e(m["title"]["text"])}</div>'); js.append(f'wipe("#{g}h",{m["title"]["t"]},.45);')
        tiles = ''.join(f'<div class="tile" id="{g}t{j}">{arrow(ICON[it["icon"]]) if it.get("icon") in ICON else ""}<span>{e(it["text"])}</span></div>' for j, it in enumerate(m.get('items', [])))
        body.append(f'<div class="tiles" id="{g}T">{tiles}</div>')
        for j, it in enumerate(m.get('items', [])):
            js.append(f'tl.fromTo("#{g}t{j}",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.35,ease:"back.out(1.6)"}},{it["t"] - .06});'); SFX.append({'name': 'tick', 't': it['t'], 'vol': .3})
        if m.get('stamp'):
            st = m['stamp']['t']
            body.append(f'<div class="stampW"><div class="stamp" id="{g}st">{e(m["stamp"]["text"])}</div></div>')
            js.append(f'tl.fromTo("#{g}st",{{scale:1.9,opacity:0,rotation:-6}},{{scale:1,opacity:1,rotation:-6,duration:.24,ease:"power4.out"}},{st - .04});tl.to("#{g}T",{{opacity:.32,duration:.2}},{st});tl.to("#{g}",{{x:7,duration:.05,yoyo:true,repeat:3,ease:"none"}},{st + .18});')
            SFX.append({'name': 'snap', 't': st, 'vol': .35})
    elif k == 'quote':
        y = 196
        if m.get('label'): body.append(f'<div class="at lab" style="top:{y}px" id="{g}l"><i></i>{e(m["label"]["text"])}</div>'); js.append(f'wipe("#{g}l",{m["label"]["t"]},.4);')
        y = 252
        for j, ln in enumerate(m.get('lines', [])):
            sz = ln.get('size', 116 if j == 0 else 80); cls = 'serif' if ln.get('weight', 'bold' if j == 0 else 'regular') == 'bold' else 'serif4'
            if ln.get('words'):
                inner = ' '.join(f'<span class="w" id="{g}w{j}_{q}">{e(w["text"])}</span>' for q, w in enumerate(ln['words']))
                for q, w in enumerate(ln['words']): js.append(f'rise("#{g}w{j}_{q}",{w["t"]});')
            else:
                inner = e(ln['text'])
                if ln.get('mark'): inner += f' <span class="cut" id="{g}c{j}"><b></b>{e(ln["mark"]["text"])}</span>'; js.append(f'tl.from("#{g}c{j} b",{{scaleX:0,transformOrigin:"right center",duration:.35,ease:"power2.out"}},{ln["mark"]["t"]});')
                js.append(f'rise("#{g}q{j}",{ln["t"]});')
            body.append(f'<div class="at {cls}{" red" if ln.get("red") else ""}" style="top:{y}px;font-size:{sz}px" id="{g}q{j}">{inner}</div>')
            y += int(sz * 1.25) + 18
        if m.get('note'): body.append(f'<div class="at sans4" style="top:{max(y, 600)}px;font-size:38px" id="{g}n">{e(m["note"]["text"])}</div>'); js.append(f'rise("#{g}n",{m["note"]["t"]},.45);')
        js.append(f'tl.fromTo("#{g}",{{scale:1}},{{scale:1.035,transformOrigin:"50% 20%",duration:{r3(m["t1"] - m["t0"])},ease:"none"}},{m["t0"]});')
    elif k == 'ledger':
        if m.get('label'): body.append(f'<div class="at lab" style="top:180px" id="{g}l"><i></i>{e(m["label"]["text"])}</div>'); js.append(f'wipe("#{g}l",{m["label"]["t"]},.45);')
        for j, rw in enumerate(m.get('rows', [])[:2]):
            top = 236 + j * 160; ok = rw.get('mark', 'ok') == 'ok'
            sm = rw.get('small')
            body.append(f'<div class="row" style="top:{top}px"><div class="dot {"ok" if ok else "no"}" id="{g}d{j}">{CHECK if ok else CROSS}</div>'
                        f'<div class="serif" style="font-size:110px" id="{g}b{j}">{e(rw["big"]["text"])}</div>'
                        + (f'<div class="{"sans4" if ok else "sans red"}" style="font-size:42px;margin-top:22px" id="{g}s{j}">{e(sm["text"])}</div>' if sm else '') + '</div>')
            js.append(f'tl.from("#{g}d{j}",{{scale:0,duration:.35,ease:"back.out(2)"}},{rw["big"]["t"] - .02});rise("#{g}b{j}",{rw["big"]["t"]},.45);')
            if sm: js.append(f'rise("#{g}s{j}",{sm["t"]},.4);')
            SFX.append({'name': 'tick' if ok else 'snap', 't': rw['big']['t'], 'vol': .3})
            if j == 0 and len(m['rows']) > 1:
                body.append(f'<div class="rule" style="top:388px;opacity:.35" id="{g}r"></div>')
                js.append(f'tl.from("#{g}r",{{scaleX:0,transformOrigin:"right center",duration:.4}},{m["rows"][1]["big"]["t"] - .35});')
    elif k == 'people':
        # شريط فوق: جملة صغيرة، كلمة كبيرة + جنبها صغيرة، وبعدين سطر أحمر بداله — وتحته ناس ثري دي بيبهتوا وبعدين بيصيروا ذهب
        if m.get('small'): body.append(f'<div class="at sans4" style="top:176px;font-size:36px" id="{g}s">{e(m["small"]["text"])}</div>'); js.append(f'rise("#{g}s",{m["small"]["t"]},.45);')
        bg, sd, thn = m.get('big'), m.get('side'), m.get('then')
        body.append(f'<div class="at" style="top:218px;display:flex;align-items:baseline;gap:26px" id="{g}B">'
                    + (f'<span class="serif" style="font-size:84px" id="{g}b">{e(bg["text"])}</span>' if bg else '')
                    + (f'<span class="sans4" style="font-size:40px" id="{g}d">{e(sd["text"])}</span>' if sd else '') + '</div>')
        if bg: js.append(f'rise("#{g}b",{bg["t"]},.4);')
        if sd: js.append(f'rise("#{g}d",{sd["t"]},.4);')
        if thn:
            body.append(f'<div class="at serif red" style="top:218px;font-size:84px;opacity:0" id="{g}t">{e(thn["text"])}</div>')
            js.append(f'tl.to("#{g}B",{{opacity:0,y:-20,duration:.25}},{thn["t"] - .2});tl.fromTo("#{g}t",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.45,ease:"power2.out",immediateRender:false}},{thn["t"]});')
        weak = m.get('weak', (bg['t'] - .07) if bg else m['t0'] + 2)
        rich = m.get('rich', thn['t'] if thn else m['t1'] - 1.1)
        if m.get('crowd', True):
            S3D['crowd'] = {'t0': m['t0'], 't1': m['t1'], 'weak': weak, 'rich': rich}
            SFX.append({'name': 'success', 't': r3(rich + .1), 'vol': .28})
    elif k == 'strike':
        if m.get('ghost'): JS.append(f'ghost("{e(m["ghost"])}",{m["t0"]},{m["t1"]});')
        if m.get('top'): body.append(f'<div class="at serif" style="top:196px;font-size:130px" id="{g}a">{e(m["top"]["text"])}</div>'); js.append(f'rise("#{g}a",{m["top"]["t"]},.4);')
        sk = m['struck']; neg = m.get('neg')
        body.append('<div class="at" style="top:350px;display:flex;align-items:center;gap:28px">' + (f'<span class="sans red" style="font-size:66px" id="{g}m">{e(neg["text"])}</span>' if neg else '') +
                    f'<span class="serif" style="font-size:130px;position:relative" id="{g}b">{e(sk["text"])}<svg viewBox="0 0 600 60" preserveAspectRatio="none" style="position:absolute;left:-14px;width:calc(100% + 28px);top:58px;height:60px;overflow:visible"><path id="{g}p" d="M590 34 C 470 22, 360 44, 250 30 S 70 20, 10 36" stroke="{th["red"]}" stroke-width="13" fill="none" stroke-linecap="round"/></svg></span></div>')
        if neg: js.append(f'rise("#{g}m",{neg["t"]},.3);')
        js.append(f'rise("#{g}b",{sk["t"]},.35);tl.fromTo("#{g}p",{{strokeDasharray:700,strokeDashoffset:700}},{{strokeDashoffset:0,duration:.32,ease:"power2.out"}},{sk["strikeAt"]});tl.to("#{g}b",{{opacity:.45,duration:.3}},{sk["strikeAt"] + .3});')
        SFX.append({'name': 'snap', 't': sk['strikeAt'], 'vol': .35})
        if m.get('bottom'):
            parts = m['bottom']['parts']
            body.append('<div class="at serif4" style="top:556px;font-size:72px">' + ' '.join(f'<span class="w{" red" if p.get("red") else ""}" id="{g}c{q}">{e(p["text"])}</span>' for q, p in enumerate(parts)) + '</div>')
            for q, p in enumerate(parts): js.append((f'wipe("#{g}c{q}",{p["t"]},.45);' if p.get('red') else f'rise("#{g}c{q}",{p["t"]},.35);'))
    elif k == 'doors':
        if m.get('small'): body.append(f'<div class="at sans4" style="top:176px;font-size:36px" id="{g}s">{e(m["small"]["text"])}</div>'); js.append(f'rise("#{g}s",{m["small"]["t"]},.4);')
        rv = m.get('reveal', {'text': '', 't': m['open'] + .6})
        body.append(f'<div class="doors" id="{g}D"><div class="glow" id="{g}g"></div><div class="dtext" id="{g}x">{e(rv["text"])}</div><div class="door l" id="{g}L"><div class="k"></div></div><div class="door r" id="{g}R"><div class="k"></div></div></div>')
        o = m['open']
        js.append(f'tl.from("#{g}D",{{y:30,opacity:0,duration:.45,ease:"power2.out"}},{m["t0"] + .05});tl.to("#{g}L",{{rotationY:-78,duration:.85,ease:"power2.inOut"}},{o});tl.to("#{g}R",{{rotationY:78,duration:.85,ease:"power2.inOut"}},{o});'
                  f'tl.to("#{g}g",{{opacity:1,duration:.7}},{o + .18});tl.to("#{g}x",{{opacity:1,duration:.45}},{rv["t"]});tl.fromTo("#{g}x",{{scale:.9}},{{scale:1,duration:1.2,ease:"power2.out"}},{rv["t"]});')
        SFX.append({'name': 'star', 't': rv['t'], 'vol': .3})
        th2 = m.get('then')
        if th2:
            js.append(f'tl.to(["#{g}D","#{g}s"],{{opacity:0,y:-24,duration:.3,ease:"power2.in"}},{th2["t"]});')
            body.append(f'<div class="at serif" style="top:196px;font-size:88px;opacity:0" id="{g}T">{e(th2["title"]["text"])}</div>')
            js.append(f'tl.to("#{g}T",{{opacity:1,duration:.01}},{th2["title"]["t"]});wipe("#{g}T",{th2["title"]["t"]},.55);')
            row = '<div class="row" style="top:350px;opacity:0" id="%sW">' % g
            if th2.get('switch'): row += f'<div class="sw" id="{g}w"><i id="{g}k"></i></div>'
            if th2.get('word'): row += f'<div class="serif" style="font-size:88px" id="{g}o">{e(th2["word"]["text"])}</div>'
            if th2.get('stamp'): row += f'<div class="sans red" style="font-size:56px;margin-top:14px" id="{g}z">{e(th2["stamp"]["text"])}</div>'
            body.append(row + '</div>')
            t_row = min([x for x in [th2.get('switch', {}).get('t'), th2.get('word', {}).get('t')] if x is not None] or [th2['title']['t'] + .6])
            js.append(f'tl.to("#{g}W",{{opacity:1,duration:.01}},{t_row});')
            if th2.get('switch'):
                sw = th2['switch']; js.append(f'tl.from("#{g}w",{{scale:0,duration:.35,ease:"back.out(2)"}},{sw["t"]});tl.to("#{g}k",{{x:94,duration:.18,ease:"power2.inOut"}},{sw["off"]});tl.to("#{g}w",{{backgroundColor:"#cdc3b1",duration:.18}},{sw["off"]});')
                SFX.append({'name': 'switch', 't': sw['off'], 'vol': .35})
            if th2.get('word'): js.append(f'rise("#{g}o",{th2["word"]["t"]},.35);')
            if th2.get('stamp'): js.append(f'tl.fromTo("#{g}z",{{scale:1.6,opacity:0}},{{scale:1,opacity:1,duration:.22,ease:"power4.out"}},{th2["stamp"]["t"]});')
    elif k == 'stack':
        mp = m.get('map')
        a_end = mp['t0'] if mp else m.get('swap', m['t1'])
        if m.get('ghost'): JS.append(f'ghost("{e(m["ghost"])}",{m["t0"]},{r3(a_end - .3 if mp else a_end)});')
        A = m.get('a', {}); y = 192
        body.append(f'<div id="{g}A">')
        if A.get('label'): body.append(f'<div class="at sans4" style="top:{y}px;font-size:38px" id="{g}al">{e(A["label"]["text"])}</div>'); js.append(f'rise("#{g}al",{A["label"]["t"]},.4);'); y += 46
        for j, ln in enumerate(A.get('lines', [])):
            sz = ln.get('size', 114)
            body.append(f'<div class="at serif{" red" if ln.get("red") else ""}" style="top:{y}px;font-size:{sz}px" id="{g}a{j}">{e(ln["text"])}</div>')
            js.append((f'wipe("#{g}a{j}",{ln["t"]},.55);' if ln.get('wipe') else f'rise("#{g}a{j}",{ln["t"]});')); y += int(sz * 1.25)
        body.append('</div>')
        if mp:
            grp_end = mp['t0']
            S3D['map'] = {'t0': mp['t0'], 'dive': mp['dive'], 't1': mp['t1']}
            # واجهة فوق الخريطة: سطر صغير، شرائح بتطلع على الكلمات، وبعدين السؤال بالأحمر
            ui = [f'<section id="{g}M" class="grp mapUI ar" dir="rtl" style="z-index:12"><div class="fade"></div>']
            ujs = [f'grp("#{g}M",{r3(mp["t0"] + .05)},{r3(mp["t1"] - .05)});']
            if mp.get('label'): ui.append(f'<div class="at sans4" style="top:150px;font-size:38px;color:#4d463f" id="{g}ml">{e(mp["label"]["text"])}</div>'); ujs.append(f'tl.fromTo("#{g}ml",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.4}},{mp["label"]["t"]});')
            chips = mp.get('chips', [])
            if chips:
                ui.append('<div class="chips" id="%sC">' % g + ''.join(f'<div class="chip" id="{g}k{j}" style="transform:rotate({[-2, 1.5, -1.5, 2][j % 4]}deg){";background:" + th["red"] if j == len(chips) - 1 and len(chips) > 1 else ""}">{e(c["text"])}</div>' for j, c in enumerate(chips)) + '</div>')
                for j, c in enumerate(chips):
                    ujs.append(f'tl.fromTo("#{g}k{j}",{{scale:.4,opacity:0}},{{scale:1,opacity:1,rotation:{[-2, 1.5, -1.5, 2][j % 4]},duration:.38,ease:"back.out(2.2)"}},{c["t"]});')
            lines = mp.get('lines', [])
            if lines and (mp.get('label') or chips):
                ujs.append(f'tl.to(["#{g}ml","#{g}C"],{{opacity:0,y:-16,duration:.3}},{r3(lines[0]["t"] - .18)});')
            yy = 360
            for j, ln in enumerate(lines):
                sz = ln.get('size', 104)
                ui.append(f'<div class="at serif red" style="top:{yy}px;font-size:{sz}px" id="{g}q{j}">{e(ln["text"])}</div>')
                ujs.append(f'rise("#{g}q{j}",{ln["t"]},.45);'); yy += int(sz * 1.35)
            ui.append('</section>')
            HT.append(''.join(ui)); JS.append(''.join(ujs))
            JS.append(f'tl.fromTo("#flash",{{opacity:0}},{{opacity:.95,duration:.12,ease:"power2.in",immediateRender:false}},{r3(mp["dive"] - .12)});tl.to("#flash",{{opacity:0,duration:.3,ease:"power2.out"}},{r3(mp["dive"] + .02)});')
            SFX.append({'name': 'fill', 't': r3(mp['dive'] + .04), 'vol': .22}); SFX.append({'name': 'pop', 't': r3(mp.get('money', mp['dive'] + .67) + .05), 'vol': .25})
        else:
            B = m.get('b')
            if B:
                sw = m['swap']; js.append(f'tl.to("#{g}A",{{opacity:0,y:-24,duration:.3,ease:"power2.in"}},{sw});tl.to("#{g}B",{{opacity:1,duration:.01}},{sw + .3});')
                body.append(f'<div id="{g}B" style="opacity:0">')
                if B.get('label'): body.append(f'<div class="at sans4" style="top:192px;font-size:38px" id="{g}bl">{e(B["label"]["text"])}</div>'); js.append(f'rise("#{g}bl",{B["label"]["t"]},.4);')
                if B.get('chips'):
                    body.append('<div class="chips">' + ''.join(f'<div class="chip" id="{g}k{j}" style="transform:rotate({[-2, 1.5, -1.5, 2][j % 4]}deg)">{e(c["text"])}</div>' for j, c in enumerate(B['chips'])) + '</div>')
                    for j, c in enumerate(B['chips']): js.append(f'tl.from("#{g}k{j}",{{scale:.4,opacity:0,duration:.38,ease:"back.out(2.2)"}},{c["t"]});'); SFX.append({'name': 'pop', 't': c['t'], 'vol': .25})
                y = 410
                for j, ln in enumerate(B.get('lines', [])):
                    sz = ln.get('size', 100)
                    body.append(f'<div class="at serif{" red" if ln.get("red") else ""}" style="top:{y}px;font-size:{sz}px" id="{g}b{j}">{e(ln["text"])}</div>')
                    js.append(f'rise("#{g}b{j}",{ln["t"]},.45);'); y += int(sz * 1.35)
                body.append('</div>')
    elif k == 'share':
        if m.get('title'): body.append(f'<div class="at serif" style="top:186px;font-size:96px" id="{g}a">{e(m["title"]["text"])}</div>'); js.append(f'wipe("#{g}a",{m["title"]["t"]},.5);')
        rr, sm = m.get('red'), m.get('small')
        body.append('<div class="at" style="top:318px;display:flex;align-items:center;gap:26px">' + (f'<span class="serif red" style="font-size:96px" id="{g}b">{e(rr["text"])}</span>' if rr else '') + (f'<span class="sans4" style="font-size:42px;margin-top:18px" id="{g}c">{e(sm["text"])}</span>' if sm else '') + '</div>')
        if rr: js.append(f'rise("#{g}b",{rr["t"]},.4);')
        if sm: js.append(f'rise("#{g}c",{sm["t"]},.35);')
        if m.get('plane'):
            pt = m['plane']; S3D['objects'].append({'kind': 'plane', 't0': pt, 't1': r3(min(m['t1'] - .2, pt + 1.35)), 'y': 520})
    elif k == 'end':
        if m.get('ghost'): JS.append(f'ghost("{e(m["ghost"])}",{m["t0"]},{TOTAL + 1});')
        body.append(f'<div class="rule" style="top:690px;left:300px;right:300px;height:3px;background:{th["red"]};opacity:1" id="{g}r"></div>')
        y = 740
        for j, ln in enumerate(m.get('lines', [])):
            body.append(f'<div class="at serif{" red" if ln.get("red") else ""}" style="top:{y}px;font-size:138px;text-align:center" id="{g}l{j}">{e(ln["text"])}</div>')
            js.append((f'wipe("#{g}l{j}",{ln["t"]},.6);' if ln.get('red') else f'rise("#{g}l{j}",{ln["t"]},.55);')); y += 170
        js.append(f'tl.from("#{g}r",{{scaleX:0,transformOrigin:"right center",duration:.5,ease:"power2.out"}},{m["t0"] + .05});tl.to("#cam",{{opacity:0,duration:.4,ease:"power1.in"}},{m["t0"] - .08});')
        SFX.append({'name': 'chime', 't': round(m['t0'] + .3, 2), 'vol': .3})
        grp_end = TOTAL + .3
    else:
        print('⚠ نوع مش معروف:', k); continue
    HT.append(f'<section id="{g}" class="grp ar" dir="rtl">' + ''.join(body) + '</section>')
    JS.append(f'grp("#{g}",{m["t0"]},{r3(grp_end)});' + ''.join(js))

# ---------- دخول/خروج أوضاع الكاميرا ----------
for idx, (a, b, md) in enumerate(wins):
    prv = wins[idx - 1] if idx > 0 and a - wins[idx - 1][1] < 0.2 else None
    nxt = wins[idx + 1] if idx + 1 < len(wins) and wins[idx + 1][0] - b < 0.2 else None
    if md == 'band':
        if not (prv and prv[2] == 'map'): JS.append(f'toBand({a});')
        JS.append(f'fromBand({r3(b - .15)});')
    elif md == 'page':
        JS.append(f'toPage({a});')
        if not (nxt and nxt[2] == 'map'): JS.append(f'fromPage({r3(b - .2)});')
    elif md == 'map':
        back = 'BAND' if (nxt and nxt[2] == 'band') else 'FULL'
        JS.append(f'tl.set("#gl",{{opacity:0}},{r3(a - .02)});tl.to("#gl",{{opacity:1,duration:.3,ease:"power1.out"}},{a});tl.set(["#frame","#tp1","#tp2"],{{opacity:0}},{r3(a + .35)});'
                  f'tl.set("#cam",{{...{back}}},{r3(b - .3)});tl.set("#stage",{{rotation:0}},{r3(b - .3)});'
                  + ('tl.set("#bandEdge",{opacity:1},%s);' % r3(b - .3) if back == 'BAND' else '') +
                  f'tl.to("#gl",{{opacity:0,duration:.28,ease:"power1.in"}},{r3(b - .28)});tl.set("#gl",{{opacity:1}},{r3(b + .03)});')

# ---------- تلوين القصة ----------
LOOK = {'normal': 'sepia(0) grayscale(0) brightness(1)', 'memory': 'sepia(0.55) grayscale(0) brightness(1.03)',
        'war': 'sepia(0) grayscale(0.88) brightness(0.94)', 'calm': 'sepia(0.18) grayscale(0) brightness(1.07)'}
for gr in M.get('grades', []):
    JS.append(f'tl.to("#cam",{{filter:"{LOOK.get(gr["look"], LOOK["normal"])}",duration:{gr.get("dur", .5)}}},{gr["t"]});')
for t in M.get('sweeps', []):
    JS.append(f'tl.set("#sweep",{{opacity:1,x:-900}},{t});tl.to("#sweep",{{x:1300,duration:1.1,ease:"power1.inOut"}},{t});tl.set("#sweep",{{opacity:0}},{r3(t + 1.1)});')
for t in M.get('shakes', []):
    JS.append(f'tl.to("#stage",{{x:9,duration:.04,yoyo:true,repeat:5,ease:"none"}},{t});tl.set("#stage",{{x:0}},{r3(t + .25)});')

# ---------- عناصر صغيرة (accents) ----------
DRAW = {
    'wheat': ((110, 300, 220, 520), '0 0 220 520', .55, .09, [
        ('M120 515 C 115 400, 118 280, 110 120', '#f3ece0', 8), ('M110 130 C 70 110, 62 70, 80 40 C 98 70, 108 95, 110 130', '#e9c06a', 6),
        ('M112 175 C 72 160, 58 120, 72 92 C 92 118, 108 140, 112 175', '#e9c06a', 6), ('M112 175 C 152 160, 166 120, 152 92 C 132 118, 116 140, 112 175', '#e9c06a', 6),
        ('M114 225 C 74 212, 58 172, 70 144 C 92 168, 110 190, 114 225', '#e9c06a', 6), ('M114 225 C 154 212, 170 172, 158 144 C 136 168, 118 190, 114 225', '#e9c06a', 6),
        ('M116 280 C 76 268, 62 230, 74 202 C 96 226, 112 248, 116 280', '#e9c06a', 6), ('M116 280 C 156 268, 170 230, 158 202 C 136 226, 120 248, 116 280', '#e9c06a', 6),
        ('M110 130 C 140 110, 150 70, 136 40 C 120 70, 112 95, 110 130', '#e9c06a', 6)]),
    'crack': ((560, 700, 520, 520), '0 0 520 520', .22, .05, [
        ('M500 20 L 430 90 L 450 140 L 370 200 L 390 260 L 300 330 L 320 380 L 240 470', '#fffaf0', 7), ('M430 90 L 360 100 L 320 70', '#fffaf0', 5),
        ('M370 200 L 300 190 L 250 220', '#fffaf0', 5), ('M300 330 L 220 300', '#fffaf0', 4)]),
    'growth': ((96, 250, 230, 222), '0 0 270 260', .45, .25, [
        ('M30 220 L 95 160 L 140 185 L 230 60', th['ink'], 12), ('M180 58 L 232 56 L 230 108', th['red'], 12)]),
    'steam': ((760, 1040, 150, 220), '0 0 150 220', .7, .12, [
        ('M30 210 C 10 170, 50 150, 30 110 S 50 50, 30 10', '#f3ece0', 7), ('M75 210 C 55 170, 95 150, 75 110 S 95 50, 75 10', '#f3ece0', 7),
        ('M120 210 C 100 170, 140 150, 120 110 S 140 50, 120 10', '#f3ece0', 7)]),
    'underline': ((300, 1398, 480, 50), '0 0 480 50', .3, 0, [('M470 20 C 360 8, 250 38, 140 22 S 30 18, 10 30', th['red'], 10)]),
}
for i, a in enumerate(M.get('accents', [])):
    k, g = a['type'], f'a{i}'
    t0, t1 = a.get('t0', a.get('t')), a.get('t1')
    if k == 'bubble':
        ACC.append(f'<div class="fx" id="{g}" style="left:{a.get("x", 795)}px;top:{a.get("y", 250)}px"><div class="bubble ar" dir="rtl">{e(a.get("text", "ع"))}</div></div>')
        JS.append(f'pop("#{g}",{t0},{t1},{a.get("rot", -6)});')
    elif k == 'pause':
        ACC.append(f'<div class="fx" id="{g}" style="left:{a.get("x", 110)}px;top:{a.get("y", 270)}px"><div class="pause"><i></i><i></i></div></div>')
        JS.append(f'pop("#{g}",{t0},{t1},{a.get("rot", 4)});')
    elif k == 'xmark':
        ACC.append(f'<div class="fx" id="{g}" style="left:{a.get("x", 790)}px;top:{a.get("y", 250)}px"><div class="xst"><svg viewBox="0 0 80 80" width="88" height="88"><path d="M16 16 L64 64 M64 16 L16 64" stroke="{th["red"]}" stroke-width="13" stroke-linecap="round"/></svg></div></div>')
        JS.append(f'pop("#{g}",{t0},{t1},{a.get("rot", -8)});'); SFX.append({'name': 'switch', 't': r3(t0 + .04), 'vol': .3})
    elif k == 'note':
        ACC.append(f'<div class="fx" id="{g}" style="left:{a.get("x", 110)}px;top:{a.get("y", 172)}px"><div class="note ar" dir="rtl">{e(a["text"])}<svg viewBox="0 0 300 30" style="display:block;width:280px;height:26px;margin:2px auto 0"><path id="{g}u" d="M290 14 C 200 4, 120 26, 10 12" stroke="{th["red"]}" stroke-width="8" fill="none" stroke-linecap="round"/></svg></div></div>')
        JS.append(f'pop("#{g}",{t0},{t1},{a.get("rot", -4)});tl.fromTo("#{g}u",{{strokeDasharray:300,strokeDashoffset:300}},{{strokeDashoffset:0,duration:.35}},{r3(a.get("underlineAt", t0 + .35))});')
    elif k == 'rings':
        x, y = a.get('x', 860), a.get('y', 990)
        ACC.append(f'<div class="fx" id="{g}" style="left:{x}px;top:{y}px;width:0;height:0;opacity:1">' + ''.join(f'<div class="ring" id="{g}r{q}"></div>' for q in range(3)) + '</div>')
        for q in range(3):
            for c in range(a.get('cycles', 2)):
                JS.append(f'tl.fromTo("#{g}r{q}",{{scale:.2,opacity:.9}},{{scale:1,opacity:0,duration:1.0,ease:"power1.out",immediateRender:false}},{r3(t0 + q * .35 + c * 1.1)});')
    elif k == 'phone':
        x, y, hr = a.get('x', 70), a.get('y', 720), a.get('heart', t0 + 2)
        ACC.append(f'<div class="fx" id="{g}" style="left:{x}px;top:{y}px"><div class="phone"><div class="scr"><div class="av"></div><div class="ln" style="top:20px;width:90px"></div><div class="ln" style="top:38px;width:60px"></div>'
                   f'<div class="img"></div><div class="ln" style="top:258px;width:150px;right:14px"></div><div class="ln" style="top:276px;width:110px;right:14px"></div>'
                   f'<svg class="ht" viewBox="0 0 48 48" id="{g}h"><path d="M24 42 C 8 30, 2 20, 8 12 C 13 6, 21 7, 24 14 C 27 7, 35 6, 40 12 C 46 20, 40 30, 24 42 Z" fill="{th["red"]}"/></svg></div></div></div>')
        JS.append(f'tl.set("#{g}",{{opacity:1}},{t0});tl.fromTo("#{g}",{{x:-320,rotation:-14}},{{x:0,rotation:-6,duration:.55,ease:"power3.out",immediateRender:false}},{t0});'
                  f'tl.fromTo("#{g}h",{{scale:.2,transformOrigin:"50% 50%"}},{{scale:1.25,duration:.3,ease:"back.out(3)",immediateRender:false}},{hr});'
                  f'tl.to("#{g}",{{x:-340,duration:.35,ease:"power2.in"}},{r3(t1 - .35)});tl.set("#{g}",{{opacity:0}},{t1});')
        SFX.append({'name': 'pop', 't': r3(hr + .02), 'vol': .22})
    elif k == 'rays':
        JS.append(f'tl.fromTo("#rays",{{opacity:0,rotation:0}},{{opacity:.5,rotation:8,duration:.6,immediateRender:false}},{t0});tl.to("#rays",{{rotation:16,duration:{r3(max(.3, t1 - t0 - .9))},ease:"none"}},{r3(t0 + .6)});tl.to("#rays",{{opacity:0,duration:.3}},{r3(t1 - .3)});')
    elif k in DRAW:
        (x, y, w, h), vb, d, stg, paths = DRAW[k]
        x, y = a.get('x', x), a.get('y', y)
        ACC.append(f'<svg class="fx ink" id="{g}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" viewBox="{vb}">'
                   + (f'<rect x="0" y="0" width="270" height="260" rx="22" fill="rgba(239,232,220,.92)"/>' if k == 'growth' else '')
                   + ''.join(f'<path class="dr" d="{pd}" stroke="{col}" stroke-width="{sw}"/>' for pd, col, sw in paths) + '</svg>')
        JS.append(f'draw("#{g}",{t0},{t1},{d},{stg});')
        if k == 'steam': JS.append(f'tl.to("#{g}",{{y:-40,duration:{r3(t1 - t0)},ease:"none"}},{t0});')
        if k == 'growth': JS.append(f'tl.fromTo("#{g}",{{scale:.6,transformOrigin:"50% 50%"}},{{scale:1,duration:.35,ease:"back.out(2)",immediateRender:false}},{t0});')
        if k == 'crack': SFX.append({'name': 'snap', 't': t0, 'vol': .28})
    elif k == 'footsteps':
        n, x0, y0 = a.get('n', 5), a.get('x', 860), a.get('y', 1150)
        for q in range(n):
            ACC.append(f'<div class="foot" id="{g}f{q}" style="left:{x0 - q * 150}px;top:{y0 + (0 if q % 2 else 46)}px;transform:rotate(-90deg)"></div>')
            JS.append(f'tl.fromTo("#{g}f{q}",{{opacity:0,scale:.4}},{{opacity:.95,scale:1,duration:.18,ease:"back.out(2)",immediateRender:false}},{r3(t0 + q * .16)});tl.to("#{g}f{q}",{{opacity:0,duration:.3}},{r3(t1 - .3 + q * .03)});')
    elif k == 'calm':
        # غبار ضو بيطفو + تموّجات (على فنجان أو سطح) — للحظات الهدوء
        rx, ry, rt = a.get('x', 585), a.get('y', 1600), a.get('ripple', t0 + 1.15)
        dust = []
        for q in range(40):
            x = 80 + ((q * 397) % 920); yv = 300 + ((q * 613) % 1300); s = 7 + (q % 4) * 3
            dust.append(f'<div class="dust" id="{g}d{q}" style="left:{x}px;top:{yv}px;width:{s}px;height:{s}px"></div>')
            st = r3(t0 + .05 + (q % 6) * .08)
            JS.append(f'tl.fromTo("#{g}d{q}",{{opacity:0,y:0,x:0}},{{opacity:.85,y:{-120 - (q % 5) * 30},x:{((q % 3) - 1) * 40},duration:{r3(t1 - .3 - st)},ease:"sine.inOut",immediateRender:false}},{st});tl.to("#{g}d{q}",{{opacity:0,duration:.25}},{r3(t1 - .25)});')
        for q in range(3):
            dust.append(f'<div class="rip" id="{g}r{q}" style="left:{rx - 330}px;top:{ry - 110}px;width:660px;height:220px"></div>')
            JS.append(f'tl.fromTo("#{g}r{q}",{{scale:.09,opacity:.9}},{{scale:1,opacity:0,duration:1.6,ease:"power1.out",immediateRender:false}},{r3(rt + q * .45)});')
        ACC.append(f'<div class="fx" style="left:0;top:0;width:1080px;height:1920px;opacity:1">' + ''.join(dust) + '</div>')
    else:
        print('⚠ عنصر مش معروف:', k)

# أصوات تلقائية للمجسمات
for o in S3D['objects']:
    if o['kind'] == 'key': SFX.append({'name': 'star', 't': r3(o['t0'] + .05), 'vol': .25})
    elif o['kind'] == 'coins': SFX.append({'name': 'pop', 't': r3(o['t0'] + .06), 'vol': .25})
    elif o['kind'] == 'case': SFX.append({'name': 'pop', 't': r3(o['t0'] + .03), 'vol': .25})
    elif o['kind'] == 'chest': SFX.append({'name': 'star', 't': r3(o.get('open', o['t0'] + .3)), 'vol': .3})

for c in caps:                       # صوت خفيف لحظة شطب كلمة بالكابشن
    for w in c['w']:
        if w['t'] in M.get('strike', []): SFX.append({'name': 'snap', 't': round(w['s'] + .25, 2), 'vol': .3})
DUR_OF = {'tick': .09, 'pop': .17, 'snap': .16, 'switch': .14, 'star': .07, 'chime': .95, 'fill': 1.4, 'counter': 1.05, 'success': .75}
aud = '\n'.join(f'<audio id="sx{j}" src="sfx/{s["name"]}.wav" data-start="{round(s["t"], 3)}" data-duration="{DUR_OF.get(s["name"], .3)}" data-volume="{s.get("vol", .3)}"></audio>' for j, s in enumerate(sorted(SFX, key=lambda s: s['t'])))

tpl = open(os.path.join(SK, 'assets', 'template.html'), encoding='utf8').read()
for kk, vv in th.items(): tpl = tpl.replace('__' + kk.upper() + '__', vv)
out = (tpl.replace('__FONTFACE__', ff).replace('__TOTAL__', str(TOTAL)).replace('__VDUR__', str(round(VDUR, 3)))
       .replace('__MOMENTS__', '\n'.join(HT)).replace('__ACCENTS__', '\n'.join(ACC)).replace('__AUDIO__', aud).replace('__JS__', '\n'.join(JS))
       .replace('__S3D__', json.dumps(S3D, ensure_ascii=False)).replace('__KEYS__', json.dumps(KEYS))
       .replace('__CAPS__', json.dumps(caps, ensure_ascii=False)).replace('__STRIKE__', json.dumps(M.get('strike', []), ensure_ascii=False)))
open(os.path.join(P, 'index.html'), 'w', encoding='utf8').write(out)

# فحص الإيقاع: أطول فجوة بدون حدث بصري (كل وقت مذكور بأي مكان بالملف بيعتبر حدث)
def times(o):
    if isinstance(o, dict):
        for kk, vv in o.items():
            if kk in ('t', 't0', 'strikeAt', 'open', 'swap', 'dive', 'heart', 'lift', 'fall', 'stop', 'plane', 'weak', 'rich', 'off') and isinstance(vv, (int, float)): yield vv
            else: yield from times(vv)
    elif isinstance(o, list):
        for x in o: yield from times(x)
beats = sorted(set([k[0] for k in KEYS] + list(times(M.get('moments', []))) + list(times(M.get('accents', []))) + list(times(S3D['objects']))
                   + list(M.get('sweeps', [])) + [g_['t'] for g_ in M.get('grades', [])] + [x for a, b, _ in wins for x in (a, b)]))
gaps = [(round(b - a, 2), a) for a, b in zip(beats, beats[1:])]
big = [f'{a:.1f}ث (+{gp})' for gp, a in gaps if gp > 3.5]
print(f"✓ index.html · {len(moms)} لحظة · {len(M.get('accents', []))} عنصر · {len(S3D['objects'])} مجسم{' + ناس' if S3D['crowd'] else ''}{' + خريطة' if S3D['map'] else ''}"
      f" · {len(KEYS)} حركة كاميرا · {len(caps)} كرت كابشن · {len(SFX)} صوت · المدة {TOTAL} ث · الخط: {fontname}")
if big: print('⚠ فجوات أطول من 3.5 ث بدون حدث (زيد عنصر أو حركة كاميرا):', ', '.join(big))
