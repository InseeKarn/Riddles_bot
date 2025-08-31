import requests
import json

API_URL = "https://riddles-api.vercel.app/random"

def get_data():
    # ดึง riddle จาก API
    response = requests.get(API_URL)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch riddle: {response.status_code}")
    
    data = response.json()
    hook = data.get("riddle", "ไม่มีคำถาม")
    answer = data.get("answer", "ไม่ทราบ")

    return [hook, answer]

if __name__ == "__main__":
    riddle = get_data()
    print(json.dumps(riddle, ensure_ascii=False, indent=2))
