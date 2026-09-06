#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import time

URL = "http://localhost:8000/services/core/search"

QUERIES = [
    {
        "id": "query-p2-1-kis",
        "title": "Nhóm 5 người chơi đùa bên con lân vàng, giấu quả bí đỏ, thức dậy gọi lân",
        "clip": "lion dance performer waking up yellow lion stage drama pumpkin",
        "meta": "nam sư ăn bông bí",
        "hint": "L24_V035 (Đoàn Lân Hào Nhựt - Ăn Bông Bí)"
    },
    {
        "id": "query-p2-2-kis",
        "title": "Chụp ảnh tranh tê giác trên tường, kết thúc chụp graffiti 3 chú khỉ trên cầu",
        "clip": "person taking photo of rhino wall painting mural with phone, graffiti of three monkeys on bridge",
        "meta": "graffiti tê giác 3 chú khỉ",
        "hint": "Tin tức 60 Giây (L21 / L22)"
    },
    {
        "id": "query-p2-3-kis",
        "title": "Chú lân vàng nhảy từ trên cao xuống gần mô hình tàu thủy nhỏ màu xanh dương",
        "clip": "yellow lion dance jumping from high pole near blue ship boat model on stage",
        "meta": "lên tàu tháo neo giúp dân",
        "hint": "L24_V014 (Đoàn Lân Tình Nghĩa - Lên Tàu Tháo Neo)"
    },
    {
        "id": "query-p2-4-kis",
        "title": "Hai bạn trẻ treo băng rôn xanh dương, núi mây đường đến trường, 2 em bé áo vàng",
        "clip": "two young people hanging large blue banner mountain clouds road to school two children in yellow shirts",
        "meta": "băng rôn trường học lan tỏa năng lượng",
        "hint": "L30 (Lan tỏa năng lượng tích cực)"
    },
    {
        "id": "query-p2-5-kis",
        "title": "Người áo đỏ nón trắng rưới nước vào mặt, 2 người đi xe đạp áo xanh đuổi theo áo đen cam",
        "clip": "person in red shirt white hat splashing water on face, cyclist in dark blue chasing cyclist in black orange",
        "meta": "cúp truyền hình đua xe đạp",
        "hint": "L23 (Cúp truyền hình HTV 2024)"
    },
    {
        "id": "query-p2-6-kis",
        "title": "2 thanh niên nằm dài trên yên xe máy phóng nhanh, ô tô xanh, 2 vòng tròn đỏ khoanh vùng",
        "clip": "two men lying flat on motorcycle seat speeding dangerously red circle highlight on screen blue car",
        "meta": "nằm trên yên xe máy phóng nhanh",
        "hint": "L21 / L22 (60 Giây giao thông)"
    },
    {
        "id": "query-p2-10-kis",
        "title": "Xào dồi trường màu trắng với bông hẹ dài màu xanh trong chảo",
        "clip": "stir frying white pork intestine with green chives in pan wok",
        "meta": "dồi trường xào bông hẹ",
        "hint": "L26 (Món ngon mỗi ngày)"
    },
    {
        "id": "query-p2-11-kis",
        "title": "Đầu bếp xiên que lăn qua hỗn hợp xanh đỏ băm nhỏ rồi phủ bột trắng trên đĩa",
        "clip": "chef rolling skewered ingredient in chopped green red herbs then coating in white flour powder on plate",
        "meta": "xiên que lăn bột chiên",
        "hint": "L26 (Món ngon mỗi ngày)"
    },
    {
        "id": "query-p2-13-kis",
        "title": "Xào thịt gà ớt đỏ xanh đậu phộng hành tím, tắt lửa cho vỏ chanh nước cốt chanh",
        "clip": "stir frying chicken red green peppers peanuts shallots in pan, adding lemon lime zest and juice pouring plate",
        "meta": "thịt gà chanh ớt đậu phộng",
        "hint": "L26 (Món ngon mỗi ngày)"
    },
    {
        "id": "query-p2-14-kis",
        "title": "Cận cảnh 3 tay đua: 2 áo xanh nón đỏ/trắng, 1 áo vàng, quai mũ nón đỏ có dây trắng lủng lẳng",
        "clip": "close up three cyclists racing, two riders in blue jerseys red white helmets, rider in yellow jersey white strap hanging",
        "meta": "cúp truyền hình",
        "hint": "L23 (Cúp truyền hình HTV 2024)"
    },
    {
        "id": "query-p2-15-kis",
        "title": "Giới thiệu nguyên liệu qua 3 chuyển cảnh: hải sản 1, hải sản 2 nhiều màu, toàn cảnh đĩa nguyên liệu",
        "clip": "overview plate of cooking ingredients seafood vegetables colorful ingredients arranged on table",
        "meta": "nguyên liệu món ngon mỗi ngày",
        "hint": "L26 (Món ngon mỗi ngày)"
    },
    {
        "id": "query-p2-16-kis",
        "title": "2 người phụ nữ làm thủ công trên ván ngựa, phía sau treo 10 thớt gỗ hàng ngang",
        "clip": "two women doing handicraft on wooden bed platform, row of ten wooden chopping boards hanging on wall",
        "meta": "làng nghề thớt gỗ",
        "hint": "L28 / L29 / L27 (Ký sự làng nghề)"
    },
    {
        "id": "query-p2-17-kis",
        "title": "Sân khấu có dòng chữ nổi 3D ánh kim phủ kim tuyến chữ SẮC CỔ...",
        "clip": "stage backdrop with 3D glitter golden letters SAC CO in front of stage",
        "meta": "SẮC CỔ",
        "hint": "L24 / L21 / L30 (Chữ nổi SẮC CỔ)"
    },
    {
        "id": "query-p2-18-kis",
        "title": "Nhóm 4 tay đua rẽ phải vào đường Hồ Tùng Mậu tại giao lộ đèn xanh đếm ngược 13 giây",
        "clip": "cyclists turning right at road intersection green traffic light countdown bicycle race",
        "meta": "Hồ Tùng Mậu Đà Lạt",
        "hint": "L23 (Đua xe đạp chặng Đà Lạt)"
    },
    {
        "id": "query-p2-20-kis",
        "title": "Slide Địa lí: bảng số liệu mạng lưới đô thị VN (3 vùng nhiều đô thị nhất màu đỏ, 2 ít nhất màu xanh)",
        "clip": "geography teacher lecture slide table data urbanization network vietnam red green numbers",
        "meta": "Địa lý dân cư đô thị",
        "hint": "L25_V060 (Môn Địa lý Chuyên đề 4: Địa lý dân cư VN)"
    },
    {
        "id": "query-p2-22-kis",
        "title": "Khứa hải sản trắng vuông góc 2 mặt, cắt thành que vào tô trộn rượu tiêu hạt nêm",
        "clip": "scoring white squid cuttlefish in criss cross pattern with knife cutting into sticks seasoning wine pepper",
        "meta": "mực khứa ca rô cắt que",
        "hint": "L26 (Món ngon mỗi ngày - Mực)"
    },
    {
        "id": "query-p2-24-kis",
        "title": "Về đích tại Quảng Nam, Martin Laas áo xanh buông 2 tay ăn mừng, sau lưng là áo vàng và áo cam",
        "clip": "cyclist in blue jersey letting go of handlebars raising both arms in victory finish line bicycle race yellow orange behind",
        "meta": "Martin Laas chiến thắng chặng Quảng Nam",
        "hint": "L23_V004 (Martin Laas thắng chặng Vĩnh Long - Tam Kỳ)"
    },
    {
        "id": "query-p2-25-kis",
        "title": "Thầy giáo áo sọc ngắn tay góc trái, minh họa cô gái ngồi sofa xám cầm cốc nước nhìn laptop",
        "clip": "male teacher striped shirt gestures bottom left, illustration young woman with glasses sitting on gray sofa laptop",
        "meta": "bí quyết ôn thi",
        "hint": "L25 (Bí quyết ôn thi THPT 2024)"
    },
    {
        "id": "query-p2-26-kis",
        "title": "Slide: nhóm 3D trắng vây quanh nhân vật đỏ, 2 nhân vật hoạt hình thi đấu kéo co sợi dây thừng",
        "clip": "presentation slide 3d white figures surrounding red figure in center, two cartoon men playing tug of war with rope",
        "meta": "quy luật cạnh tranh sản xuất hàng hóa",
        "hint": "L25_V062 (Môn GDCD: Quy luật sản xuất và cạnh tranh)"
    }
]

