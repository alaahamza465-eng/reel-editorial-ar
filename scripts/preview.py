#!/usr/bin/env python3
"""الخطوة 8: ورقة معاينة (لقطات ثابتة) بدون رندر كامل — ثواني بدل نص ساعة.
الاستخدام: python3 preview.py <project_dir> <out.jpg> t1 t2 t3 ... (6 أو 9 لقطات)
بيفتح index.html بمتصفح الرندر نفسه، بيحط الفيديو والتايملاين على كل ثانية، وبيصوّر."""
import sys, os, glob, asyncio, subprocess
from playwright.async_api import async_playwright

P, out = sys.argv[1], sys.argv[2]
ts = [float(x) for x in sys.argv[3:]]

def chrome():
    for pat in ['~/.cache/hyperframes/chrome/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell*',
                '~/AppData/Local/hyperframes/chrome/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell*.exe',
                '~/Library/Caches/hyperframes/chrome/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell']:
        g = sorted(glob.glob(os.path.expanduser(pat)))
        g = [x for x in g if os.path.isfile(x) and os.access(x, os.X_OK)]
        if g: return g[-1]
    return None   # كروميوم تبع playwright (ممكن ما يشغّل mp4)

async def main():
    async with async_playwright() as p:
        exe = chrome()
        b = await p.chromium.launch(executable_path=exe, args=['--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']) if exe else await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        pg.on('pageerror', lambda e: print('خطأ بالصفحة:', e))
        await pg.goto('file://' + os.path.abspath(os.path.join(P, 'index.html')), wait_until='domcontentloaded')
        for _ in range(120):   # استنى الثري دي والتايملاين
            if await pg.evaluate('!!(window.S3D && window.__timelines && window.__timelines.main)'): break
            await pg.wait_for_timeout(500)
        await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(600)
        files = []
        for i, t in enumerate(ts):
            await pg.evaluate('''async (t) => { const v = document.getElementById('v'); v.pause();
                await new Promise(r => { v.onseeked = () => r(); v.currentTime = Math.min(t, (v.duration || 1e9) - 0.05); setTimeout(r, 3000); });
                window.__timelines.main.seek(t, false); }''', t)
            await pg.wait_for_timeout(120)
            f = os.path.join(os.path.dirname(os.path.abspath(out)), f'.pv_{i}.png'); await pg.screenshot(path=f); files.append(f)
        await b.close()
    cols = 3; rows = (len(files) + cols - 1) // cols
    ins, fc = [], ''
    for i, f in enumerate(files):
        ins += ['-i', f]
        fc += f"[{i}:v]scale=360:-2,drawbox=x=0:y=0:w=96:h=34:color=black@0.7:t=fill,drawtext=text='{ts[i]:.1f}':x=8:y=4:fontsize=26:fontcolor=yellow[s{i}];"
    for i in range(len(files), rows * cols): fc += f"color=c=black:s=360x640:d=1[s{i}];"
    fc += ''.join(f'[s{i}]' for i in range(rows * cols)) + f'xstack=inputs={rows * cols}:layout=' + '|'.join(f'{(i % cols) * 360}_{(i // cols) * 640}' for i in range(rows * cols)) + '[o]'
    r = subprocess.run(['ffmpeg', '-v', 'error'] + ins + ['-filter_complex', fc, '-map', '[o]', '-frames:v', '1', '-q:v', '3', '-y', out])
    if r.returncode:   # بعض نسخ ffmpeg بدون drawtext
        fc2 = fc.replace(",drawbox=x=0:y=0:w=96:h=34:color=black@0.7:t=fill", "")
        import re; fc2 = re.sub(r",drawtext=[^\[]*", "", fc2)
        subprocess.run(['ffmpeg', '-v', 'error'] + ins + ['-filter_complex', fc2, '-map', '[o]', '-frames:v', '1', '-q:v', '3', '-y', out], check=True)
    for f in files: os.remove(f)
    print('✓', out)

asyncio.run(main())
