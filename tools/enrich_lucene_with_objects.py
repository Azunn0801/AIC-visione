#!/usr/bin/env python3
import os
import glob
import json
import gzip
import time
from pathlib import Path

OBJECT_VI_MAP = {
    "person": "person nguoi",
    "man": "man dan ong",
    "woman": "woman phu nu",
    "girl": "girl co gai be gai",
    "boy": "boy cau be",
    "car": "car xe hoi oto",
    "land vehicle": "land vehicle xe co",
    "vehicle": "vehicle phuong tien",
    "bicycle": "bicycle xe dap",
    "motorcycle": "motorcycle xe may",
    "boat": "boat thuyen ghe tau",
    "airplane": "airplane may bay phi co",
    "helicopter": "helicopter truc thang",
    "bus": "bus xe buyt",
    "truck": "truck xe tai",
    "bird": "bird chim",
    "cat": "cat meo",
    "dog": "dog cho",
    "horse": "horse ngua",
    "cattle": "cattle bo trau",
    "goat": "goat de",
    "sheep": "sheep cuu",
    "elephant": "elephant voi",
    "tiger": "tiger ho",
    "lion": "lion su tu",
    "fish": "fish ca",
    "flower": "flower hoa",
    "tree": "tree cay",
    "plant": "plant thuc vat cay coi",
    "food": "food thuc an mon an",
    "fruit": "fruit trai cay hoa qua",
    "guitar": "guitar dan guitar",
    "musical instrument": "musical instrument nhac cu",
    "drum": "drum trong",
    "umbrella": "umbrella du o che",
    "backpack": "backpack ba lo",
    "handbag": "handbag tui xach",
    "helmet": "helmet non mu bao hiem",
    "hat": "hat non mu",
    "cap": "cap mu luoi trai",
    "tent": "tent leu bat",
    "table": "table ban",
    "chair": "chair ghe",
    "couch": "couch sofa",
    "bed": "bed giuong",
    "television": "television tivi truyen hinh",
    "camera": "camera may anh may quay",
    "mobile phone": "mobile phone dien thoai smartphone",
    "microphone": "microphone micro",
    "cake": "cake banh",
    "bread": "bread banh mi",
    "banana": "banana chuoi",
    "apple": "apple tao",
    "strawberry": "strawberry dau tay"
}


def process_video(video_id: str, lucene_docs_root: Path, objects_root: Path) -> int:
    doc_path = lucene_docs_root / video_id / f"{video_id}-lucene-docs.jsonl.gz"
    if not doc_path.exists():
        return 0

    obj_dir = objects_root / video_id
    has_objs = obj_dir.exists()

    with gzip.open(doc_path, "rt", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    updated_records = []
    for rec in records:
        if "detected_objects" in rec:
            del rec["detected_objects"]

        img_id = rec.get("imgID", "")
        stem = img_id.split("-")[-1] if "-" in img_id else img_id

        obj_file = obj_dir / f"{stem}.json" if has_objs else None
        detected_tags = set()

        if obj_file and obj_file.exists():
            try:
                with open(obj_file, "r", encoding="utf-8") as of:
                    obj_data = json.load(of)
                    entities = obj_data.get("detection_class_entities", []) or obj_data.get("object_class_names", [])
                    scores = obj_data.get("detection_scores", []) or obj_data.get("object_scores", [])

                    for ent, sc in zip(entities, scores):
                        if float(sc) >= 0.25:
                            ent_lower = str(ent).lower().strip()
                            if ent_lower in OBJECT_VI_MAP:
                                detected_tags.add(OBJECT_VI_MAP[ent_lower])
                            else:
                                detected_tags.add(ent_lower)
            except Exception:
                pass

        orig_meta = rec.get("metadata_norm", "")
        if " [objects: " in orig_meta:
            orig_meta = orig_meta[:orig_meta.find(" [objects: ")]

        if detected_tags:
            tag_str = " ".join(sorted(detected_tags))
            rec["metadata_norm"] = orig_meta + f" [objects: {tag_str}]"
        else:
            rec["metadata_norm"] = orig_meta

        updated_records.append(rec)

    with gzip.open(doc_path, "wt", encoding="utf-8") as f:
        for rec in updated_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return len(updated_records)


def main():
    t0 = time.time()
    lucene_docs_root = Path("/home/azunn0801/aic-visione/lucene-documents")
    objects_root = Path("/home/azunn0801/data/AIC2026/objects")

    video_dirs = sorted([d for d in lucene_docs_root.iterdir() if d.is_dir()])
    print(f"Starting clean enrichment for {len(video_dirs)} videos...")

    total_records = 0
    for i, v in enumerate(video_dirs, 1):
        count = process_video(v.name, lucene_docs_root, objects_root)
        total_records += count
        if i % 100 == 0 or i == len(video_dirs):
            print(f"Progress: {i}/{len(video_dirs)} videos ({total_records} keyframes)")

    dt = time.time() - t0
    print(f"Successfully enriched {total_records} records in {dt:.1f}s!")


if __name__ == "__main__":
    main()
