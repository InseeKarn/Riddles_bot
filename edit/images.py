import requests
import os
import random
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PEXELS_API")
QUERY = "Pattern"
download_dir = Path("src/bg")
download_dir.mkdir(exist_ok=True)

def download(url, dest_path):
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def get_img():
    url = "https://api.pexels.com/v1/search"
    params = {
        "query": QUERY,
        "per_page": 20,
        "orientation": "portrait"
    }
    headers = {"Authorization": API_KEY}

    res = requests.get(url, headers=headers, params=params, timeout=20)
    res.raise_for_status()
    data = res.json()

    images = data.get("photos", [])
    if not images:
        print("❌ No images found")
        return None

    # randomly select one image
    img = random.choice(images)

    # find better resolution
    img_url = img["src"]["original"]

    dest_path = download_dir / f"background.jpg"
    download(img_url, dest_path)
    print(f"✅ Downloaded: {dest_path}")
    return dest_path

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Missing API key. Set PEXELS_API in .env")
    else:
        get_img()
