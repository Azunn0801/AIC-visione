#!/usr/bin/env python3
"""Convert AIC per-video CLIP .npy files into VisioNe FAISS HDF5 artifacts.

Expected inputs:
  keyframes_root/<video_id>/*.{jpg,jpeg,png}
  clip_root/<video_id>.npy
  optional map_root/<video_id>.csv with columns n,pts_time,fps,frame_idx
  optional object_root/<video_id>/<keyframe_stem>.json

Output:
  output_root/features-<feature_name>/<video_id>/<video_id>-<feature_name>.hdf5
  output_root/aic-visione-frame-map.csv

The generated HDF5 follows VisioNe's FAISS contract:
  datasets: ids (UTF-8 strings), data (float32 matrix)
  file attr: features_name

Additional HDF5 datasets preserve AIC temporal metadata without affecting FAISS:
  keyframe_n, pts_time, fps, frame_idx
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import h5py
import numpy as np


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def normalized_rows(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return x / norms


def read_temporal_map(path: Path) -> list[dict[str, float | int]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"n", "pts_time", "fps", "frame_idx"}
    missing = required.difference(rows[0].keys() if rows else set())
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    return [
        {
            "n": int(row["n"]),
            "pts_time": float(row["pts_time"]),
            "fps": float(row["fps"]),
            "frame_idx": int(row["frame_idx"]),
        }
        for row in rows
    ]


def convert_video(
    video_id: str,
    keyframe_dir: Path,
    clip_file: Path,
    output_root: Path,
    feature_name: str,
    normalize: bool,
    map_file: Path | None = None,
    object_root: Path | None = None,
) -> list[dict[str, str | float | int]]:
    image_files = sorted(
        p for p in keyframe_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not image_files:
        raise ValueError(f"No keyframes found for {video_id}: {keyframe_dir}")

    features = np.load(clip_file, mmap_mode="r")
    if features.ndim != 2:
        raise ValueError(f"Expected 2-D features in {clip_file}, got shape {features.shape}")
    if len(features) != len(image_files):
        raise ValueError(
            f"Count mismatch for {video_id}: {len(image_files)} keyframes vs "
            f"{len(features)} vectors in {clip_file}"
        )

    temporal_rows = read_temporal_map(map_file) if map_file else []
    if temporal_rows and len(temporal_rows) != len(image_files):
        raise ValueError(
            f"Count mismatch for {video_id}: {len(image_files)} keyframes vs "
            f"{len(temporal_rows)} rows in {map_file}"
        )

    data = np.asarray(features, dtype=np.float32)
    if normalize:
        data = normalized_rows(data).astype(np.float32, copy=False)

    ids = [f"{video_id}-{p.stem}" for p in image_files]
    out_dir = output_root / f"features-{feature_name}" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{video_id}-{feature_name}.hdf5"

    with h5py.File(out_file, "w") as h5:
        h5.create_dataset("ids", data=np.asarray(ids, dtype=h5py.string_dtype("utf-8")))
        h5.create_dataset("data", data=data, dtype="float32")
        h5.attrs["features_name"] = feature_name
        h5.attrs["source"] = "AIC supplied CLIP .npy"
        h5.attrs["normalized"] = bool(normalize)
        if temporal_rows:
            h5.create_dataset("keyframe_n", data=np.asarray([r["n"] for r in temporal_rows], dtype="int64"))
            h5.create_dataset("pts_time", data=np.asarray([r["pts_time"] for r in temporal_rows], dtype="float64"))
            h5.create_dataset("fps", data=np.asarray([r["fps"] for r in temporal_rows], dtype="float32"))
            h5.create_dataset("frame_idx", data=np.asarray([r["frame_idx"] for r in temporal_rows], dtype="int64"))

    # Compatibility scene map for VisioNe core/UI. These are keyframe brackets,
    # not BTC ground-truth scenes; AIC frame_idx/pts_time remain authoritative.
    selected_dir = output_root / "selected-frames" / video_id
    selected_dir.mkdir(parents=True, exist_ok=True)
    scenes_file = selected_dir / f"{video_id}-scenes.csv"
    with scenes_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Start Frame", "End Frame", "Start Time (seconds)", "End Time (seconds)"],
        )
        writer.writeheader()
        for i, temporal in enumerate(temporal_rows):
            next_temporal = temporal_rows[i + 1] if i + 1 < len(temporal_rows) else temporal
            writer.writerow({
                "Start Frame": temporal["frame_idx"],
                "End Frame": (next_temporal["frame_idx"] - 1) if i + 1 < len(temporal_rows) else temporal["frame_idx"],
                "Start Time (seconds)": temporal["pts_time"],
                "End Time (seconds)": next_temporal["pts_time"] if i + 1 < len(temporal_rows) else temporal["pts_time"],
            })

    rows: list[dict[str, str | float | int]] = []
    for i, image_path in enumerate(image_files):
        row: dict[str, str | float | int] = {
            "video_id": video_id,
            "keyframe_n": temporal_rows[i]["n"] if temporal_rows else i + 1,
            "keyframe_stem": image_path.stem,
            "pts_time": temporal_rows[i]["pts_time"] if temporal_rows else "",
            "fps": temporal_rows[i]["fps"] if temporal_rows else "",
            "frame_idx": temporal_rows[i]["frame_idx"] if temporal_rows else "",
            "prev_frame_idx": temporal_rows[i - 1]["frame_idx"] if temporal_rows and i > 0 else "",
            "next_frame_idx": temporal_rows[i + 1]["frame_idx"] if temporal_rows and i + 1 < len(temporal_rows) else "",
            "next_pts_time": temporal_rows[i + 1]["pts_time"] if temporal_rows and i + 1 < len(temporal_rows) else "",
            "gap_to_next_sec": (temporal_rows[i + 1]["pts_time"] - temporal_rows[i]["pts_time"]) if temporal_rows and i + 1 < len(temporal_rows) else "",
            "bracket_start_frame": temporal_rows[i]["frame_idx"] if temporal_rows else "",
            "bracket_end_frame": (temporal_rows[i + 1]["frame_idx"] - 1) if temporal_rows and i + 1 < len(temporal_rows) else "",
            "visione_id": ids[i],
            "keyframe_path": str(image_path.resolve()),
            "object_path": "",
        }
        if object_root:
            candidate = object_root / video_id / f"{image_path.stem}.json"
            if candidate.exists():
                row["object_path"] = str(candidate.resolve())
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyframes-root", type=Path, required=True)
    parser.add_argument("--clip-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--map-root", type=Path, help="Directory containing <video_id>.csv maps.")
    parser.add_argument("--object-root", type=Path, help="Directory containing <video_id>/<keyframe_stem>.json files.")
    parser.add_argument("--feature-name", default="clip-openai")
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Keep vectors unchanged; default normalizes rows for cosine/IP search.",
    )
    parser.add_argument(
        "--video-id",
        action="append",
        help="Convert only this video ID; may be supplied multiple times.",
    )
    args = parser.parse_args()

    keyframe_dirs = sorted(p for p in args.keyframes_root.iterdir() if p.is_dir())
    if args.video_id:
        wanted = set(args.video_id)
        keyframe_dirs = [p for p in keyframe_dirs if p.name in wanted]

    if not keyframe_dirs:
        raise SystemExit("No video directories found under --keyframes-root")

    all_rows: list[dict[str, str | float | int]] = []
    for keyframe_dir in keyframe_dirs:
        video_id = keyframe_dir.name
        clip_file = args.clip_root / f"{video_id}.npy"
        if not clip_file.exists():
            raise SystemExit(f"Missing CLIP file for {video_id}: {clip_file}")
        map_file = args.map_root / f"{video_id}.csv" if args.map_root else None
        rows = convert_video(
            video_id,
            keyframe_dir,
            clip_file,
            args.output_root,
            args.feature_name,
            normalize=not args.no_normalize,
            map_file=map_file,
            object_root=args.object_root,
        )
        all_rows.extend(rows)
        print(f"converted {video_id}: {len(rows)} frames")

    map_file = args.output_root / "aic-visione-frame-map.csv"
    map_file.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "video_id", "keyframe_n", "keyframe_stem", "pts_time", "fps",
        "frame_idx", "prev_frame_idx", "next_frame_idx", "next_pts_time",
        "gap_to_next_sec", "bracket_start_frame", "bracket_end_frame",
        "visione_id", "keyframe_path", "object_path",
    ]
    with map_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"wrote {len(all_rows)} frame mappings to {map_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
