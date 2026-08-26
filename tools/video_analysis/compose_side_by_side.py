"""
compose_side_by_side.py

Pairs frames from camera C30 and C32 by nearest timestamp and creates side-by-side images

Usage:
  python compose_side_by_side.py --frames-dir ./out/frames --out-dir ./out/side_by_side --max-delta 5
"""
import argparse
from pathlib import Path
from PIL import Image
import re
import os

TIMESTAMP_RE = re.compile(r'_t(\d+)')
CAM_RE = re.compile(r'c(?:amera_)?(30|32)|c30|c32', re.IGNORECASE)


def extract_ts(path):
    m = TIMESTAMP_RE.search(path.name)
    if m:
        return int(m.group(1))
    # fallback to file mtime
    return int(path.stat().st_mtime)


def find_cam(path):
    m = CAM_RE.search(path.name)
    if m:
        return m.group(1) if m.group(1) else m.group(0)
    return 'unknown'


def pair_and_compose(frames_dir, out_dir, max_delta=5):
    frames_dir = Path(frames_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(frames_dir.glob('*.jpg'))
    items = []
    for f in files:
        items.append({'path': f, 'ts': extract_ts(f), 'cam': find_cam(f)})
    c30 = [i for i in items if i['cam'] and '30' in str(i['cam'])]
    c32 = [i for i in items if i['cam'] and '32' in str(i['cam'])]

    c32_sorted = sorted(c32, key=lambda x: x['ts'])
    for a in c30:
        # find nearest b
        diffs = [(abs(a['ts'] - b['ts']), b) for b in c32_sorted]
        if not diffs:
            continue
        diffs.sort(key=lambda x: x[0])
        delta, b = diffs[0]
        if delta > max_delta:
            continue
        img_a = Image.open(a['path']).convert('RGB')
        img_b = Image.open(b['path']).convert('RGB')
        # resize to same height
        h = min(img_a.height, img_b.height)
        img_a = img_a.resize((int(img_a.width * h / img_a.height), h))
        img_b = img_b.resize((int(img_b.width * h / img_b.height), h))
        new = Image.new('RGB', (img_a.width + img_b.width, h))
        new.paste(img_a, (0,0))
        new.paste(img_b, (img_a.width,0))
        out_name = out_dir / f"pair_{a['path'].stem}_{b['path'].stem}.jpg"
        new.save(out_name, quality=95)
        print('Wrote', out_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames-dir', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--max-delta', type=int, default=5)
    args = parser.parse_args()
    pair_and_compose(args.frames_dir, args.out_dir, args.max_delta)
