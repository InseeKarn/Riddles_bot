from moviepy.editor import *
from moviepy.audio.fx.all import audio_loop
from PIL import Image, ImageDraw
from gtts import gTTS
# from riddles_gen import get_data
from .riddles_gen import get_data

import numpy as np
import moviepy.video.fx.all as afx
import moviepy.config as mpconfig
import os, shutil, platform

if platform.system() == "Windows":
    mpconfig.change_settings({
        "IMAGEMAGICK_BINARY": r"E:\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
    })

def create_clip(hook, bg_video_path, music_file_path):

    os.makedirs("src/tts", exist_ok=True)

    # --- สร้าง TTS ---
    hook_path = "src/tts/hook.mp3"
    comment_path = "src/tts/comment.mp3"

    gTTS(text=hook, lang='en').save(hook_path)
    gTTS(text="Comment your answer", lang='en').save(comment_path)

    speed_factor = 1.3
    hook_clip = AudioFileClip(hook_path).fx(afx.speedx, speed_factor)
    comment_clip = AudioFileClip(comment_path).fx(afx.speedx, speed_factor)

    # --- คำนวณเวลา ---
    hook_duration = hook_clip.duration + 0.1
    comment_duration = comment_clip.duration + 0.1
    end_time = hook_duration + 0.1 + comment_duration

    # --- narration ---
    narration = concatenate_audioclips([
        hook_clip,
        comment_clip
    ])

    # --- พื้นหลัง ---
    bg = VideoFileClip(bg_video_path).resize((1080, 1920))
    if bg.duration < end_time:
        loop_count = int(end_time // bg.duration) + 1
        bg = concatenate_videoclips([bg] * loop_count)
    bg = bg.subclip(0, end_time)

    # --- ข้อความบนจอ ---
    # เว้นช่องว่างระหว่างตัวอักษร

    txt_clip_before = TextClip(
        f"🤔 R i d d l e 🤔\n\n{hook}\n\n",
        fontsize=60,
        color='white',
        size=(950, 1600),
        method='caption',
        align='center'
    ).set_duration(hook_duration)

    txt_clip_after = TextClip(
        f"🤔 R i d d l e 🤔\n\n{hook}\n\n❗ C o m m e n t  y o u r  A n s w e r ❗",
        fontsize=60,
        color='white',
        size=(950, 1600),
        method='caption',
        align='center',
    ).set_start(hook_duration + 0.1).set_duration(comment_duration)

    # --- กล่องพื้นหลังโปร่งแสง ---
    padding = 40
    scale_factor = 0.9
    box_w = int((txt_clip_before.w + padding) * scale_factor)
    box_h = int((txt_clip_before.h + padding) * scale_factor)
    corner_radius = 40
    alpha = 0.35
    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [(0, 0), (box_w, box_h)],
        radius=corner_radius,
        fill=(0, 0, 0, int(255 * alpha))
    )

    bg_box_before = ImageClip(np.array(img)).set_duration(hook_duration)
    bg_box_after = ImageClip(np.array(img)).set_start(hook_duration).set_duration(comment_duration)

    # --- รวมข้อความ + กล่อง ---
    text_with_bg = CompositeVideoClip([
        bg_box_before.set_position('center'),
        txt_clip_before.set_position('center'),
        bg_box_after.set_position('center'),
        txt_clip_after.set_position('center')
    ], size=(1080, 1920))

    # --- เพลงประกอบ ---
    music = AudioFileClip(music_file_path).volumex(0.2).set_duration(end_time)

    # --- รวมเสียงทั้งหมด ---
    final_audio = CompositeAudioClip([narration, music])

    # --- รวมวิดีโอ + เสียง ---
    final_clip = CompositeVideoClip([bg, text_with_bg]).set_audio(final_audio)

    return final_clip

import random
def build_quiz_clip():
    hook = get_data()  # ต้อง return แค่ข้อความ hook
    hook_text = hook[0] if isinstance(hook, list) else hook

    music_dir = "src/musics"
    music_files = [f for f in os.listdir(music_dir) if f.endswith((".mp3"))]

    random_music = os.path.join(music_dir, random.choice(music_files))

    clip = create_clip(
        hook_text,
        bg_video_path="src/bg/background.mp4",
        music_file_path=random_music,
    )

    os.makedirs("src/outputs", exist_ok=True)
    clip.write_videofile("src/outputs/quiz_shorts.mp4", fps=30)
    clip.close()
    shutil.rmtree("src/tts", ignore_errors=True)

    return "src/outputs/quiz_shorts.mp4"


if __name__ == "__main__":
    build_quiz_clip()
