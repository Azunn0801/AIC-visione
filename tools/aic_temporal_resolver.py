#!/usr/bin/env python3
"""Resolve a VisioNe hit to an AIC frame bracket and optional scan window.

This utility does not extract video frames. It only converts a retrieval hit
into frame/time coordinates that a submission adapter or UI can use.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"empty mapping: {path}")
    return rows


def as_int(row: dict[str, str], key: str) -> int | None:
    value = row.get(key, "")
    return int(value) if value not in (None, "") else None


def as_float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    return float(value) if value not in (None, "") else None


def resolve(rows: list[dict[str, str]], visione_id: str, tolerance_seconds: float) -> dict[str, object]:
    positions = {row["visione_id"]: i for i, row in enumerate(rows)}
    if visione_id not in positions:
        raise KeyError(f"visione_id not found: {visione_id}")
    i = positions[visione_id]
    row = rows[i]
    fps = as_float(row, "fps")
    frame_idx = as_int(row, "frame_idx")
    pts_time = as_float(row, "pts_time")
    next_frame = as_int(row, "next_frame_idx")
    next_time = as_float(row, "next_pts_time")
    if fps is None or frame_idx is None or pts_time is None:
        raise ValueError("mapping row lacks fps/frame_idx/pts_time; regenerate with --map-root")

    bracket_end = next_frame - 1 if next_frame is not None else frame_idx
    scan_start = max(0, int(round((pts_time - tolerance_seconds) * fps)))
    scan_end = int(round((pts_time + tolerance_seconds) * fps))
    return {
        "video_id": row["video_id"],
        "visione_id": visione_id,
        "keyframe_n": as_int(row, "keyframe_n"),
        "keyframe_stem": row.get("keyframe_stem"),
        "keyframe_pts_time": pts_time,
        "keyframe_frame_idx": frame_idx,
        "previous_keyframe_frame_idx": as_int(row, "prev_frame_idx"),
        "next_keyframe_frame_idx": next_frame,
        "bracket_start_frame": frame_idx,
        "bracket_end_frame": bracket_end,
        "bracket_start_time": pts_time,
        "bracket_end_time": next_time,
        "scan_tolerance_seconds": tolerance_seconds,
        "scan_start_frame": scan_start,
        "scan_end_frame": scan_end,
        "fps": fps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--visione-id", required=True)
    parser.add_argument(
        "--tolerance-seconds",
        type=float,
        default=0.0,
        help="Optional video scan radius around the retrieved keyframe; use 300 for a five-minute window.",
    )
    args = parser.parse_args()
    result = resolve(load_rows(args.mapping), args.visione_id, args.tolerance_seconds)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
