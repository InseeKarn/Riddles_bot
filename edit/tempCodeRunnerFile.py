    # --- พื้นหลัง ---
    bg = VideoFileClip(bg_video_path).resize((1080, 1920))
    if bg.duration < end_time:
        loop_count = int(end_time // bg.duration) + 1
        bg = concatenate_videoclips([bg] * loop_count)
    bg = bg.subclip(0, end_time)

    # --- สร้าง TextClip และ Composite ---
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

    # --- Composite text + background ---
    text_with_bg = CompositeVideoClip([
        txt_clip_before.set_position('center'),
        txt_clip_after.set_position('center')
    ], size=(1080, 1920))

    # --- เพลงประกอบ ---
    music = AudioFileClip(music_file_path).volumex(0.2).set_duration(end_time)
    final_audio = CompositeAudioClip([narration, music, sfx])

    final_clip = CompositeVideoClip([bg, text_with_bg]).set_audio(final_audio)

    # --- ปล่อย clip พื้นหลังหลังใช้งาน ---
    bg.close()