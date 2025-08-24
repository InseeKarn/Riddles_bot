import requests
import os
import random
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PIXA_API")

queries = ["Space", "Galaxy", "Planet", "Orbit"]
needed = 10
min_needed = 8
history_file = Path("pixabay_seen.json")
unused_file = Path("pixabay_unused.json")
download_dir = Path("src\\bg")
download_dir.mkdir(exist_ok=True)
blacklist_file = Path("pixabay_blocked.json")


def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except:
            return []
    return []

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def download(url, dest_path):
    """Download file from URL in chunk avoid ERROR"""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"✅ Download success!!: {dest_path}")
    except Exception as e:
        print(f"❌ Download Fail!!: {url} — {e}")

def search(exclude_ids):
    query = random.choice(queries)
    print(f"🔍 Finding: {query}")

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": API_KEY,
        "q": query,
        "per_page": 200,
        "video_type": "all",
        "safesearch": "flase"  
    }

    res = requests.get(url, params=params, timeout=15)
    data = res.json()

    vertical_4k, vertical_other, horizontal = [], [], []

    for hit in data.get("hits", []):
        vid_id = hit.get("id")
        if vid_id in exclude_ids:
            continue

        videos = hit.get("videos", {})
        video_data = videos.get("large", {})
        width = video_data.get("width", 0)
        height = video_data.get("height", 0)
        url_video = video_data.get("url")
        downloads = hit.get("downloads", 0)

        if not url_video:
            continue

        if height > width:
            if width >= 2160 and height >= 3840:
                vertical_4k.append((vid_id, url_video, downloads))
            else:
                vertical_other.append((vid_id, url_video, downloads))
        else:
            horizontal.append((vid_id, url_video, downloads))  # Pick horizontal
    
    vertical_4k.sort(key=lambda x: x[2], reverse=True)
    vertical_other.sort(key=lambda x: x[2], reverse=True)
    horizontal.sort(key=lambda x: x[2], reverse=True)

    return (
        [(vid, url) for vid, url, _ in vertical_4k],
        [(vid, url) for vid, url, _ in vertical_other],
        [(vid, url) for vid, url, _ in horizontal]
    )

def run_pixabay():
    blacklist_ids = set(load_json(blacklist_file))
    seen_ids = set(load_json(history_file))
    unused_list = load_json(unused_file)  
    selected = []

    # 🆕 ถ้าประวัติเกินหรือเท่ากับ 40 ให้รีเซ็ตเลย
    if len(seen_ids) >= 40:
        print(f"🔄 Resetting history — was {len(seen_ids)} items")
        seen_ids.clear()
        save_json(history_file, [])  # เขียนไฟล์ให้เป็น list ว่าง

    # 1. ใช้ unused ก่อน
    while unused_list and len(selected) < needed:
        selected.append(unused_list.pop(0))

    # 2. หาใหม่ถ้ายังไม่พอ
    while len(selected) < needed:
        exclude = seen_ids.union({vid for vid, _ in selected}).union(blacklist_ids)

        while True:
            v4k, vother, horiz = search(exclude)
            if v4k or vother or horiz:
                break
            print("⚠️ No videos found for this query. Retrying...")
            # จะสุ่ม query ใหม่เพราะ search() random.choice(queries) อยู่แล้ว

        remaining = needed - len(selected)

        pool_vertical = v4k + vother
        if len(pool_vertical) >= remaining:
            selected.extend(random.sample(pool_vertical, k=remaining))
        else:
            selected.extend(pool_vertical)
            more_need = remaining - len(pool_vertical)

            # เติมด้วย horizontal ถ้ายังไม่ครบ
            if more_need > 0 and horiz:
                take_h = min(more_need, len(horiz))
                selected.extend(random.sample(horiz, k=take_h))

    # 3. โหลดและอัปเดตประวัติ
    for vid_id, v_url in selected:
        seen_ids.add(vid_id)
        filepath = download_dir / f"{vid_id}.mp4"
        download(v_url, filepath)

    save_json(history_file, sorted(list(seen_ids)))
    return True

# if __name__ == "__main__":
#     run_pixabay()