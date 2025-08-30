import requests
import os
import random
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PEXELS_API")
QUERY = "universe"  # หรือ "space", "nebula"
download_dir = Path("src/bg")
download_dir.mkdir(exist_ok=True)

def download(url, dest_path):
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def get_one_random_video():
    url = "https://api.pexels.com/videos/search"
    params = {
        "query": QUERY,
        "per_page": 20,   # ขอมาเยอะหน่อยเพื่อสุ่ม
        "orientation": "portrait"
    }
    headers = {"Authorization": API_KEY}

    res = requests.get(url, headers=headers, params=params, timeout=20)
    res.raise_for_status()
    data = res.json()

    videos = data.get("videos", [])
    if not videos:
        print("❌ No videos found")
        return None

    # สุ่มเลือกคลิป
    vid = random.choice(videos)
    vid_id = vid["id"]

    # หาไฟล์ที่ความละเอียดสูงสุด
    best_file = max(vid["video_files"], key=lambda f: f.get("width", 0))
    video_url = best_file["link"]

    dest_path = download_dir / f"background.mp4"
    download(video_url, dest_path)
    print(f"✅ Downloaded: {dest_path}")
    return dest_path

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Missing API key. Set PEXELS_API in .env")
    else:
        get_one_random_video()
