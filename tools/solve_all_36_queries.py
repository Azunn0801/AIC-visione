#!/usr/bin/env python3
"""
Comprehensive retrieval and solver script for all 36 Part 2 queries.
Queries VisioNe (CLIP + Metadata Lucene) and Lucene index directly if needed.
"""
import urllib.request
import urllib.parse
import json
import os
import csv

URL = "http://localhost:8000/services/core/search"
FRAME_MAP_PATH = "/home/azunn0801/aic-visione/aic-visione-frame-map.csv"

# Load frame map cache
print("Loading frame map...")
frame_map = {} # (video_id, frame_idx_str) -> row
with open(FRAME_MAP_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        v_id = r["video_id"]
        f_idx = r["frame_idx"]
        frame_map[(v_id, f_idx)] = r
print(f"Loaded {len(frame_map)} frames into map.")

def search_visione(payload):
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error searching: {e}")
        return []

def run_query(clip_prompts, meta_queries, k=5):
    all_results = {}
    
    # 1. CLIP queries
    for p in clip_prompts:
        payload = {
            "query": json.dumps({"query": [{"textual": p}], "parameters": [{"textualMode": "clip-openai"}]}),
            "k": str(k),
            "sortbyvideo": "true"
        }
        res = search_visione(payload)
        for r in res:
            vid = r.get("videoId")
            img = r.get("imgId")
            score = float(r.get("score", 0))
            if vid not in all_results or score > all_results[vid]["score"]:
                all_results[vid] = {"vid": vid, "img": img, "score": score, "source": f"CLIP: {p[:30]}"}
                
    # 2. Metadata queries
    for m in meta_queries:
        payload = {
            "query": json.dumps({"query": [{"metadata": m}], "parameters": [{"textualMode": "metadata"}]}),
            "k": str(k),
            "sortbyvideo": "true"
        }
        res = search_visione(payload)
        for r in res:
            vid = r.get("videoId")
            img = r.get("imgId")
            score = float(r.get("score", 0))
            if vid not in all_results or score > all_results[vid]["score"]:
                all_results[vid] = {"vid": vid, "img": img, "score": score, "source": f"META: {m[:30]}"}
                
    sorted_res = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)
    return sorted_res

