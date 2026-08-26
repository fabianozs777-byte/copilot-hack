"""
generate_demo_data.py

Generates synthetic frames for cameras C30 and C32 and a summary.csv for demo purposes.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random, time, csv

out_frames = Path('out/frames')
out_frames.mkdir(parents=True, exist_ok=True)

now = int(time.time())
rows = []
for cam in ['c30','c32']:
    for i in range(10):
        ts = now + i*2 + (0 if cam=='c30' else 1)
        img = Image.new('RGB', (1280,720), (20,20,20))
        draw = ImageDraw.Draw(img)
        # draw fake objects
        if random.random() < 0.6:
            # person: draw rectangle
            x = random.randint(100,1000)
            y = random.randint(100,600)
            w = random.randint(30,80)
            h = random.randint(60,160)
            draw.rectangle([x,y,x+w,y+h], outline=(255,200,0), width=6)
            draw.text((x,y-20), 'person', fill=(255,200,0))
            persons = 1
        else:
            persons = 0
        cars = 1 if random.random()<0.3 else 0
        if cars:
            x = random.randint(50,1000)
            y = random.randint(300,650)
            draw.rectangle([x,y,x+120,y+40], outline=(0,200,255), width=6)
            draw.text((x,y-20), 'car', fill=(0,200,255))
        bikes = 1 if random.random()<0.2 else 0
        if bikes:
            x = random.randint(50,1100)
            y = random.randint(200,650)
            draw.rectangle([x,y,x+60,y+30], outline=(200,0,200), width=6)
            draw.text((x,y-20), 'motorbike', fill=(200,0,200))
        filename = f"sample_{cam}_frame{i}_t{ts}.jpg"
        path = out_frames / filename
        img.save(path, quality=90)
        rows.append({'file': str(path), 'camera': cam, 'timestamp': ts, 'sharpness': random.uniform(150,400), 'person': persons, 'car': cars, 'motorbike': bikes, 'output': str(path)})

# write summary.csv
out = Path('out')
out.mkdir(exist_ok=True)
with open(out / 'summary.csv', 'w', newline='', encoding='utf8') as fh:
    writer = csv.DictWriter(fh, fieldnames=['file','camera','timestamp','sharpness','person','car','motorbike','output'])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
print('Generated', len(rows), 'frames in', out_frames)
print('Wrote out/summary.csv')
