from edit.images import run_pixabay
from edit.video import video_edit
from youtube.upload import run_upload
from notify.discord import discord_message
from dotenv import load_dotenv
import sys, os
load_dotenv()

def safe_run_pixabay():
    try:
        return run_pixabay()
    except Exception as e:
        print(f"❌ run_pixabay() failed: {e}")
        return False

def safe_run_upload():
    try:
        return run_upload()
    except Exception as e:
        print(f"❌ run_upload() failed: {e}")
        return None

print("PIXA_API:", bool(os.getenv("PIXA_API")))
print("YT_API:", bool(os.getenv("YT_API")))

if __name__ == "__main__":
    try:
        print("🔍 Starting bot...")
        if safe_run_pixabay():
            print("🖼️ Image step passed")
            video_edit()
            print("🎬 Video edited")
            video_url = safe_run_upload()
            if video_url:
                user_id = "304548816907010050"
                discord_message(f"✅ <@{user_id}> Uploaded vids: {video_url} ✅")
            else:
                print("⚠️ Upload failed, skipping Discord notify")
        else:
            print("⚠️ Pixabay step failed, skipping video/edit/upload")

        sys.exit(0)  # ✅ จบด้วย success เสมอ

    except Exception as e:
        print(f"❌ Unexpected error: {e}")