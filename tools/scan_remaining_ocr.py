#!/usr/bin/env python3
"""
Search OCR and metadata for the remaining 18 queries across all 874 videos.
"""
import glob
import gzip
import json
import os
import re

OCR_DIR = "/home/azunn0801/aic-visione/ocr-results"

# Queries and target keywords
TARGETS = {
    "query-p2-2-kis": ["bảng tên lớp", "khai giảng", "lễ khai giảng", "xếp hàng", "vào lớp", "lớp 1", "lớp 6", "lớp 10", "đồng phục"],
    "query-p2-3-kis": ["nước dùng", "cà rốt", "nấm", "thịt bò", "thịt heo", "lẩu", "món ngon mỗi ngày"],
    "query-p2-9-kis": ["hình học", "họa tiết", "búp bê", "trình diễn", "thời trang", "bộ sưu tập", "người mẫu"],
    "query-p2-11-kis": ["bánh que", "nở to", "món ăn vặt", "bánh phồng", "chiên giòn", "que dính"],
    "query-p2-12-kis": ["bốc khói", "chảo đỏ", "lửa hồng", "nồi nhỏ", "bát trắng"],
    "query-p2-15-kis": ["nhào bột", "xanh lá", "màu vàng", "chảo đỏ", "chiên bánh"],
    "query-p2-16-kis": ["1.5L", "1,5 lít", "1.5 lít", "1/2 muỗng", "1/2m", "muối", "đường", "hạt nêm", "nồi thủy tinh"],
    "query-p2-17-kis": ["chiên sơ", "tách lõi", "cắt đôi", "cắt 2 nửa", "vỏ"],
    "query-p2-19-kis": ["lân vàng", "mai hoa thung", "cành hoa", "nhả hoa", "ngậm hoa", "hoa tím"],
    "query-p2-20-kis": ["lương thực", "tinh bột", "cacbohidrat", "gluxit", "monosaccarit", "polisaccarit", "bắc cầu", "hóa học 12", "hóa học"],
    "query-p2-25-kis": ["nhúng thịt", "nước sôi", "tô bún", "bún bò", "bún cà chua", "canh bún", "chan nước dùng"],
    "query-p2-28-kis": ["bao đồ", "quần áo", "từ thiện", "kính gọng đen", "logo xanh"],
    "query-p2-29-kis": ["múc canh", "khay gỗ", "vải sọc", "tô nhỏ"],
    "query-p2-30-kis": ["xe đạp", "phất cờ", "quanh hồ", "gậy quay", "về đích", "cúp truyền hình", "cuộc đua"],
    "query-p2-31-kis": ["gói bánh", "người nước ngoài", "quạt máy", "quạt xanh", "bánh tét", "bánh chưng", "bánh ít"],
    "query-p2-32-kis": ["phụ nữ da đen", "mẹ con", "điện thoại", "trò chuyện"],
    "query-p2-33-kis": ["mũ đen", "mũ trắng", "nước rút", "về đích", "slow motion", "tay đua"],
    "query-p2-36-kis": ["bác hồ", "bắt tay", "nghệ nhân", "vẽ chân dung", "bút đặc biệt"]
}

ocr_files = sorted(glob.glob(os.path.join(OCR_DIR, "*-ocr.jsonl.gz")))
print(f"Scanning {len(ocr_files)} OCR files...")

hits = {k: [] for k in TARGETS}

for fpath in ocr_files:
    vid = os.path.basename(fpath).replace("-ocr.jsonl.gz", "")
    try:
        with gzip.open(fpath, "rt", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                text = data.get("ocr_joined", "").lower()
                stem = data.get("stem", "")
                
                # Check specific queries
                # 16: 1.5L / 1,5L or salt/sugar/bouillon
                if ("1.5" in text or "1,5" in text) and ("muối" in text or "nêm" in text or "đường" in text):
                    hits["query-p2-16-kis"].append((vid, stem, text[:120]))
                
                # 20: Chemistry lecture on grains / carbs
                if any(w in text for w in ["tinh bột", "cacbohi", "gluxit", "polisaccarit", "hóa học 12"]):
                    hits["query-p2-20-kis"].append((vid, stem, text[:120]))
                    
                # 36: Bac Ho handshake / artist portrait
                if "bác hồ" in text or "chân dung" in text or "nghệ nhân" in text:
                    hits["query-p2-36-kis"].append((vid, stem, text[:120]))
                    
                # 30 & 33: Bike races
                if any(w in text for w in ["cuộc đua", "tay đua", "nước rút", "xe đạp", "áo vàng", "về đích"]):
                    if "nước rút" in text or "về đích" in text:
                        hits["query-p2-33-kis"].append((vid, stem, text[:120]))
                        hits["query-p2-30-kis"].append((vid, stem, text[:120]))
                        
                # 31: Foreigner wrapping cakes
                if "gói bánh" in text or "bánh tét" in text or "bánh chưng" in text:
                    hits["query-p2-31-kis"].append((vid, stem, text[:120]))
                    
                # 2: School students line up
                if "khai giảng" in text or "năm học mới" in text or "đồng phục" in text:
                    hits["query-p2-2-kis"].append((vid, stem, text[:120]))
                    
                # 28: Charity clothes
                if "quần áo" in text and ("từ thiện" in text or "miễn phí" in text or "quyên góp" in text):
                    hits["query-p2-28-kis"].append((vid, stem, text[:120]))
    except Exception as e:
        continue

print("\n--- SUMMARY OF DETECTIONS ---")
for qid, results in hits.items():
    if results:
        print(f"\n{qid} (Total hits: {len(results)}):")
        # Unique vids
        vids = {}
        for vid, stem, t in results:
            if vid not in vids:
                vids[vid] = []
            vids[vid].append((stem, t))
        for vid, items in list(vids.items())[:5]:
            print(f"  {vid}: {len(items)} hits (e.g. stem {items[0][0]}: {items[0][1]})")

with open("/home/azunn0801/aic-visione/REMAINING_OCR_HITS.json", "w", encoding="utf-8") as f:
    json.dump(hits, f, ensure_ascii=False, indent=2)
