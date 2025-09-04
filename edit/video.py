from moviepy.editor import *
from gtts import gTTS
# from riddles_gen import get_data # Use to test on local
from .riddles_gen import get_data # Use to run on Github workflows

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
    your_answer = "src/tts/your answer.mp3"
    comment_path2 = "src/tts/comment.mp3"

    gTTS(text="answer Smart enough to solve this?", lang='en').save(your_answer)
    gTTS(text="Comment your", lang='en').save(comment_path2)
    gTTS(text=hook, lang='en').save(hook_path)
    

    speed_factor = 1.3
    hook_clip = AudioFileClip(hook_path).fx(afx.speedx, speed_factor)
    your_answer_clip = AudioFileClip(your_answer).fx(afx.speedx, speed_factor)
    comment_clip = AudioFileClip(comment_path2).fx(afx.speedx, speed_factor)

    # --- คำนวณเวลา ---
    your_answer_duration = your_answer_clip.duration
    hook_duration = hook_clip.duration + 0.1
    comment_duration = comment_clip.duration
    end_time = your_answer_duration + hook_duration + comment_duration

    # --- narration ---
    narration = concatenate_audioclips([
        your_answer_clip,
        hook_clip,
        comment_clip
    ])

    # --- พื้นหลัง ---
    bg = VideoFileClip(bg_video_path).resize((1080, 1920))
    if bg.duration < end_time:
        loop_count = int(end_time // bg.duration) + 1
        bg = concatenate_videoclips([bg] * loop_count)
    bg = bg.subclip(0, end_time)
    w, h = bg.size

    # --- ข้อความบนจอ ---
    font = "src/fonts/bold_font.ttf"
    txt_title = TextClip(
        "Riddle Time!",
        fontsize=70,
        font=font,
        color='yellow',
        method='caption',
        align='center',
        size=(900, None)
    ).set_duration(end_time)

    txt_smart = TextClip(
        "Smart enough to solve this?!",
        fontsize=70,
        font=font,
        color='magenta',
        method='label',
        align='center',
        size=(950, None)
    ).set_duration(3)

    txt_hook = TextClip(
        hook,
        fontsize=60,
        font=font,
        color='white',
        method='caption',
        align='center',
        size=(950, None)
    ).set_duration(end_time)

    txt_comment = TextClip(
        "Comment your answer!",
        fontsize=65,
        font=font,
        color='red',
        method='caption',
        align='center',
        size=(950, None)
    ).set_duration(end_time)

    # --- GIF แทน Emoji ---
    gif_title = VideoFileClip("src/gifs/thinking.gif").set_duration(end_time).resize(height=200)
    gif_comment = VideoFileClip("src/gifs/comment-3-5148.gif").set_duration(end_time).resize(height=200)

    txt_clip = CompositeVideoClip([
        txt_title.set_position(("center", 300)),
        txt_hook.set_position(("center", 550)),
        txt_smart.set_position(("center", 450)),
        txt_comment.set_position(("center", 1400)),
        gif_comment.set_position(("center", 1500)),
        gif_title.set_position(("center", 80)),
    ], size=(1080, 1920))


    # --- เพลงประกอบ ---
    music = AudioFileClip(music_file_path).volumex(0.2).set_duration(end_time)

    # --- รวมเสียงทั้งหมด ---
    final_audio = CompositeAudioClip([narration, music])

    # --- รวมวิดีโอ + เสียง ---
    final_clip = CompositeVideoClip([bg, txt_clip]).set_audio(final_audio)

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
