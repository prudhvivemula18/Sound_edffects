ffmpeg -f concat -safe 0 -i hackathon_output\final\concat_list.txt \
    -c copy hackathon_output\final\final_story_video.mp4