def search(payload):
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return []

print(f"=== CHẠY AUTO RETRIEVAL CHO TẤT CẢ {len(QUERIES)} CÂU HỎI KIS ĐỢT 2 ===\n")

results_summary = []

for q in QUERIES:
    qid = q["id"]
    title = q["title"]
    print("-" * 80)
    print(f"[*] {qid}: {title}")
    
    # 1. CLIP Search
    payload_clip = {
        "query": json.dumps({"query": [{"textual": q["clip"]}], "parameters": [{"textualMode": "clip-openai"}]}),
        "k": "3",
        "sortbyvideo": "true"
    }
    clip_res = search(payload_clip)
    
    # 2. Metadata Search
    payload_meta = {
        "query": json.dumps({"query": [{"metadata": q["meta"]}], "parameters": [{"textualMode": "metadata"}]}),
        "k": "3",
        "sortbyvideo": "true"
    }
    meta_res = search(payload_meta)
    
    top_clip = [f"{r.get('videoId')} ({r.get('imgId')})" for r in clip_res[:3]]
    top_meta = [f"{r.get('videoId')} ({r.get('imgId')})" for r in meta_res[:3]]
    
    print(f"   - CLIP Top: {top_clip}")
    print(f"   - Meta Top: {top_meta}")
    print(f"   - Gợi ý chuẩn: {q['hint']}")
    
    results_summary.append({
        "id": qid,
        "title": title,
        "hint": q["hint"],
        "clip_top": top_clip,
        "meta_top": top_meta,
        "clip_prompt": q["clip"],
        "meta_query": q["meta"]
    })

with open("/home/azunn0801/aic-visione/AUTO_RETRIEVAL_P2_RESULTS.json", "w", encoding="utf-8") as f:
    json.dump(results_summary, f, ensure_ascii=False, indent=2)

print("\nĐã lưu kết quả hoàn chỉnh vào /home/azunn0801/aic-visione/AUTO_RETRIEVAL_P2_RESULTS.json!")
