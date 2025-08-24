import os
import time
import googleapiclient
import google_auth_oauthlib
import google.oauth2
from dotenv import load_dotenv

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
load_dotenv()
youtube_api = os.getenv("YT_API")


def get_service():
    """
    created and return service object YouTube API
    """
    creds = None  # token/credentials

    # if token.json (has been login) → load token.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # if not or token expire → create new OAuth flow 
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)  # Open browser for login
        # save token
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # build YouTube API service object
    return build("youtube", "v3", credentials=creds)

def upload_video(file_path, title, description, 
                 category=None, privacy=None):
    """
    Upload YouTube videos
    """
    youtube = get_service()  # get service object

    # load .env if not have use , ""
    category = category or os.getenv("YT_CATEGORY", "24")
    privacy = privacy or os.getenv("YT_PRIVACY", "unlisted")

    #body (data of videos)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category
        },
        "status": {
            "privacyStatus": privacy
        }
    }

    # เตรียมไฟล์วิดีโอที่จะอัปโหลด
    media = MediaFileUpload(file_path)

    # ส่งคำขออัปโหลดไปยัง API
    request = youtube.videos().insert(
        part="snippet,status",  # ต้องตรงกับ fields ใน body
        body=body,
        media_body=media
    )

    print(f"Uploading...")
    response = request.execute()  # รอผลลัพธ์
    video_id = response["id"]     # เก็บ videoId ที่ได้กลับมา

    print(f"✅ Uploaded: https://youtu.be/{video_id}")

    # print(youtube_api)

raw_title = """120FPS 
#shorts #ytshorts #viralshorts #trending #fyp #space 
#universe #galaxy #cosmos #nasa #milkyway #nebula #stars 
#blackhole #interstellar #astrophotography #spacelover 
#astronomy #cosmicbeauty #spaceexploration #amazinguniverse 
#spaceart #beautifulspace #outerspace #spacefacts #science"""

# ลบขึ้นบรรทัด → เหลือเป็นบรรทัดเดียว
clean_title = " ".join(raw_title.split())
# ตัดไม่ให้เกิน 100 ตัว
clean_title = clean_title[:100]

upload_video(
    file_path="src\\outputs\\final_video_.mp4",
    title=clean_title,
    description="120FPS"
)