"""
process_videos.py

Usage examples:
  python process_videos.py --input-dir ./input --output-dir ./out --start 22:00 --end 06:00

What it does:
 - Finds files with camera IDs (c30/c32) in filenames under input-dir
 - Extracts frames from each video/image
 - Runs YOLOv8 detector (people, car, motorbike)
 - Keeps sharp frames (Laplacian variance) and saves annotated images + a CSV summary
"""
import argparse
import os
import re
import cv2
import time
from pathlib import Path
import pandas as pd
from ultralytics import YOLO
from PIL import Image
import numpy as np
from tqdm import tqdm

CAM_REGEX = re.compile(r'c(?:amera_)?(30|32)|c30|c32', re.IGNORECASE)

# Sharpness: variance of Laplacian
def sharpness(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def detect_and_extract(input_dir, output_dir, start_time=None, end_time=None, min_sharp=100.0):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir = output_dir / 'annotated'
    annotated_dir.mkdir(exist_ok=True)
    frames_dir = output_dir / 'frames'
    frames_dir.mkdir(exist_ok=True)

    model = YOLO('yolov8n.pt')  # downloads if needed

    rows = []

    # find files
    files = [p for p in input_dir.rglob('*') if p.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.jpg', '.jpeg', '.png']]
    for f in files:
        name = f.name
        cam = None
        m = CAM_REGEX.search(name)
        if m:
            cam = m.group(1) if m.group(1) else m.group(0)
        else:
            cam = 'unknown'

        # If image, process single frame
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            img = cv2.imread(str(f))
            s = sharpness(img)
            results = model(img)
            annotated = results[0].plot()
            out_name = frames_dir / f"{f.stem}_annotated{f.suffix}"
            cv2.imwrite(str(out_name), annotated)
            counts = { 'person':0, 'car':0, 'motorbike':0 }
            if hasattr(results[0], 'boxes'):
                for cls in results[0].boxes.cls:
                    label = model.names[int(cls)]
                    if label in counts:
                        counts[label] += 1
            rows.append({'file': str(f), 'camera': cam, 'timestamp': f.stat().st_mtime, 'sharpness': s, **counts, 'output': str(out_name)})
            continue

        # For videos: extract frames every N seconds
        cap = cv2.VideoCapture(str(f))
        if not cap.isOpened():
            print('Failed opening', f)
            continue
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        # sample every 1 second (configurable)
        sample_interval = 1.0
        frame_idx = 0
        pbar = tqdm(total=total, desc=f.name)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % max(1, int(fps*sample_interval)) == 0:
                t = frame_idx / fps
                s = sharpness(frame)
                if s >= min_sharp:
                    results = model(frame)
                    annotated = results[0].plot()
                    timestamp_label = int(time.time())
                    out_name = frames_dir / f"{f.stem}_frame{frame_idx}_t{timestamp_label}.jpg"
                    cv2.imwrite(str(out_name), annotated)
                    counts = { 'person':0, 'car':0, 'motorbike':0 }
                    if hasattr(results[0], 'boxes'):
                        for cls in results[0].boxes.cls:
                            label = model.names[int(cls)]
                            if label in counts:
                                counts[label] += 1
                    rows.append({'file': str(f), 'camera': cam, 'frame_index': frame_idx, 'timestamp': timestamp_label, 'sharpness': s, **counts, 'output': str(out_name)})
            frame_idx += 1
            pbar.update(1)
        pbar.close()
        cap.release()

    df = pd.DataFrame(rows)
    csv_out = output_dir / 'summary.csv'
    df.to_csv(csv_out, index=False)
    print('Wrote', csv_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('--min-sharp', type=float, default=100.0)
    args = parser.parse_args()
    detect_and_extract(args.input_dir, args.output_dir, args.start, args.end, args.min_sharp)
