from pathlib import Path
from moviepy.editor import *

import numpy as np
import random
import json

download_dir = Path("src\\bg")
output_file = f"src\\outputs\\final_video_.mp4"
unused_for_edit_file = Path("downloaded_not_edited.json")
music_dir = Path("src/mp3")  
music_files = list(music_dir.glob("*.mp3"))

TARGET_W, TARGET_H = 1080, 1920  # 9:16

def load_unused_for_edit():
    if unused_for_edit_file.exists():
        return set(json.loads(unused_for_edit_file.read_text(encoding="utf-8")))
    return set()

def save_unused_for_edit(data):
    unused_for_edit_file.write_text(json.dumps(sorted(list(data))), encoding="utf-8")

def video_edit():

    unused_ids = load_unused_for_edit()

    # Find mp4 in folder
    video_files = sorted(download_dir.glob("*.mp4"))

    if not video_files:
        print("⚠️ Not found videos in src/bg/")
        exit()

    clips = []
    used_in_this_run = set()

    for vf in video_files:
        stem = vf.stem
        try:
            with VideoFileClip(str(vf)) as clip:
                clip_len = random.choice([2, 3])
                duration = min(clip_len, clip.duration)
                start_time = random.uniform(0, clip.duration - duration) if clip.duration > duration else 0

                sub = clip.subclip(start_time, start_time + duration)
                sub = sub.resize(height=TARGET_H)
                sub = vfx.crop(sub, width=TARGET_W, height=TARGET_H,
                            x_center=sub.w / 2, y_center=sub.h / 2)

                # ✅ All frame save in memory
                frames = [sub.get_frame(t) for t in np.arange(0, sub.duration, 1/clip.fps)]
                sub_mem = ImageSequenceClip(frames, fps=clip.fps)

                clips.append(sub_mem)
                used_in_this_run.add(stem)

        except Exception as e:
            print(f"❌ Cannot {vf} open — {e}")

    if not clips:
        print("⚠️ Do not have videos that can use!!")
        exit()

    # combine vids
    final = concatenate_videoclips(clips, method="compose")
    # Limit duration
    MAX_DURATION = 15
    if final.duration > MAX_DURATION:
        final = final.subclip(0, MAX_DURATION)

    # ===== Random musics =====
    music_files = list(music_dir.glob("*.mp3"))
    if not music_files:
        print("⚠️ file .mp3 not found in dir src/mp3 will process with no audio")
    else:
        chosen_music = random.choice(music_files)
        print(f"🎵 Adding music...: {chosen_music.name}")

        bg_music = AudioFileClip(str(chosen_music))

        # Adjust duration music == final video duration
        if bg_music.duration < final.duration:
            # loop
            loop_count = int(final.duration // bg_music.duration) + 1
            bg_music = concatenate_audioclips([bg_music] * loop_count)
        bg_music = bg_music.subclip(0, final.duration)

        # add audio in final
        final = final.set_audio(bg_music)

    final.write_videofile(
        str(output_file),
        codec="libx264",
        audio_codec="aac",
        fps=120
    )

    # Update unused.json → Delete vid that been use, Add vids id has not been use in json
    current_ids = {vf.stem for vf in video_files}
    still_unused = (unused_ids | current_ids) - used_in_this_run
    save_unused_for_edit(still_unused)

    # Delete file vids
    for vf in video_files:
        if vf.stem in used_in_this_run:
            vf.unlink()

    print(f"✅ Use {len(used_in_this_run)} vids Deleted, "
        f"Remain {len(still_unused)} vids not been use")
    
if __name__ == "__main__":
    video_edit()