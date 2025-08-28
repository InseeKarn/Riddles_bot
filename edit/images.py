import requests
import os
import random
import json
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

API_KEY = os.getenv("PEXELS_API") or os.environ.get("PEXELS_API")

# Queries ที่จะสุ่มค้น
queries = ["Galaxy"]
needed = 10
download_dir = Path("src/bg")
download_dir.mkdir(exist_ok=True)

# ไฟล์เก็บประวัติ/บล็อก/ยังไม่ได้ใช้
history_file = Path("pexels_seen.json")
unused_file = Path("pexels_unused.json")
blacklist_file = Path("pexels_blocked.json")


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
    url = "https://api.pexels.com/videos/search"
    params = {
        "query": query,
        "per_page": 80,
        "orientation": "portrait"  # แนวตั้ง
    }
    headers = {
        "Authorization": API_KEY
    }

    res = requests.get(url, headers=headers, params=params, timeout=20)
    if res.status_code != 200:
        print(f"❌ Pexels API error: {res.status_code} — {res.text[:200]}")
        return [], [], []

    try:
        data = res.json()
    except ValueError as e:
        print(f"❌ JSON decode error: {e}")
        return [], [], []

    vertical_4k, vertical_other, horizontal = [], [], []

    for vid in data.get("videos", []):
        vid_id = vid.get("id")
        if vid_id in exclude_ids:
            continue

        width = vid.get("width", 0)
        height = vid.get("height", 0)

        # เลือกไฟล์วิดีโอความละเอียดสูงสุด
        video_files = vid.get("video_files", [])
        if not video_files:
            continue
        best_file = max(video_files, key=lambda f: f.get("width", 0))
        url_video = best_file.get("link")

        if not url_video:
            continue

        if height > width:  # แนวตั้ง
            if width >= 2160 and height >= 3840:
                vertical_4k.append((vid_id, url_video))
            else:
                vertical_other.append((vid_id, url_video))
        else:
            horizontal.append((vid_id, url_video))

    return vertical_4k, vertical_other, horizontal


def run_pexels():
    if not API_KEY:
        print("❌ Missing API key. Set PEXELS_API in .env")
        return False

    blacklist_ids = set(load_json(blacklist_file))
    seen_ids = set(load_json(history_file))
    unused_list = load_json(unused_file)

    selected = []

    # รีเซ็ตประวัติถ้าเกิน 40
    if len(seen_ids) >= 40:
        print(f"🔄 Resetting history — was {len(seen_ids)} items")
        seen_ids.clear()
        save_json(history_file, [])

    # ใช้ unused ก่อน
    while unused_list and len(selected) < needed:
        selected.append(unused_list.pop(0))

    attempts = 0
    MAX_ATTEMPTS = 3
    MAX_CLIPS = needed

    while len(selected) < MAX_CLIPS:
        exclude = seen_ids.union({vid for vid, _ in selected}).union(blacklist_ids)
        v4k, vother, horiz = search(exclude)

        if not (v4k or vother or horiz):
            attempts += 1
            if attempts >= MAX_ATTEMPTS:
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

        if not take:
            attempts += 1
            if attempts >= MAX_ATTEMPTS:
                break
            continue

        take = take[:space_left]
        selected.extend(take)
        attempts = 0

    def download_task(i, total, vid_id, url):
        dest_path = download_dir / f"{vid_id}.mp4"
        download(url, dest_path)
        return dest_path

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

    for i, total, path in sorted(results, key=lambda x: x[0]):
        print(f"✅ Download success!! ({i}/{total}): {path}")

    save_json(history_file, sorted(list(seen_ids)))
    save_json(unused_file, unused_list)


if __name__ == "__main__":
    run_pexels()
