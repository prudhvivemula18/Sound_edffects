ffmpeg -i hackathon_output\videos\clip_01.mp4 \
    -i hackathon_output\narration\narration_01.mp3 \
    -i hackathon_output\soundfx\soundfx_01.mp3 \
    -filter_complex "[1:a][2:a]amix=inputs=2:duration=longest[aout]" \
    -map 0:v -map "[aout]" \
    -c:v copy -c:a aac \
    hackathon_output\final\merged_clip_01.mp4