from moviepy.editor import *
from gtts import gTTS
from riddles_gen import get_data # Use to test on local
# from .riddles_gen import get_data # Use to run on Github workflows

import numpy as np
import moviepy.video.fx.all as afx
import moviepy.config as mpconfig
import os, shutil, platform
import moviepy.video.fx.all as vfx
if platform.system() == "Windows":
    mpconfig.change_settings({
        "IMAGEMAGICK_BINARY": r"E:\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
    })

def create_clip(hook, bg_path, music_file_path):

    font = "src/fonts/bold_font.ttf"

    hook_clip = TextClip(
        hook,
        fontsize=60,
        font=font,
        color='black',
        method='caption',
        size=(950, None),
    ).set_start(1).set_duration(22)

    mask = hook_clip.to_mask()

    def mask_func(get_frame, t):
        frame = get_frame(t)
        width = int(hook_clip.w * min(1, t / hook_clip.duration))
        frame[:, width:] = 0
        return frame

    mask = mask.fl(mask_func, apply_to=['mask'])

    # --- Calculate time ---
    hook_duration = hook_clip.duration
    end_time = 23

    #background box
    hook_clip = hook_clip.set_mask(mask)
    box_bg = ColorClip(size=(950, hook_clip.h + 40), color=(255,255,255)).set_opacity(1)
    hook_with_box = CompositeVideoClip([
        box_bg.set_position(("center", 550 - 20)),
        hook_clip.set_position(("center", 550))
    ], size=(1080,1920))

    # --- Background ---
    bg = ImageClip(bg_path).resize((1080, 1920))
    bg = bg.subclip(0, end_time)

    # --- Text ---
    txt_title = (TextClip(
        "Riddle Time!",
        fontsize=70,
        font=font,
        color='black',
        stroke_color='orange',
        stroke_width=3,
        method='label',
        size=(900, None)
    )
    .set_start(0)
    .set_duration(end_time)
    .set_position(("center", 50))
    .fx(vfx.resize, lambda t: 0.5 + 0.5*(t/1)))


    # --- GIF ---
    gif_think = VideoFileClip("src/gifs/thinking.gif").set_start(hook_duration).set_duration(end_time).resize(height=200)

    txt_clip = CompositeVideoClip([
        txt_title,
        hook_with_box,
        gif_think.set_position(("center", 1500)),
    ], size=(1080, 1920))


    # --- music ---
    music = AudioFileClip(music_file_path).volumex(0.2).set_duration(end_time)

    # --- all audio ---
    final_audio = CompositeAudioClip([music])

    # --- Bg + audio ---
    final_clip = CompositeVideoClip([bg, txt_clip]).set_audio(final_audio)

    return final_clip

import random
def build_clip():
    hook = get_data()
    hook_text = hook[0] if isinstance(hook, list) else hook

    music_dir = "src/musics"
    music_files = [f for f in os.listdir(music_dir) if f.endswith((".mp3"))]

    random_music = os.path.join(music_dir, random.choice(music_files))

    clip = create_clip(
        hook_text,
        bg_path="src/bg/background.jpg",
        music_file_path=random_music,
    )
    clip = clip.subclip(0, 23)
    os.makedirs("src/outputs", exist_ok=True)
    clip.write_videofile(
    "src/outputs/quiz_shorts.mp4",
    fps=24,
    codec="libx264",
    threads=4,
    preset="ultrafast",
    )
    clip.close()
    shutil.rmtree("src/tts", ignore_errors=True)

    return "src/outputs/quiz_shorts.mp4"


if __name__ == "__main__":
    build_clip()
