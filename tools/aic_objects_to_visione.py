#!/usr/bin/env python3
"""Convert AIC Faster R-CNN/OpenImages JSON records to VisioNe raw JSONL.GZ.

Input:
  input_root/<video_id>/<keyframe_stem>.json

Output:
  output_root/objects-frcnn-oiv4/<video_id>/<video_id>-objects-frcnn-oiv4.jsonl.gz

The output schema follows VisioNe's objects-openimagesv4 extractor and keeps
one record per keyframe with a VisioNe-compatible `_id`.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def get_first(data: dict, *keys: str):
    for key in keys:
        if key in data:
            return data[key]
    raise KeyError(f"none of the keys found: {keys}")


def convert_video(video_dir: Path, output_root: Path) -> int:
    video_id = video_dir.name
    files = sorted(video_dir.glob("*.json"))
    if not files:
        raise ValueError(f"No JSON files under {video_dir}")

    out_dir = output_root / "objects-frcnn-oiv4" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{video_id}-objects-frcnn-oiv4.jsonl.gz"

    count = 0
    with gzip.open(out_file, "wt", encoding="utf-8") as out:
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            scores = [float(x) for x in get_first(data, "object_scores", "detection_scores")]
            names = list(get_first(data, "object_class_names", "detection_class_entities"))
            entities = list(get_first(data, "object_class_entities", "detection_class_names"))
            labels = [int(float(x)) for x in get_first(data, "object_class_labels", "detection_class_labels")]
            boxes = [[float(v) for v in box] for box in get_first(data, "object_boxes_yxyx", "detection_boxes")]
            lengths = {len(scores), len(names), len(entities), len(labels), len(boxes)}
            if len(lengths) != 1:
                raise ValueError(f"parallel arrays have different lengths in {path}: {lengths}")
            record = {
                "_id": f"{video_id}-{path.stem}",
                "detector": "frcnn-oiv4",
                "object_class_labels": labels,
                "object_class_names": names,
                "object_class_entities": entities,
                "object_scores": scores,
                "object_boxes_yxyx": boxes,
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--video-id", action="append")
    args = parser.parse_args()

    dirs = sorted(p for p in args.input_root.iterdir() if p.is_dir())
    if args.video_id:
        wanted = set(args.video_id)
        dirs = [p for p in dirs if p.name in wanted]
    if not dirs:
        raise SystemExit("No video directories found")

    total = 0
    for video_dir in dirs:
        count = convert_video(video_dir, args.output_root)
        total += count
        print(f"converted {video_dir.name}: {count} object records")
    print(f"total records: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
