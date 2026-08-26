"""
generate_report.py

Generates a PDF report and a small HTML dashboard from the analysis output.

Usage:
  python generate_report.py --summary ./out/summary.csv --pairs ./out/side_by_side --inquiry ./inquest.pdf --out ./out/report
"""
import argparse
from pathlib import Path
import pandas as pd
from fpdf import FPDF
import os


def make_pdf(summary_csv, pairs_dir, inquiry_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(summary_csv) if Path(summary_csv).exists() else None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Cameras C30 & C32 - Night Scan Report', ln=True)
    pdf.set_font('Arial', size=11)
    if df is not None:
        total_people = df['person'].sum() if 'person' in df.columns else 0
        total_cars = df['car'].sum() if 'car' in df.columns else 0
        total_bikes = df['motorbike'].sum() if 'motorbike' in df.columns else 0
        pdf.cell(0, 8, f'Total detections - people: {total_people}, cars: {total_cars}, motorbikes: {total_bikes}', ln=True)

    # include inquiry text if provided
    if inquiry_path and Path(inquiry_path).exists():
        pdf.cell(0, 8, 'Inquiry provided (attached).', ln=True)
    else:
        pdf.cell(0, 8, 'No inquiry file found.', ln=True)

    # add side-by-side images
    pairs = sorted(Path(pairs_dir).glob('*.jpg')) if Path(pairs_dir).exists() else []
    cnt = 0
    for p in pairs:
        if cnt and cnt % 2 == 0:
            pdf.add_page()
        pdf.image(str(p), w=180)
        pdf.ln(5)
        cnt += 1

    out_pdf = out_dir / 'night_scan_report.pdf'
    pdf.output(str(out_pdf))
    print('Wrote', out_pdf)
    # Simple HTML dashboard (counts by hour)
    if df is not None and 'timestamp' in df.columns:
        df['ts'] = pd.to_datetime(df['timestamp'], unit='s')
        by_hour = df.groupby(df['ts'].dt.hour)[['person','car','motorbike']].sum() if 'person' in df.columns else None
        html = ['<html><head><title>Night Scan Dashboard</title></head><body>']
        html.append('<h1>Night Scan Dashboard</h1>')
        if by_hour is not None:
            html.append(by_hour.to_html())
        html.append('<h2>Side-by-side samples</h2>')
        for p in pairs[:20]:
            html.append(f'<div style="margin-bottom:12px"><img src="{os.path.relpath(p, out_dir)}" style="max-width:900px;"/></div>')
        html.append('</body></html>')
        html_path = out_dir / 'dashboard.html'
        with open(html_path, 'w', encoding='utf8') as fh:
            fh.write('\n'.join(html))
        print('Wrote', html_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True)
    parser.add_argument('--pairs', required=True)
    parser.add_argument('--inquiry')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    make_pdf(args.summary, args.pairs, args.inquiry, args.out)
