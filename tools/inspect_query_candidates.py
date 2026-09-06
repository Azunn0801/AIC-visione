#!/usr/bin/env python3
"""
Inspect query candidates, search Lucene OCR text, and extract keyframes for visual verification.
"""
import urllib.request
import urllib.parse
import json
import os
import glob
import csv

URL = "http://localhost:8000/services/core/search"
FRAME_MAP_PATH = "/home/azunn0801/aic-visione/aic-visione-frame-map.csv"
SELECTED_FRAMES_DIR = "/home/azunn0801/aic-visione/selected-frames"
OCR_DIR = "/home/azunn0801/aic-visione/ocr-results"

# Load frame map
frame_map = {} # (video_id, img_id) -> row
with open(FRAME_MAP_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        vid = r["video_id"]
        img = r["visione_id"].split("/")[-1].replace(".jpg", "").replace(".webp", "").replace(".png", "")
        frame_map[(vid, img)] = r

def search(payload):
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return []

def search_clip(query, k=10):
    payload = {
        "query": json.dumps({"query": [{"textual": query}], "parameters": [{"textualMode": "clip-openai"}]}),
        "k": str(k),
        "sortbyvideo": "true"
    }
    return search(payload)

def search_meta(query, k=10):
    payload = {
        "query": json.dumps({"query": [{"metadata": query}], "parameters": [{"textualMode": "metadata"}]}),
        "k": str(k),
        "sortbyvideo": "true"
    }
    return search(payload)

def get_video_ocr(video_id):
    ocr_file = os.path.join(OCR_DIR, f"{video_id}.json")
    if os.path.exists(ocr_file):
        with open(ocr_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def list_video_frames(video_id):
    vdir = os.path.join(SELECTED_FRAMES_DIR, video_id)
    if os.path.exists(vdir):
        frames = sorted(os.listdir(vdir))
        return frames
    return []

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        q = " ".join(sys.argv[2:])
        if mode == "clip":
            res = search_clip(q, k=10)
            for r in res:
                print(r)
        elif mode == "meta":
            res = search_meta(q, k=10)
            for r in res:
                print(r)
        elif mode == "ocr":
            data = get_video_ocr(q)
            print(f"OCR count: {len(data)}")
            for k, v in list(data.items())[:20]:
                print(k, v)
