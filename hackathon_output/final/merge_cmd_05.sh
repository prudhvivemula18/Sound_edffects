ffmpeg -i hackathon_output\videos\clip_05.mp4 \
    -i hackathon_output\narration\narration_05.mp3 \
    -i hackathon_output\soundfx\soundfx_05.mp3 \
    -filter_complex "[1:a][2:a]amix=inputs=2:duration=longest[aout]" \
    -map 0:v -map "[aout]" \
    -c:v copy -c:a aac \
    hackathon_output\final\merged_clip_05.mp4