# Define query configurations
QUERIES = {
    # --- KIS (26 queries) ---
    "query-p2-1-kis": {
        "title": "Trứng gà đánh tan đổ vào súp, nấm măng cắt sợi, đầu bếp cắt đậu hũ trực tiếp trên nồi",
        "clip": [
            "chef pouring beaten egg into soup pot with shredded mushrooms and bamboo shoots cutting tofu with knife into pot",
            "cutting white tofu with knife directly over cooking soup pot shredded mushrooms",
            "chef pouring yellow beaten eggs into boiling soup pot stirring tofu mushrooms bamboo shoots"
        ],
        "meta": ["trứng gà súp nấm măng đậu hũ", "cắt đậu hũ súp măng nấm"]
    },
    "query-p2-2-kis": {
        "title": "Học sinh mặc đồng phục xếp hàng trước trường cầm bảng số lớp, di chuyển vào hành lang lên cầu thang",
        "clip": [
            "students in uniform lining up in front of school holding class number signs walking into hallway stairs",
            "school students in uniform standing in rows holding class boards teacher guiding students walking upstairs",
            "students holding classroom signs moving into school building corridor staircase"
        ],
        "meta": ["học sinh đồng phục bảng lớp", "học sinh xếp hàng vào lớp"]
    },
    "query-p2-3-kis": {
        "title": "Cho nguyên liệu vào nồi nước dùng: cà rốt cam, nguyên liệu ống nhỏ, rau xanh nấm nâu, đĩa thịt mỏng",
        "clip": [
            "chef adding orange carrots small tube ingredients green vegetables brown mushrooms and sliced meat to boiling pot",
            "boiling soup pot adding orange carrot sliced brown mushrooms green vegetables and thin sliced meat",
            "adding tubular ingredients mushrooms meat vegetables into boiling broth pot"
        ],
        "meta": ["nước dùng cà rốt nấm thịt", "lẩu rau củ nấm thịt"]
    },
    "query-p2-4-kis": {
        "title": "Giáo viên nữ ngồi bên phải giảng Tiếng Anh bảng xanh: 2 ví dụ (bảo tàng tuần trước, đá bóng khi trẻ)",
        "clip": [
            "female English teacher sitting right side green chalkboard grammar used to past tense museum soccer football",
            "female teacher explaining English grammar on green blackboard example sentences formula",
            "English lesson female teacher green board visited museum last week used to play football"
        ],
        "meta": ["tiếng anh used to museum football", "bài giảng tiếng anh thì quá khứ"]
    },
    "query-p2-7-kis": {
        "title": "Giao thông: 2 thanh niên chạy xe bất cẩn trên làn ô tô nguy cơ tai nạn",
        "clip": [
            "two young men riding motorbike recklessly on car lane highway traffic safety violation",
            "two youths on motorcycle driving carelessly on automobile lane dangerous traffic",
            "motorcycle speeding on car lane highway traffic camera"
        ],
        "meta": ["chạy xe làn ô tô", "thanh niên đi xe máy bất cẩn"]
    },
    "query-p2-9-kis": {
        "title": "Người mẫu trang phục kem họa tiết hình học, triển lãm trên cỏ, thủ công búp bê quả cầu vải",
        "clip": [
            "fashion models wearing cream loose outfits colorful geometric patterns outdoor lawn exhibition fabric dolls balls craft",
            "models wearing cream loose clothing colorful patches outdoor lawn craft exhibition handmade dolls fabric balls",
            "outdoor craft exhibition on grass colorful fabric patchwork dolls balls models cream dresses"
        ],
        "meta": ["trang phục màu kem triển lãm búp bê vải", "thời trang họa tiết quả cầu vải"]
    },
    "query-p2-10-kis": {
        "title": "Diễu hành xe lội nước như ô tô cổ điển chạy trên mặt nước kênh qua cầu người dân xem",
        "clip": [
            "amphibious vintage classic cars floating driving on water river canal under bridges crowd watching",
            "amphicar amphibious cars parade driving on canal water under bridge spectators watching on riverbank",
            "classic cars cruising on canal water river parade"
        ],
        "meta": ["xe lội nước diễu hành", "ô tô lội nước kênh"]
    },
    "query-p2-11-kis": {
        "title": "Phụ nữ lấy thành phẩm trắng nở to từ đồ vật đỏ dạng que dính nhau bày trên vật liệu trắng",
        "clip": [
            "woman taking white puffed food from red device adding ingredients white stick shape on white surface",
            "woman making white puffed snacks sticks from red machine container plating on white plate",
            "taking puffed white crispy noodle snack from red pot container"
        ],
        "meta": ["bánh phồng que trắng đồ vật đỏ", "làm bánh sợi que trắng"]
    },
    "query-p2-12-kis": {
        "title": "Đổ chất lỏng từ bát trắng vào chảo đỏ xóc đều bốc khói/lửa màu hồng chuyển sang nồi nhỏ",
        "clip": [
            "pouring liquid from white bowl into red frying pan wok tossing food pink smoke flame effect transferring to small pot",
            "cooking in red pan tossing liquid from white bowl creating pink flame vapor moving food to smaller pot",
            "chef tossing red pan with food and liquid creating pink flame on stove"
        ],
        "meta": ["chảo đỏ bốc khói hồng", "chất lỏng bát trắng chảo đỏ"]
    },
    "query-p2-13-kis": {
        "title": "Hàng trăm chiếc lờ/lợp bắt cá bằng tre đan bên bờ sông miền Tây hàng dừa ghe cần xé",
        "clip": [
            "hundreds of bamboo fish traps stacked along riverbank coconut trees boats mekong delta craft village",
            "bamboo fish traps rows by riverside coconut trees wooden boats bamboo baskets",
            "traditional bamboo fish traps craft village riverside mekong delta"
        ],
        "meta": ["lờ lợp bắt cá tre đan bờ sông", "làng nghề đan lợp cá dừa ghe"]
    },
    "query-p2-15-kis": {
        "title": "Đầu bếp sơ chế nước lạnh để ráo, nhào bột, cho 1 miếng xanh lá + 2 miếng vàng vào chảo đỏ trước khi chiên",
        "clip": [
            "chef kneading flour powder with food, adding one green piece and two yellow pieces to red pan with oil before frying",
            "cooking adding 1 green piece and 2 yellow pieces into red frying pan with cooking oil",
            "chef preparing dough batter then putting green and yellow ingredients into red oil pan"
        ],
        "meta": ["sơ chế bột chảo đỏ miếng xanh vàng", "chiên chảo đỏ nguyên liệu xanh vàng"]
    },
    "query-p2-16-kis": {
        "title": "Đổ nguyên liệu vào nồi thủy tinh, đũa đảo đỏ xanh, đổ 1.5L lỏng, 1/2 mcp muối, 1/2 mcp đường, 2 mcp hạt nêm",
        "clip": [
            "cooking in transparent glass pot stirring red green ingredients with chopsticks adding 1.5L liquid salt sugar bouillon",
            "transparent glass pot on stove chopsticks stirring red food seasoning 1.5L broth spoonfuls",
            "chef cooking in glass pot adding 1.5 liter liquid salt sugar seasoning powder"
        ],
        "meta": ["nồi thủy tinh 1.5L nước muối đường hạt nêm", "nồi thủy tinh đảo đũa"]
    },
    "query-p2-17-kis": {
        "title": "Nguyên liệu chiên sơ cắt 2 nửa không rời, dùng công cụ tách lõi và vỏ, đặt trên công cụ màu trắng",
        "clip": [
            "cutting fried ingredient into two halves not separated using tool to peel core and skin placing on white tool",
            "chef slicing fried food in half peeling core from skin placing on white utensil board",
            "splitting fried food separating skin and core on white tool"
        ],
        "meta": ["cắt 2 nửa tách lõi vỏ", "nguyên liệu chiên sơ tách vỏ"]
    },
    "query-p2-19-kis": {
        "title": "Lân vàng đứng 3 chân trên 3 trụ rồi chân thứ 4, ngoạm cành hoa tím quay lưng, mở đóng hàm 4 nhịp nhả hoa",
        "clip": [
            "yellow lion dance balancing on three high poles grabbing purple flower branch rotating closing jaw 4 times dropping flower",
            "yellow lion dance grabbing purple flower on high poles turns around opening closing mouth dropping flower",
            "lion dance performer in yellow costume holding purple flower on tall pillars"
        ],
        "meta": ["lân vàng hoa tím 4 nhịp", "múa lân cành hoa tím cột trụ"]
    },
    "query-p2-20-kis": {
        "title": "Slide hợp chất hữu cơ: 2 hình biến thể hạt lương thực, sơ đồ phân loại dải tròn dài nối cầu tròn tím",
        "clip": [
            "chemistry lecture slide organic compounds carbohydrates starch amylose amylopectin grains molecular chains purple circles",
            "slide presentation biology chemistry carbohydrates two grain photos molecular structure circular chains bridged by purple",
            "lecture slide starch carbohydrates molecular structure polymer chains purple nodes"
        ],
        "meta": ["hợp chất hữu cơ tinh bột dải phân tử tím", "bài giảng hóa học carbohydrate tinh bột"]
    },
    "query-p2-22-kis": {
        "title": "Phương tiện bay điện eVTOL thử nghiệm trên khuôn viên vườn hình học kiến trúc cổ Tây Âu khung tròn lớn",
        "clip": [
            "electric flying vehicle eVTOL flying test over large palace gardens geometric green maze historic European architecture large circular frame",
            "electric aerial vehicle flying drone over classical European palace geometric garden circular ring frame",
            "eVTOL flying taxi test flight over historic chateau gardens Europe"
        ],
        "meta": ["thiết bị bay thử nghiệm châu âu", "xe bay điện vườn tây âu"]
    },
    "query-p2-23-kis": {
        "title": "3 cặp trâu nước đua trên ruộng bùn Đông Nam Á, sau đó 1 cặp trâu trắng chạy đua",
        "clip": [
            "three pairs of water buffalo racing in muddy field Southeast Asia then pair of white albino buffalo racing",
            "water buffalo race in mud field riders jockey pair of white buffalos racing mud splash",
            "buffalo racing festival mud field white buffalo pair racing"
        ],
        "meta": ["đua trâu ruộng bùn trâu trắng", "lễ hội đua trâu đông nam á"]
    },
    "query-p2-25-kis": {
        "title": "Vá nhúng thịt mỏng vào nồi nước sôi, cho vào tô sợi trắng cà chua, chan nước dùng nóng",
        "clip": [
            "chef using strainer ladle blanching thin meat slices in boiling pot putting meat into bowl with white noodles tomatoes pouring hot broth",
            "blanching thin beef slices in boiling broth placing in noodle bowl with tomatoes ladling soup",
            "putting blanched meat tomato white noodles in bowl pouring hot broth soup"
        ],
        "meta": ["nhúng thịt tô sợi trắng cà chua chan nước", "bún cà chua thịt bò"]
    },
    "query-p2-26-kis": {
        "title": "Bài giảng hình học không gian: đường xiên qua hình phẳng, 2 hình phẳng giao nhau, điểm vuông góc, khối tứ diện",
        "clip": [
            "mathematics geometry lecture spatial geometry diagrams line intersecting plane perpendicular line tetrahedron dashed lines",
            "math teacher spatial geometry 3d shapes planes intersecting perpendicular line to plane 4 vertex tetrahedron",
            "geometry lecture slides plane line intersection tetrahedron 3d geometry"
        ],
        "meta": ["hình học không gian tứ diện vuông góc", "bài giảng toán hình học không gian"]
    },
    "query-p2-28-kis": {
        "title": "Phỏng vấn phụ nữ đeo kính gọng đen ôm bao đồ quần áo màu trắng logo xanh lá cây",
        "clip": [
            "interview woman wearing black frame glasses holding white bag clothes green logo surrounded by clothing bags",
            "close up woman wearing black eyeglasses holding white sack bag with green logo charity donations",
            "interview woman with glasses hugging white bag green logo"
        ],
        "meta": ["phụ nữ đeo kính ôm bao đồ logo xanh lá", "từ thiện bao đồ logo xanh lá"]
    },
    "query-p2-29-kis": {
        "title": "Múc canh từ nồi sang tô nhỏ đặt trên vải sọc trắng khay gỗ (2 lần múc)",
        "clip": [
            "ladling soup from cooking pot into small bowl placed on striped white cloth on wooden tray twice",
            "chef serving soup with ladle into bowl on striped cloth wooden tray",
            "ladling soup pot to small bowl striped fabric wooden tray"
        ],
        "meta": ["múc canh tô nhỏ vải sọc trắng khay gỗ", "múc canh khay gỗ 2 lần"]
    },
    "query-p2-30-kis": {
        "title": "Phất cờ về đích đua xe đạp quanh hồ, đoàn cua đường cây, người cầm đt tay trái gậy quay tay phải",
        "clip": [
            "person waving finish flag bicycle race around lake cyclists turning corner trees bystander holding phone and camera selfie stick",
            "cycling race around lake finish flag pack turning corner spectator holding smartphone left hand selfie stick right hand",
            "cyclists race corner shady trees person holding selfie stick phone recording"
        ],
        "meta": ["đua xe đạp quanh hồ phất cờ", "gậy quay điện thoại đoàn đua xe đạp"]
    },
    "query-p2-31-kis": {
        "title": "Bạn trẻ tóc sáng màu người nước ngoài ngồi xếp bằng gói bánh lá, quạt máy cánh xanh lá cây",
        "clip": [
            "young blond light haired foreigner sitting cross legged wrapping traditional leaf cakes with locals green blade electric fan",
            "blond foreign tourist sitting on floor wrapping Vietnamese rice cakes leaf package green fan in room",
            "foreign youth sitting cross legged wrapping banh chung banh tet green electric fan"
        ],
        "meta": ["người nước ngoài gói bánh quạt xanh lá", "tóc sáng màu gói bánh lá quạt xanh"]
    },
    "query-p2-32-kis": {
        "title": "Hai mẹ con cầm điện thoại trò chuyện, người con phỏng vấn, phụ nữ da đen bước qua phía sau",
        "clip": [
            "mother and child holding smartphone talking, child interviewed on camera, black woman walking past in background",
            "two people mother child holding phone talking, interview young person, black woman walks by in background",
            "interview young person indoor black woman walking behind"
        ],
        "meta": ["hai mẹ con điện thoại phỏng vấn phụ nữ da đen", "phỏng vấn con mẹ điện thoại"]
    },
    "query-p2-33-kis": {
        "title": "Slow motion flycam nước rút 2 tay đua dẫn đầu, tay đua mũ đen đuối sức thua tay đua mũ trắng",
        "clip": [
            "aerial drone flycam slow motion sprint finish two cyclists cyclist in black helmet losing to cyclist in white helmet",
            "top down drone view sprint finish bicycle race rider black helmet vs rider white helmet",
            "flycam slow motion sprint cycling black helmet white helmet finish line"
        ],
        "meta": ["flycam nước rút mũ đen mũ trắng", "sprint đua xe đạp flycam"]
    },
    "query-p2-36-kis": {
        "title": "Camera lia bàn làm việc, ảnh bắt tay Bác Hồ, nghệ nhân vẽ lại chân dung bút đặc biệt chất liệu đặc biệt",
        "clip": [
            "camera panning on desk photo shaking hands with Ho Chi Minh artisan drawing portrait special pyrography pen unique material",
            "artisan burning pyrography pen drawing portrait from photo of handshake with President Ho Chi Minh",
            "desk pan photo shaking hand Bac Ho artist drawing portrait special pen wood leaf"
        ],
        "meta": ["bắt tay Bác Hồ nghệ nhân vẽ bút đặc biệt", "tranh chân dung Bác Hồ nghệ nhân"]
    },

    # --- Q&A (8 queries) ---
    "query-p2-5-qa": {
        "title": "Ôn tập Địa lí: giới thiệu vùng kinh tế, vị trí, lãnh thổ, bản đồ khí hậu VN -> vùng gồm bao nhiêu tỉnh thành?",
        "clip": [
            "male geography teacher standing left side lecture slide map economic region climate map vietnam provinces",
            "geography lecture vietnam economic regions map climate provinces",
            "teacher standing left slide economic geography vietnam climate map"
        ],
        "meta": ["địa lí vùng kinh tế bản đồ khí hậu", "ôn thi tốt nghiệp thpt địa lí vùng kinh tế"]
    },
    "query-p2-6-qa": {
        "title": "Ôn tập Ngữ văn: hướng dẫn chấm điểm mở thân kết bài, phân tích nhân vật, tác giả gắn bó miền núi nào?",
        "clip": [
            "male literature teacher standing left side lecture computer screen grading guide essay structure author ethnic mountainous region",
            "male teacher literature lecture slide essay rubric analysis of literary character",
            "Ngữ văn ôn thi tốt nghiệp THPT tác giả miền núi"
        ],
        "meta": ["ngữ văn hướng dẫn chấm bài nghị luận văn học", "ôn thi ngữ văn tác giả miền núi"]
    },
    "query-p2-8-qa": {
        "title": "Phỏng vấn người sưu tầm game cảm hứng từ đồ chơi của bà, dòng chữ neon phát sáng là gì?",
        "clip": [
            "interview man collecting retro video games grandmother toy glowing neon sign on wall",
            "video game collector interview illuminated glowing neon letters sign background",
            "interview video game collection glowing neon word"
        ],
        "meta": ["sưu tầm game đồ chơi của bà đèn neon", "bộ sưu tập game neon"]
    },
    "query-p2-14-qa": {
        "title": "Bé gái áo bơi hoa lá trả lời phỏng vấn cạnh hồ bơi, bơi đội mũ tím -> bé sắp lên lớp mấy (1 chữ số)?",
        "clip": [
            "little girl floral swimsuit interview swimming pool swimming purple swim cap",
            "interview young girl in floral swimsuit next to pool swimming with purple cap",
            "swimming lesson girl floral swim suit purple swimming cap interview"
        ],
        "meta": ["bé gái áo bơi hoa lá mũ bơi tím", "học bơi hồ bơi phỏng vấn bé gái"]
    },
    "query-p2-18-qa": {
        "title": "Lớp học: Sư cô quan sát bé áo xanh lá, vở Toán, cô giáo áo hồng đứng lớp chính -> giáo viên chính trường tiểu học nào?",
        "clip": [
            "buddhist nun in classroom watching boy in green shirt math notebook female teacher pink shirt",
            "classroom buddhist nun helping student boy green shirt teacher in pink dress math notebook",
            "lớp học tình thương sư cô cô giáo áo hồng vở toán"
        ],
        "meta": ["sư cô lớp học áo hồng bé áo xanh", "lớp học tình thương sư cô giáo viên tiểu học"]
    },
    "query-p2-24-qa": {
        "title": "Đầu bếp chuẩn bị miếng cam (cá hồi/thịt), băm gia vị tách hạt nêm nước tương -> lượng nước tương là bao nhiêu?",
        "clip": [
            "chef seasoning orange salmon fillet chopping herbs pouring soy sauce measurement",
            "cooking orange meat fish seasoning herbs sprinkling soy sauce tablespoon teaspoon",
            "chef marinating salmon fish herbs soy sauce recipe"
        ],
        "meta": ["nước tương cá hồi miếng màu cam", "gia vị nước tương món ngon mỗi ngày"]
    },
    "query-p2-27-qa": {
        "title": "2 người nắn bột dẹt: 1 trắng 1 màu khác, đặt nhân cuộn lại trên lá nhỏ dĩa -> trên dĩa có mấy màu bột khác nhau?",
        "clip": [
            "two people flattening dough balls one white one colored wrapping filling small leaf plate different dough colors",
            "making traditional cakes flattening dough wrapping filling placing on small leaves colorful dough plate",
            "nặn bánh bột trắng màu lá chuối đĩa"
        ],
        "meta": ["nặn bột bánh màu trắng lá nhỏ dĩa", "làm bánh dĩa mấy màu bột"]
    },
    "query-p2-35-qa": {
        "title": "Giải đề THPTQG 2018 tại nhóm X (4 câu trắc nghiệm 4 đáp án A B C D đều chứa số 0) -> X là số mấy?",
        "clip": [
            "teacher solving 2018 national exam multiple choice questions with number 0 ABCD group X",
            "slide lecture solving THPTQG 2018 exam questions options containing number 0",
            "giải đề thi THPT quốc gia 2018 nhóm câu hỏi"
        ],
        "meta": ["giải đề THPTQG 2018", "đề thi THPTQG 2018 câu trắc nghiệm"]
    },

    # --- TRAKE (2 queries) ---
    "query-p2-21-trake": {
        "title": "Món tôm sốt cam (E1: trộn xốt cam+vỏ cam, E2: cắt đầu tôm, E3: con tôm đầu tiên chạm đĩa, E4: tép cam thứ 4 xếp đĩa)",
        "clip": [
            "chef cooking shrimp with orange sauce slicing orange zest cutting shrimp head plating shrimp orange slices",
            "tôm sốt cam cooking shrimp orange dressing plating shrimp",
            "shrimp with orange slices culinary dish"
        ],
        "meta": ["tôm sốt cam", "tôm xốt nước cam vỏ cam"]
    },
    "query-p2-34-trake": {
        "title": "Lân đỏ biểu diễn trên trụ (E1: treo 2 chân trước vào 2 trụ gần cuối, E2: đứng thẳng co 1 chân trước, E3: ngoảnh mặt ngược lại, E4: ngậm thanh trụ)",
        "clip": [
            "red lion dance performing high poles balancing on pillars hanging front legs",
            "red lion dance acrobatic high pole performance biting pillar standing on one leg",
            "múa lân mai hoa thung lân đỏ cọc trụ"
        ],
        "meta": ["lân đỏ mai hoa thung", "múa lân lân đỏ cột trụ"]
    }
}

print(f"\nProcessing all {len(QUERIES)} queries...")
results = {}

for qid, qdata in QUERIES.items():
    print(f"\n>>> Searching {qid}: {qdata['title'][:60]}...")
    top_matches = run_query(qdata["clip"], qdata["meta"], k=5)
    results[qid] = {
        "title": qdata["title"],
        "top_matches": top_matches[:5]
    }
    for i, m in enumerate(top_matches[:3]):
        print(f"   [{i+1}] {m['vid']} (img: {m['img']}) score={m['score']:.4f} via {m['source']}")

with open("/home/azunn0801/aic-visione/ALL_36_RETRIEVAL_RAW.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nSaved raw search results to /home/azunn0801/aic-visione/ALL_36_RETRIEVAL_RAW.json")
