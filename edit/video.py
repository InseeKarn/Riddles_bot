from moviepy.editor import *
from moviepy.audio.fx.all import audio_loop
from PIL import Image, ImageDraw
from gtts import gTTS
from .riddles_gen import get_data

import numpy as np
import moviepy.video.fx.all as afx
import moviepy.config as mpconfig
import os, shutil

mpconfig.change_settings({"IMAGEMAGICK_BINARY": r"E:\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"})

def create_clip(hook, answer, bg_video_path, music_file_path, sfx_file_path):

    os.makedirs("src/tts", exist_ok=True)

    # --- สร้าง TTS ---
    hook_path = "src/tts/hook.mp3"
    answer_path = "src/tts/answer.mp3"

    gTTS(text=hook, lang='en').save(hook_path)
    gTTS(text=f"The answer is {answer}", lang='en').save(answer_path)

    speed_factor = 1.3
    hook_clip = AudioFileClip(hook_path).fx(afx.speedx, speed_factor)
    answer_clip = AudioFileClip(answer_path).fx(afx.speedx, speed_factor)

    # --- คำนวณเวลา ---
    sfx_duration = 3.0
    hook_duration = hook_clip.duration + 0.1
    answer_start_time = hook_duration + sfx_duration
    end_time = answer_start_time + answer_clip.duration + 0.2

    # --- narration ---
    silence_after_hook = AudioClip(lambda t: 0, duration=0.1)
    silence_for_sfx = AudioClip(lambda t: 0, duration=sfx_duration)
    silence_after_answer = AudioClip(lambda t: 0, duration=0.1)

    narration = concatenate_audioclips([
        hook_clip,
        silence_after_hook,
        silence_for_sfx,
        answer_clip,
        silence_after_answer
    ])

    # --- SFX ---
    sfx = AudioFileClip(sfx_file_path).volumex(0.3)
    sfx = audio_loop(sfx, duration=sfx_duration).set_start(hook_duration)

    # --- พื้นหลัง ---
    bg = VideoFileClip(bg_video_path).resize((1080, 1920))
    if bg.duration < end_time:
        loop_count = int(end_time // bg.duration) + 1
        bg = concatenate_videoclips([bg] * loop_count)
    bg = bg.subclip(0, end_time)

    # --- ข้อความบนจอ ---
    txt_clip_before = TextClip(
        hook,
        fontsize=60,
        color='white',
        size=(1000, 1600),
        method='caption',
        align='center'
    ).set_duration(answer_start_time)

    txt_clip_after = TextClip(
        f"{hook}\n\n✅ Answer: {answer}",
        fontsize=60,
        color='white',
        size=(1000, 1600),
        method='caption',
        align='center'
    ).set_start(answer_start_time).set_duration(end_time - answer_start_time)

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

    bg_box_before = ImageClip(np.array(img)).set_duration(answer_start_time)
    bg_box_after = ImageClip(np.array(img)).set_start(answer_start_time).set_duration(end_time - answer_start_time)

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
    final_audio = CompositeAudioClip([narration, music, sfx])

    # --- รวมวิดีโอ + เสียง ---
    final_clip = CompositeVideoClip([bg, text_with_bg]).set_audio(final_audio)


    return final_clip

def build_quiz_clip():
    hook, answer = get_data()  # ต้องให้ get_data() return แค่ 2 ค่า
    clip = create_clip(
        hook,
        answer,
        bg_video_path="src/bg/background.mp4",
        music_file_path="src/musics/download.mp3",
        sfx_file_path="src/sound_effects/clock-ticking.mp3"
    )

    os.makedirs("src/outputs", exist_ok=True)
    clip.write_videofile("src/outputs/quiz_shorts.mp4", fps=30)
    clip.close()
    shutil.rmtree("src/tts", ignore_errors=True)

    return "src/outputs/quiz_shorts.mp4"


if __name__ == "__main__":
    build_quiz_clip()