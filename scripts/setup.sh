#!/usr/bin/env bash
# تجهيز الأدوات مرة وحدة: يفحص، ويثبّت الناقص، ويحمّل الخطوط البديلة، ويولّد الأصوات.
# الاستخدام: bash scripts/setup.sh [--check]
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
ok=1
need() { if command -v "$1" >/dev/null 2>&1; then echo "✓ $1"; else echo "✗ $1 ناقص — $2"; ok=0; fi; }
need ffmpeg  "ثبّته: macOS: brew install ffmpeg · Windows: winget install ffmpeg · Linux: apt install ffmpeg"
need ffprobe "يجي مع ffmpeg"
need node    "ثبّت Node 22 أو أحدث من nodejs.org"
need $PY     "ثبّت Python 3.10+"
if command -v node >/dev/null 2>&1; then
  v=$(node -v | sed 's/v//; s/\..*//'); [ "$v" -ge 22 ] 2>/dev/null && echo "✓ node $v" || { echo "✗ node قديم ($v) — بدها 22+"; ok=0; }
fi
[ "${1:-}" = "--check" ] && { [ $ok = 1 ] && echo "كل شي جاهز" || echo "فيه ناقص"; exit 0; }
[ $ok = 1 ] || { echo "ثبّت الناقص فوق وارجع شغّل السكربت."; exit 1; }

# مكتبات بايثون
$PY -c "import faster_whisper" 2>/dev/null || $PY -m pip install -q faster-whisper || $PY -m pip install -q --break-system-packages faster-whisper
$PY -c "import numpy, PIL" 2>/dev/null || $PY -m pip install -q numpy pillow || $PY -m pip install -q --break-system-packages numpy pillow
$PY -c "import playwright" 2>/dev/null || $PY -m pip install -q playwright || $PY -m pip install -q --break-system-packages playwright
echo "✓ مكتبات بايثون"

# متصفح الرندر الخاص بـ HyperFrames
npx --yes hyperframes browser ensure >/dev/null 2>&1 && echo "✓ متصفح الرندر" || echo "⚠ ما قدرت أجهّز متصفح الرندر — جرّب: npx hyperframes browser ensure"

# خطوط بديلة مفتوحة (OFL) لو خط ثمانية مش موجود
F="$HERE/assets/fonts"; mkdir -p "$F"
G=https://raw.githubusercontent.com/google/fonts/main/ofl
for f in ibmplexsansarabic/IBMPlexSansArabic-Regular.ttf ibmplexsansarabic/IBMPlexSansArabic-Bold.ttf amiri/Amiri-Regular.ttf amiri/Amiri-Bold.ttf ibmplexsansarabic/OFL.txt amiri/OFL.txt; do
  b=$(basename "$f"); [ "$b" = OFL.txt ] && b="OFL-$(dirname "$f").txt"
  [ -s "$F/$b" ] || curl -sSL -m 60 -o "$F/$b" "$G/$f" || echo "⚠ ما نزل $b"
done
echo "✓ خطوط بديلة (IBM Plex Sans Arabic + Amiri)"
ls "$F" | grep -qi thmanyah && echo "✓ خط ثمانية موجود" || echo "ℹ خط ثمانية مش موجود — رح أستعمل الخطوط البديلة. (نزّله من الصفحة الرسمية وحطّه بـ assets/fonts — شوف references/fonts.md)"

# أصوات خفيفة (مولّدة، بدون حقوق)
$PY "$HERE/scripts/make_sfx.py" "$HERE/assets/sfx" && echo "✓ الأصوات"
echo "جاهز."
