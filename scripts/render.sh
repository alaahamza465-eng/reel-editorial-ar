#!/usr/bin/env bash
# الخطوة 9: الرندر النهائي + نسخة مضغوطة للنشر.
# الاستخدام: bash scripts/render.sh <project_dir> [حجم_أقصى_بالميجا=30]
# - final.mp4: الجودة العالية (ماستر)
# - reel.mp4: مضغوط بمرورين لتحت الحجم المطلوب (انستقرام بيعيد الضغط أصلاً، فالفرق بالعين قليل)
set -e
P="$1"; MAXMB="${2:-30}"
cd "$P"
mkdir -p renders
WORKERS=$(( $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2) > 4 ? 4 : $(nproc 2>/dev/null || echo 2) ))
echo "⏳ الرندر (بياخذ وقت: تقريباً 10-30 ضعف طول الفيديو حسب كمية الثري دي)…"
# الرندر بمقاطع (كل 8 ث لحال، والمتصفح بيتجدد بين المقاطع): الرندر الطويل بمقطع واحد ممكن يعلّق.
# إذا علّق، بنعيد بـ--resume وبيكمل من آخر مقطع خلص بدل ما يبدأ من الصفر.
export HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=240 HF_SEGMENT_BROWSER_RECYCLE=1
rm -f renders/final.mp4
for TRY in 1 2 3; do
  RES=""; [ "$TRY" -gt 1 ] && RES="--resume" && echo "↻ إعادة ومكمّل من وين وقف (محاولة $TRY)…"
  npx --yes hyperframes@0.8.122 render . --sdr --no-low-memory-mode --workers "$WORKERS" --keep-segments $RES -o renders/final.mp4 2>&1 | tr '\r' '\n' | grep -E "Streaming frame [0-9]+/|rendered in|Error|error|failed" | awk 'NR%60==1 || /rendered|rror|failed/' || true
  [ -f renders/final.mp4 ] && break
done
[ -f renders/final.mp4 ] || { echo "✗ الرندر ما خلص بعد 3 محاولات"; exit 1; }
rm -rf renders/.hf-segments
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/final.mp4)
SIZE=$(stat -c %s renders/final.mp4 2>/dev/null || stat -f %z renders/final.mp4)
LIMIT=$(( MAXMB * 1000 * 1000 ))
if [ "$SIZE" -le "$LIMIT" ]; then cp renders/final.mp4 renders/reel.mp4; else
  VB=$(python3 -c "print(int(($LIMIT*8*0.96/$DUR - 128000)/1000))")
  echo "⏳ ضغط لتحت ${MAXMB} ميجا (${VB}k)…"
  ffmpeg -v error -y -i renders/final.mp4 -c:v libx264 -preset medium -b:v ${VB}k -pass 1 -passlogfile renders/p2 -an -f null /dev/null
  ffmpeg -v error -y -i renders/final.mp4 -c:v libx264 -preset medium -b:v ${VB}k -maxrate $((VB*2))k -bufsize $((VB*4))k -pass 2 -passlogfile renders/p2 \
    -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart renders/reel.mp4
  rm -f renders/p2*
fi
ffmpeg -nostats -i renders/reel.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tr -s ' ' | tr '\n' ' '; echo
ls -la renders/reel.mp4 | awk '{printf "✓ renders/reel.mp4 · %.1f ميجا\n", $5/1000000}'
