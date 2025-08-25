import requests
import os
import random
import json
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

load_dotenv()

API_KEY = os.getenv("PIXA_API") or os.environ.get("PIXA_API")

queries = ["Space", "Galaxy", "Planet", "Orbit"]
queries_pool = random.sample(queries, len(queries))
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

def download(url, dest_path, index=None, total=None):
    """Download file from URL in chunk avoid ERROR"""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        raise RuntimeError(f"Download Fail: {url} — {e}")

def search(exclude_ids):
    query = random.choice(queries)
    print(f"🔍 Finding: {query}")
    print("DEBUG API KEY SET:", bool(API_KEY))
    url = "https://pixabay.com/api/videos/"
    params = {
        "key": API_KEY,
        "q": query,
        "per_page": 200,
        "video_type": "all",
        "safesearch": "flase"  
    }

    res = requests.get(url, params=params, timeout=15)
    if res.status_code != 200:
        print(f"❌ Pixabay API error: {res.status_code} — {res.text[:200]}")
        return [], [], []

    try:
        data = res.json()
    except ValueError as e:
        print(f"❌ JSON decode error: {e} — content preview: {res.text[:200]}")
        return [], [], []

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


blacklist_ids = set(load_json(blacklist_file))
seen_ids = set(load_json(history_file))
unused_list = load_json(unused_file)

def run_pixabay():

    if not API_KEY:
        print("❌ Missing API key. Set PIXABAY_API_KEY or PIXA_API in .env")
        return False
    
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
    attempts = 0
    MAX_ATTEMPTS_IF_NOT_FULL = 2
    MAX_CLIPS = 10  # เพดานสูงสุด

    while len(selected) < MAX_CLIPS:
        exclude = seen_ids.union({vid for vid, _ in selected}).union(blacklist_ids)

        v4k, vother, horiz = search(exclude)
        if not (v4k or vother or horiz):
            attempts += 1
            print(f"⚠️ No videos found — skipping ({attempts}/{MAX_ATTEMPTS_IF_NOT_FULL})")
            if attempts >= MAX_ATTEMPTS_IF_NOT_FULL:
                break
            continue

        space_left = MAX_CLIPS - len(selected)
        pool_vertical = v4k + vother
        take = []

        if len(pool_vertical) >= space_left:
            take = random.sample(pool_vertical, k=space_left)
        else:
            take = pool_vertical[:]
            more_need = space_left - len(pool_vertical)
            if more_need > 0 and horiz:
                take += random.sample(horiz, k=min(more_need, len(horiz)))

        # ถ้าไม่เจอเพิ่ม ก็นับความพยายาม
        if not take:
            attempts += 1
            if attempts >= MAX_ATTEMPTS_IF_NOT_FULL:
                break
            continue

        # เติมคลิปโดยล็อกไม่ให้เกินเพดาน
        take = take[:space_left]
        selected.extend(take)

        # ถ้ามีเพิ่ม → ล้างตัวนับ เพราะถือว่าหาเจอ
        attempts = 0

        if len(selected) >= MAX_CLIPS:
            break

    def download_task(i, total, vid_id, url):
        dest_path = download_dir / f"{vid_id}.mp4"
        download(url, dest_path)
        return dest_path
    
    # 3. โหลดและอัปเดตประวัติ (แบบ parallel)
    total_files = len(selected)
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_info = {
            executor.submit(download_task, i, total_files, vid_id, v_url): (i, total_files)
            for i, (vid_id, v_url) in enumerate(selected, start=1)
        }
        seen_ids.update(vid_id for vid_id, _ in selected)

        for future in as_completed(future_to_info):
            i, total = future_to_info[future]
            try:
                path = future.result()
                results.append((i, total, path))
            except Exception as e:
                results.append((i, total, f"Fail: {e}"))

    # เรียงตาม i ก่อนแสดงผล
    for i, total, path in sorted(results, key=lambda x: x[0]):
        print(f"✅ Download success!! ({i}/{total}): {path}")

    save_json(history_file, sorted(list(seen_ids)))
    save_json(unused_file, unused_list)  # ถ้ามี unused_list เหลือ
    return True

if __name__ == "__main__":
    run_pixabay()