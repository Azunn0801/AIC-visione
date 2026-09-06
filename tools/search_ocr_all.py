#!/usr/bin/env python3
import gzip
import json
import glob
import sys
import re

def search_ocr(query, max_results=30):
    files = sorted(glob.glob("/home/azunn0801/aic-visione/ocr-results/*-ocr.jsonl.gz"))
    query_lower = query.lower()
    matches = []
    
    for fpath in files:
        vid = fpath.split("/")[-1].replace("-ocr.jsonl.gz", "")
        with gzip.open(fpath, "rt", encoding="utf-8") as gz:
            for line in gz:
                try:
                    d = json.loads(line.strip())
                    text = d.get("ocr_joined", "").lower()
                    if query_lower in text:
                        matches.append({
                            "video_id": vid,
                            "imgID": d.get("imgID"),
                            "stem": d.get("stem"),
                            "ocr": d.get("ocr_joined")
                        })
                        if len(matches) >= max_results:
                            return matches
                except:
                    pass
    return matches

if __name__ == "__main__":
    q = " ".join(sys.argv[1:])
    res = search_ocr(q)
    print(f"Found {len(res)} matches for '{q}':")
    for r in res[:20]:
        print(f"[{r['video_id']}] {r['imgID']} -> {r['ocr']}")
