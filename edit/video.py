from moviepy.editor import *
from moviepy.audio.fx.all import audio_loop
from PIL import Image, ImageDraw
from gtts import gTTS

import numpy as np
import moviepy.video.fx.all as afx
import moviepy.config as mpconfig
import os, shutil,gemini


mpconfig.change_settings({"IMAGEMAGICK_BINARY": r"E:\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"})

data = gemini.get_data() 

def create_clip(hook, opt1, opt2, opt3, answer,
                     bg_video_path, music_file_path, sfx_file_path):

    os.makedirs("src/tts", exist_ok=True)

    # --- สร้าง TTS แยกเป็นช่วง ---
    before_opt3_path = "src/tts/before_opt3.mp3"
    opt3_path = "src/tts/opt3.mp3"
    answer_path = "src/tts/answer.mp3"

    gTTS(text=f"{hook}. {opt1}. {opt2}.", lang='en').save(before_opt3_path)
    gTTS(text=f"{opt3}", lang='en').save(opt3_path)
    gTTS(text=f"The answer is {answer}", lang='en').save(answer_path)

    speed_factor = 1.2  # ปรับความเร็วที่นี่
    before_opt3_clip = AudioFileClip(before_opt3_path).fx(afx.speedx, speed_factor)
    opt3_clip        = AudioFileClip(opt3_path).fx(afx.speedx, speed_factor)
    answer_clip      = AudioFileClip(answer_path).fx(afx.speedx, speed_factor)


    # --- คำนวณเวลา ---
    sfx_duration = 3.0
    sfx_start_time = before_opt3_clip.duration + opt3_clip.duration + 0.1
    answer_start_time = sfx_start_time + sfx_duration
    end_time = answer_start_time + answer_clip.duration + 0.2

    # --- narration ---
    silence_after_opt3 = AudioClip(lambda t: 0, duration=0.1)
    silence_for_sfx = AudioClip(lambda t: 0, duration=sfx_duration)
    silence_after_answer = AudioClip(lambda t: 0, duration=0.2)

    narration = concatenate_audioclips([
        before_opt3_clip,
        opt3_clip,
        silence_after_opt3,
        silence_for_sfx,
        answer_clip,
        silence_after_answer
    ])

    # --- สร้าง SFX ---
    sfx = AudioFileClip(sfx_file_path).volumex(0.5)
    sfx = audio_loop(sfx, duration=sfx_duration).set_start(sfx_start_time)

    # --- พื้นหลัง 1080x1920 และ loop ถ้าสั้น ---
    bg = VideoFileClip(bg_video_path).resize((1080, 1920))
    if bg.duration < end_time:
        loop_count = int(end_time // bg.duration) + 1
        bg = concatenate_videoclips([bg] * loop_count)
    bg = bg.subclip(0, end_time)

    # --- ข้อความบนจอ (ไม่มีคำตอบ) ---
    text_before_answer = f"{hook}\n\n1) {opt1}\n2) {opt2}\n3) {opt3}"
    txt_clip_before = TextClip(
        text_before_answer,
        fontsize=60,
        color='white',
        size=(1000, 1600),
        method='caption',
        align='center'
    ).set_duration(answer_start_time)  # จบก่อนเฉลยเริ่ม

    # --- ข้อความบนจอ (มีคำตอบ) ---
    # หาหมายเลขคำตอบ
    if answer == opt1:
        answer_display = f"{opt1}"
    elif answer == opt2:
        answer_display = f"{opt2}"
    elif answer == opt3:
        answer_display = f"{opt3}"
    else:
        answer_display = answer  # fallback ถ้าไม่ตรง

    text_with_answer = (
        f"{hook}\n\n"
        f"1) {opt1}\n2) {opt2}\n3) {opt3}\n\n"
        f"✅ Answer: Option {answer_display}"
    )

    txt_clip_after = TextClip(
        text_with_answer,
        fontsize=60,
        color='white',
        size=(1000, 1600),
        method='caption',
        align='center'
    ).set_start(answer_start_time).set_duration(end_time - answer_start_time)

    # --- กล่องพื้นหลังโปร่งแสง ---
    padding = 40
    box_w = txt_clip_before.w + padding
    box_h = txt_clip_before.h + padding
    corner_radius = 30

    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [(0, 0), (box_w, box_h)],
        radius=corner_radius,
        fill=(0, 0, 0, int(255 * 0.5))
    )
    bg_box_before = ImageClip(np.array(img)).set_duration(answer_start_time)
    bg_box_after = ImageClip(np.array(img)).set_start(answer_start_time).set_duration(end_time - answer_start_time)

    # --- จัดตำแหน่งให้อยู่กลางจอ ---
    bg_box_before = bg_box_before.set_position('center')
    txt_clip_before = txt_clip_before.set_position('center')
    bg_box_after = bg_box_after.set_position('center')
    txt_clip_after = txt_clip_after.set_position('center')

    # --- รวมข้อความ + กล่อง ---
    text_with_bg = CompositeVideoClip([
        bg_box_before,
        txt_clip_before,
        bg_box_after,
        txt_clip_after
    ], size=(1080, 1920))

    # --- เพลงประกอบ ---
    music = AudioFileClip(music_file_path).volumex(0.2).set_duration(end_time)

    # --- เสียงนาฬิกา ---
    sfx = AudioFileClip(sfx_file_path).volumex(0.3)
    sfx = audio_loop(sfx, duration=sfx_duration).set_start(sfx_start_time)

    # --- รวมเสียงทั้งหมด ---
    final_audio = CompositeAudioClip([narration, music, sfx])

    # --- รวมวิดีโอ + เสียง ---
    final_clip = CompositeVideoClip([bg, text_with_bg]).set_audio(final_audio)

    return final_clip

# ===== สร้างคลิป =====
row = gemini.get_data()
clip = create_clip(*row,
    bg_video_path="src/bg/background.mp4",
    music_file_path=r"src\musics\download.mp3",
    sfx_file_path=r"src\sound_effects\clock-ticking-sound-effect-240503.mp3"
)

os.makedirs("src/outputs", exist_ok=True)
clip.write_videofile("src/outputs/quiz_shorts.mp4", fps=30)

# --- ลบไฟล์ background.mp4 หลังตัดเสร็จ ---
clip.close()
bg_path = "src/bg/background.mp4"
if os.path.exists(bg_path):
    try:
        os.remove(bg_path)
        print(f"Deleated {bg_path} successful✅")
    except Exception as e:
        print(f"Cannot deleate {bg_path}: {e}❌")

shutil.rmtree("src/tts", ignore_errors=True)
