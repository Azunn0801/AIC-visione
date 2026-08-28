#!/usr/bin/env python3
"""Production Batch OCR Pipeline for AIC Dataset.

Extracts Vietnamese & English text from all keyframes across Keyframes_L21..L30,
stores checkpointed results, enriches lucene-documents, and triggers Lucene re-indexing.
"""

import os
import sys

# Ensure single GPU to avoid ROCm DataParallel imbalance warning
if "CUDA_VISIBLE_DEVICES" not in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

import glob
import json
import gzip
import time
import argparse
from pathlib import Path

try:
    import easyocr
except ImportError:
    easyocr = None


def get_all_video_dirs(keyframes_root: Path, prefix: str = ""):
    pattern = str(keyframes_root / "Keyframes_*" / "keyframes" / f"{prefix}*")
    video_dirs = sorted([Path(p) for p in glob.glob(pattern) if os.path.isdir(p)])
    return video_dirs


def process_video_ocr(reader, video_dir: Path, out_dir: Path, min_conf: float = 0.35):
    video_id = video_dir.name
    out_file = out_dir / f"{video_id}-ocr.jsonl.gz"

    if out_file.exists():
        return video_id, 0, True  # Skipped (already done)

    image_files = sorted(video_dir.glob("*.jpg"))
    if not image_files:
        return video_id, 0, False

    records = []
    for img_path in image_files:
        stem = img_path.stem  # e.g., "001"
        img_id = f"{video_id}-{stem}"
        try:
            results = reader.readtext(str(img_path))
            texts = []
            for box, text, conf in results:
                text_clean = text.strip()
                if float(conf) >= min_conf and len(text_clean) >= 2:
                    texts.append(text_clean)

            if texts:
                records.append({
                    "imgID": img_id,
                    "stem": stem,
                    "ocr_texts": texts,
                    "ocr_joined": " ".join(texts)
                })
        except Exception:
            pass

    out_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_file, "wt", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return video_id, len(records), False


def merge_ocr_into_lucene_docs(ocr_root: Path, lucene_docs_root: Path):
    print("Merging OCR results into Lucene documents...")
    ocr_files = sorted(ocr_root.glob("*-ocr.jsonl.gz"))
    merged_count = 0

    for ocr_file in ocr_files:
        video_id = ocr_file.name.replace("-ocr.jsonl.gz", "")
        doc_path = lucene_docs_root / video_id / f"{video_id}-lucene-docs.jsonl.gz"
        if not doc_path.exists():
            continue

        ocr_map = {}
        with gzip.open(ocr_file, "rt", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                ocr_map[rec["imgID"]] = rec["ocr_joined"]

        if not ocr_map:
            continue

        with gzip.open(doc_path, "rt", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]

        updated = False
        for rec in records:
            img_id = rec.get("imgID", "")
            if img_id in ocr_map:
                ocr_text = ocr_map[img_id]
                orig_meta = rec.get("metadata_norm", "")
                if " [ocr: " in orig_meta:
                    orig_meta = orig_meta[:orig_meta.find(" [ocr: ")]
                rec["metadata_norm"] = orig_meta + f" [ocr: {ocr_text}]"
                rec["ocr_text"] = ocr_text
                updated = True

        if updated:
            with gzip.open(doc_path, "wt", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            merged_count += 1

    print(f"Successfully merged OCR text into {merged_count} video Lucene documents!")


def main():
    parser = argparse.ArgumentParser(description="Batch OCR for AIC Dataset")
    parser.add_argument("--keyframes-root", default="/home/azunn0801/data/AIC2026", help="Path to AIC2026 data root")
    parser.add_argument("--output-dir", default="/home/azunn0801/aic-visione/ocr-results", help="Directory to save OCR results")
    parser.add_argument("--lucene-docs-root", default="/home/azunn0801/aic-visione/lucene-documents", help="Path to lucene documents")
    parser.add_argument("--prefix", default="", help="Filter by video prefix (e.g. L21, L22, L30)")
    parser.add_argument("--gpu", type=int, default=0, help="GPU device ID (default 0)")
    parser.add_argument("--min-conf", type=float, default=0.35, help="Minimum OCR confidence score")
    parser.add_argument("--merge-only", action="store_true", help="Only merge existing OCR results into Lucene without re-extracting")
    args = parser.parse_args()

    keyframes_root = Path(args.keyframes_root)
    out_dir = Path(args.output_dir)
    lucene_docs_root = Path(args.lucene_docs_root)

    if args.merge_only:
        merge_ocr_into_lucene_docs(out_dir, lucene_docs_root)
        return

    if easyocr is None:
        print("Error: easyocr is not installed in current Python environment. Please run with ai_env Python:")
        print("  /home/azunn0801/ai_env/bin/python tools/extract_dataset_ocr.py")
        sys.exit(1)

    print(f"Initializing EasyOCR with languages [vi, en] on GPU {args.gpu}...")
    reader = easyocr.Reader(["vi", "en"], gpu=True)

    video_dirs = get_all_video_dirs(keyframes_root, args.prefix)
    print(f"Found {len(video_dirs)} videos to process (prefix: '{args.prefix}').")

    t0 = time.time()
    total_extracted_frames = 0
    skipped_count = 0

    for i, vdir in enumerate(video_dirs, 1):
        vid = vdir.name
        t_v0 = time.time()
        vid_id, extracted_frames, skipped = process_video_ocr(reader, vdir, out_dir, args.min_conf)
        t_v = time.time() - t_v0

        if skipped:
            skipped_count += 1
        else:
            total_extracted_frames += extracted_frames
            print(f"[{i}/{len(video_dirs)}] {vid}: extracted text from {extracted_frames} frames in {t_v:.1f}s")

        if i % 10 == 0:
            elapsed = time.time() - t0
            print(f"--- Progress: {i}/{len(video_dirs)} videos ({total_extracted_frames} frames extracted, {skipped_count} skipped, {elapsed/60:.1f} min elapsed) ---")

    dt = time.time() - t0
    print(f"\nOCR Extraction complete in {dt/60:.1f} minutes! ({total_extracted_frames} frames extracted)")

    merge_ocr_into_lucene_docs(out_dir, lucene_docs_root)
    print("\n[!] To re-index Lucene with new OCR data, run:")
    print("  docker run --rm -v /home/azunn0801/aic-visione:/data visione/lucene-index-manager /data/lucene-index add --force /data/lucene-documents/{video_id}/{video_id}-lucene-docs.jsonl.gz --video-ids-list-path /data/aic-video-ids.txt")
    print("  docker restart aic-visione-core-1")


if __name__ == "__main__":
    main()
