from pathlib import Path
from moviepy.editor import *
import numpy as np
import random
import json

download_dir = Path("src/bg")
output_file = Path("src/outputs/final_video_.mp4")
unused_for_edit_file = Path("downloaded_not_edited.json")
music_dir = Path("src/mp3")
music_files = list(music_dir.glob("*.mp3"))

TARGET_W, TARGET_H = 1080, 1920  # 9:16 target AR

def load_unused_for_edit():
    if unused_for_edit_file.exists():
        return set(json.loads(unused_for_edit_file.read_text(encoding="utf-8")))
    return set()

def save_unused_for_edit(data):
    unused_for_edit_file.write_text(json.dumps(sorted(list(data))), encoding="utf-8")

def ensure_vertical_clip(clip):
    """ปรับ clip ให้เป็นแนวตั้ง 9:16 — ถ้ากว้างไปก็ crop, ถ้าแคบไปก็เติมขอบ"""
    target_ar = TARGET_W / TARGET_H
    current_ar = clip.w / clip.h
    
    # resize ให้สูงตรงก่อน
    clip = clip.resize(height=TARGET_H)

    if current_ar > target_ar:
        # กว้างเกิน → crop ซ้ายขวา
        new_width = int(TARGET_H * target_ar)
        return vfx.crop(clip, width=new_width, height=TARGET_H, x_center=clip.w/2, y_center=clip.h/2)
    elif current_ar < target_ar:
        # แคบเกิน → padding ด้านข้าง (ใส่พื้นหลังดำ)
        return clip.on_color(size=(TARGET_W, TARGET_H), color=(0, 0, 0), pos=("center","center"))
    else:
        return clip  # สัดส่วนพอดี

def video_edit():
    unused_ids = load_unused_for_edit()
    video_files = sorted(download_dir.glob("*.mp4"))

    if not video_files:
        print("⚠️ Not found videos in src/bg/")
        return

    clips = []
    used_in_this_run = set()

    for vf in video_files:
        stem = vf.stem
        try:
            with VideoFileClip(str(vf)) as clip:
                # ข้ามคลิปที่สั้นเกินไป
                if clip.duration < 0.5:
                    print(f"⏩ Skip {vf.name} — too short")
                    continue

                clip_len = random.choice([2, 3])
                duration = min(clip_len, clip.duration)
                start_time = random.uniform(0, clip.duration - duration) if clip.duration > duration else 0

                sub = clip.subclip(start_time, start_time + duration)
                sub = ensure_vertical_clip(sub)

                # โหลดเฟรมเก็บในเมมโมรีป้องกัน I/O lag
                frames = [sub.get_frame(t) for t in np.arange(0, sub.duration, 1/clip.fps)]
                sub_mem = ImageSequenceClip(frames, fps=clip.fps)

                clips.append(sub_mem)
                used_in_this_run.add(stem)

        except Exception as e:
            print(f"❌ Cannot {vf} open — {e}")

    if not clips:
        print("⚠️ Do not have videos that can use!!")
        return

    # รวมทุกคลิป
    final = concatenate_videoclips(clips, method="compose")

    # จำกัดความยาวรวม
    MAX_DURATION = 15
    if final.duration > MAX_DURATION:
        final = final.subclip(0, MAX_DURATION)

    # ใส่เพลงสุ่ม
    if music_files:
        chosen_music = random.choice(music_files)
        print(f"🎵 Adding music...: {chosen_music.name}")
        bg_music = AudioFileClip(str(chosen_music))

        if bg_music.duration < final.duration:
            loop_count = int(final.duration // bg_music.duration) + 1
            bg_music = concatenate_audioclips([bg_music] * loop_count)
        bg_music = bg_music.subclip(0, final.duration)

        final = final.set_audio(bg_music)
    else:
        print("⚠️ file .mp3 not found in dir src/mp3 — process with no audio")

    final.write_videofile(
        str(output_file),
        codec="libx264",
        audio_codec="aac",
        fps=120  # ลด fps เพื่อประหยัดขนาดไฟล์และป้องกันปัญหา
    )

    # อัปเดต unused.json
    current_ids = {vf.stem for vf in video_files}
    still_unused = (unused_ids | current_ids) - used_in_this_run
    save_unused_for_edit(still_unused)

    # ลบไฟล์ที่ใช้แล้ว
    for vf in video_files:
        if vf.stem in used_in_this_run:
            vf.unlink()

    print(f"✅ Used {len(used_in_this_run)} vids deleted, remain {len(still_unused)} vids not used")

if __name__ == "__main__":
    video_edit()
