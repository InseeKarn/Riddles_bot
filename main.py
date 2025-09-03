# Dev by InseeKarn

from edit.images import get_one_random_video
from edit.video import build_quiz_clip
from youtube.upload import run_upload
from notify.discord import discord_message
from dotenv import load_dotenv
import os

load_dotenv()

print("PEXELS_API:", bool(os.getenv("PEXELS_API")))
print("YT_API:", bool(os.getenv("YT_API")))
bg_path = "src\\bg\\background.mp4"

if __name__ == "__main__":
    try:
        print("🔍 Starting bot...")
        video_path = get_one_random_video()
        if video_path:
            print("🖼️ Videos step pass")
            build_quiz_clip()
            print("🎬 Video edited")
            video_url = run_upload()
            if video_url:
                print("upload step pass")
                user_id = "304548816907010050"
                discord_message(f"✅ <@{user_id}> Uploaded vids: {video_url} ✅")
            else:
                print("⚠️ Upload failed, skipping Discord notify")
        else:
            print("⚠️ Pexels step failed, skipping video/edit/upload")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")




