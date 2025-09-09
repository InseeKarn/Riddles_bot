from moviepy.editor import *
from gtts import gTTS
# from riddles_gen import get_data # Use to test on local
from .riddles_gen import get_data # Use to run on Github workflows

import numpy as np
import moviepy.video.fx.all as afx
import moviepy.config as mpconfig
import os, shutil, platform
import moviepy.video.fx.all as vfx
if platform.system() == "Windows":
    mpconfig.change_settings({
        "IMAGEMAGICK_BINARY": r"E:\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
    })

def create_clip(hook, bg_path, music_file_path, answer=None):

    # Calculate timing variables first
    start_time = 1
    char_time = 0.1
    typewriter_complete_time = start_time + len(hook) * char_time
    gif_start_time = typewriter_complete_time
    answer_start_time = gif_start_time + 3
    answer_duration = 2
    end_time = answer_start_time + answer_duration

    # ================== Effects ==================

    def hook_typewriter(hook, font="src/fonts/bold_font.ttf", fontsize=50, color='black', start_time=1, char_time=0.1, end_time=23):
        print(f"Debug: hook = '{hook}', length = {len(hook)}")
        
        # Use list to store clips
        clips = []
        
        # create blank clip for start_time
        blank_clip = ColorClip(size=(800, 200), color=(255,255,255), duration=start_time)
        blank_clip = blank_clip.set_position(("center", 330))
        
        for i in range(len(hook)):
            sub_text = hook[:i+1]
            
            txt_clip = TextClip(
                sub_text,
                fontsize=fontsize,
                font=font,
                color=color,
                size=(800, None),
                method='caption'
            )
            
            txt_clip = txt_clip.set_position(("center", 330))
            txt_clip = txt_clip.set_duration(char_time)
            clips.append(txt_clip)
        
        final_clip = TextClip(
            hook,
            fontsize=fontsize,
            font=font,
            color=color,
            size=(800, None),
            method='caption'
        ).set_position(("center", 230))
        
        remaining_time = end_time - start_time - len(hook) * char_time
        if remaining_time > 0:
            final_clip = final_clip.set_duration(remaining_time)
            clips.append(final_clip)
        
        # Concatenate all clips
        if clips:
            result = concatenate_videoclips([blank_clip] + clips, method="compose")
            return result
        else:
            return ColorClip(size=(950, 200), color=(0,0,0), duration=end_time)
    
    # ============================================

    font = "src/fonts/bold_font.ttf"

    hook_clip = hook_typewriter(
        hook,
        fontsize=50,
        font=font,
        color='black',
        start_time=start_time,
        char_time=char_time,
        end_time=end_time
    )

    gif_h = 350

    gif_folder = "src/gifs/"
    gif_files = [f for f in os.listdir(gif_folder) if f.endswith(".gif")]

    random_gif = os.path.join(gif_folder, random.choice(gif_files))

    # --- GIF ---
    gif_think = (
        VideoFileClip(random_gif)
        .resize(height=gif_h)
        .loop(duration=3)   # วนจนกว่าจะครบเวลาที่กำหนด
        .set_start(gif_start_time)
    )

    # --- Background box ---
    box_bg = ColorClip(size=(850, 1400), color=(255,255,255)).set_duration(end_time)
        
    # --- Background ---
    bg = ImageClip(bg_path).resize((1080, 1920))
    bg = bg.subclip(0, end_time)

    # --- Title ---
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
    .fx(vfx.resize, lambda t: min(0.5 + 0.5*(t**2), 1))
    )

    # Answer ===========

    if answer:
        txt_answer = (TextClip(
            f"The answer is: {answer}",
            fontsize=50,
            font=font,
            color='red',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(700, 500)
        )
        .set_start(answer_start_time)
        .set_duration(answer_duration)
        )
    else:
        txt_answer = ColorClip(size=(0,0), color=(0,0,0), duration=end_time)
    # Answer ===========

    # --- Composite everything ---
    txt_clip = CompositeVideoClip([
        txt_title,
        box_bg.set_position(("center", "center")),
        hook_clip.set_position(("center", 330)),
        txt_answer.set_position(("center", 1100)),
        gif_think.set_position(("center", 1280)),
    ], size=(1080, 1920))

    # --- music ---
    music = AudioFileClip(music_file_path).volumex(0.2).set_duration(end_time)

    # --- all audio ---
    final_audio = CompositeAudioClip([music])

    # --- Final composition ---
    final_clip = CompositeVideoClip([bg, txt_clip]).set_audio(final_audio)

    return final_clip

import random
def build_clip():
    hook, answer = get_data()
    hook_text = hook[0] if isinstance(hook, list) else hook
    answer_text = answer[0] if isinstance(answer, list) else answer

    music_dir = "src/musics"
    music_files = [f for f in os.listdir(music_dir) if f.endswith((".mp3"))]

    random_music = os.path.join(music_dir, random.choice(music_files))

    clip = create_clip(
        hook_text,
        bg_path="src/bg/background.jpg",
        music_file_path=random_music,
        answer=answer_text
    )
    
    os.makedirs("src/outputs", exist_ok=True)
    clip.write_videofile(
    "src/outputs/quiz_shorts.mp4",
    fps=20,
    codec="libx264",
    threads=4,
    preset="ultrafast",
    )
    clip.close()
    shutil.rmtree("src/tts", ignore_errors=True)

    return "src/outputs/quiz_shorts.mp4"


if __name__ == "__main__":
    build_clip()