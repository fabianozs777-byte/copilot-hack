Night camera scan pipeline

Overview
- Scripts to process camera files (C30, C32), detect people/cars/motorbikes, extract sharp frames, compose side-by-side images, and generate a PDF + simple HTML dashboard.

Steps
1. Place camera files (videos or images) in a folder, e.g. ./input
2. Install dependencies in a venv: python -m venv .venv && .venv\Scripts\pip install -r tools\video_analysis\requirements.txt
3. Run processing:
   python tools\video_analysis\process_videos.py --input-dir ./input --output-dir ./out
4. Compose pairs:
   python tools\video_analysis\compose_side_by_side.py --frames-dir ./out/frames --out-dir ./out/side_by_side
5. Generate report:
   python tools\video_analysis\generate_report.py --summary ./out/summary.csv --pairs ./out/side_by_side --inquiry ./inquiry.pdf --out ./out/report

Notes
- YOLOv8 will download a small model automatically on first run. Ensure network access.
- The scripts assume camera id in filenames (c30 / c32). If your filenames differ, rename or adapt the regex in CAM_REGEX.
- Time-window filtering (22:00-06:00) is supported if filenames or metadata provide timestamps; otherwise run on the provided files and filter externally.
