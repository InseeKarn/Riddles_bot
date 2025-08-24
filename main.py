from edit.images import run_pixabay
from edit.video import video_edit
from youtube.upload import run_upload
from notify.discord import discord_message

if __name__ == "__main__":
    if run_pixabay():
        video_edit()
        video_url = run_upload()
        user_id = "304548816907010050"
        discord_message(f"✅ <@{user_id}> Uploaded vids: {video_url} ✅")