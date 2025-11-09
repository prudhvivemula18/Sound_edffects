import os
import json
from pathlib import Path
from typing import List, Dict
import google.generativeai as genai
from PIL import Image
import time
import base64

# Configure Google AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class StoryVideoPipeline:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.dirs = {
            'images': self.output_dir / 'images',
            'videos': self.output_dir / 'videos',
            'audio': self.output_dir / 'audio',
            'narration': self.output_dir / 'narration',
            'soundfx': self.output_dir / 'soundfx',
            'final': self.output_dir / 'final'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Initialize models
        self.text_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.imagen_model = genai.ImageGenerationModel('gemini-2.0-flash-exp')
        self.veo_model = genai.VideoGenerationModel('gemini-2.0-flash-exp')
    
    def analyze_child_image(self, image_path: str) -> Dict:
        """Analyze the child image and extract features"""
        print("📸 Analyzing child image...")
        
        img = Image.open(image_path)
        
        prompt = """Analyze this child's photo and provide:
        1. Age range
        2. Gender
        3. Clothing style and colors
        4. Expression/mood
        5. Physical features (hair color, etc)
        6. Any distinctive characteristics
        
        Return as JSON with keys: age, gender, clothing, expression, features, distinctive"""
        
        response = self.text_model.generate_content([prompt, img])
        
        # Extract JSON from response
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        
        analysis = json.loads(text)
        print(f"✅ Image analysis complete")
        return analysis
    
    def enhance_story_plot(self, user_plot: str, child_analysis: Dict, num_clips: int = 8) -> List[Dict]:
        """Enhance user's 2-line plot into detailed 8-second clip descriptions"""
        print(f"\n📝 Enhancing story plot into {num_clips} clips...")
        
        prompt = f"""Given this child: {json.dumps(child_analysis)}
        
User's story idea: {user_plot}

Create a {num_clips}-clip story (each 8 seconds). For EACH clip provide:
1. scene_description: Detailed visual description
2. animation_prompt: How to animate from starting frame
3. image_prompt: Ultra detailed prompt for image generation (describe every detail - lighting, colors, composition, style, mood, characters, background, textures)
4. video_prompt: Detailed video generation prompt focusing on motion, camera movement, and cinematography
5. narration_text: What narrator says (2-3 sentences max, engaging storytelling voice)
6. soundfx_description: Sound effects needed (ambient sounds, actions, music style)

Return ONLY a JSON array with {num_clips} objects, each containing these 6 fields.
Keep the child's characteristics consistent across all clips.
Make prompts vivid, detailed, and production-ready."""

        response = self.text_model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract JSON
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        
        clips = json.loads(text)
        
        # Save story structure
        story_path = self.output_dir / 'story_structure.json'
        with open(story_path, 'w') as f:
            json.dump(clips, f, indent=2)
        
        print(f"✅ Story enhanced and saved to {story_path}")
        return clips
    
    def generate_image_with_imagen(self, prompt: str, reference_image_path: str, clip_num: int) -> str:
        """Generate scene image using Imagen 3"""
        print(f"\n🎨 Generating image for clip {clip_num} with Imagen 3...")
        
        try:
            # Read reference image
            with open(reference_image_path, 'rb') as f:
                ref_image_data = f.read()
            
            # Generate image with Imagen 3
            result = self.imagen_model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_some",
                person_generation="allow_adult",
                reference_image=ref_image_data
            )
            
            # Save generated image
            output_path = self.dirs['images'] / f'clip_{clip_num:02d}.png'
            result.images[0].save(output_path)
            
            print(f"✅ Image generated and saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error generating image: {e}")
            print(f"   Saving prompt for manual generation...")
            
            # Save prompt for reference
            prompt_path = self.dirs['images'] / f'clip_{clip_num:02d}_prompt.txt'
            with open(prompt_path, 'w') as f:
                f.write(f"IMAGEN 3 PROMPT:\n\n{prompt}")
            
            return None
    
    def generate_video_with_veo(self, image_path: str, video_prompt: str, clip_num: int) -> str:
        """Generate video using Veo 2"""
        print(f"\n🎬 Generating video for clip {clip_num} with Veo 2...")
        
        try:
            # Read input image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Generate video with Veo 2
            result = self.veo_model.generate_video(
                prompt=video_prompt,
                image=image_data,
                duration=8,  # 8 seconds
                aspect_ratio="16:9",
                resolution="1080p"
            )
            
            # Save generated video
            output_path = self.dirs['videos'] / f'clip_{clip_num:02d}.mp4'
            
            # Wait for generation to complete
            print("   ⏳ Waiting for video generation...")
            result.wait()
            
            # Download video
            with open(output_path, 'wb') as f:
                f.write(result.video_bytes)
            
            print(f"✅ Video generated and saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            print(f"   Saving prompt for manual generation...")
            
            # Save prompt
            prompt_path = self.dirs['videos'] / f'clip_{clip_num:02d}_prompt.txt'
            with open(prompt_path, 'w') as f:
                f.write(f"VEO 2 PROMPT:\n\n{video_prompt}")
            
            return None
    
    def generate_narration_with_tts(self, narration_text: str, clip_num: int) -> str:
        """Generate narration audio using Gemini TTS"""
        print(f"\n🎙️ Generating narration for clip {clip_num} with Gemini TTS...")
        
        try:
            # Use Gemini 2.5 Flash Preview TTS
            tts_model = genai.GenerativeModel('gemini-2.5-flash-preview-tts')  # Will update when TTS available
            
            # For now, save text and prepare for TTS
            text_path = self.dirs['narration'] / f'narration_{clip_num:02d}.txt'
            with open(text_path, 'w') as f:
                f.write(narration_text)
            
            output_path = self.dirs['narration'] / f'narration_{clip_num:02d}.mp3'
            
            # Note: Actual TTS integration pending API availability
            print(f"✅ Narration text saved: {text_path}")
            print(f"   📝 Text: {narration_text[:100]}...")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error generating narration: {e}")
            return None
    
    def generate_sound_effects(self, sfx_description: str, clip_num: int) -> str:
        """Generate sound effects - saves description for now"""
        print(f"\n🔊 Preparing sound effects for clip {clip_num}...")
        
        output_path = self.dirs['soundfx'] / f'soundfx_{clip_num:02d}.mp3'
        
        # Save sound effects description
        prompt_path = self.dirs['soundfx'] / f'soundfx_{clip_num:02d}_description.txt'
        with open(prompt_path, 'w') as f:
            f.write(f"SOUND EFFECTS DESCRIPTION:\n\n{sfx_description}")
        
        print(f"✅ Sound FX description saved: {prompt_path}")
        return str(output_path)
    
    def merge_clip_media(self, clip_num: int, video_path: str, narration_path: str, sfx_path: str) -> str:
        """Merge video, narration, and sound effects for one clip"""
        print(f"\n🎞️ Preparing merge for clip {clip_num}...")
        
        output_path = self.dirs['final'] / f'merged_clip_{clip_num:02d}.mp4'
        
        # Check if files exist
        video_exists = os.path.exists(video_path) if video_path else False
        
        if not video_exists:
            print(f"⚠️  Video not yet generated, skipping merge for clip {clip_num}")
            return None
        
        # FFmpeg command
        ffmpeg_cmd = f"""ffmpeg -i {video_path} \\
    -i {narration_path} \\
    -i {sfx_path} \\
    -filter_complex "[1:a][2:a]amix=inputs=2:duration=longest[aout]" \\
    -map 0:v -map "[aout]" \\
    -c:v copy -c:a aac \\
    -y {output_path}"""
        
        # Save command
        cmd_path = self.dirs['final'] / f'merge_cmd_{clip_num:02d}.sh'
        with open(cmd_path, 'w') as f:
            f.write(ffmpeg_cmd)
        
        # Try to execute
        try:
            import subprocess
            subprocess.run(ffmpeg_cmd, shell=True, check=True)
            print(f"✅ Clip merged: {output_path}")
        except Exception as e:
            print(f"⚠️  FFmpeg command saved to: {cmd_path}")
            print(f"   Run manually: bash {cmd_path}")
        
        return str(output_path)
    
    def merge_all_clips(self, clip_paths: List[str]) -> str:
        """Merge all clips into final video"""
        print(f"\n🎥 Preparing to merge all clips into final video...")
        
        # Filter out None values
        valid_clips = [p for p in clip_paths if p and os.path.exists(p)]
        
        if not valid_clips:
            print("⚠️  No valid clips to merge yet")
            return None
        
        output_path = self.dirs['final'] / 'final_story_video.mp4'
        
        # Create concat file
        concat_file = self.dirs['final'] / 'concat_list.txt'
        with open(concat_file, 'w') as f:
            for path in valid_clips:
                f.write(f"file '{os.path.abspath(path)}'\n")
        
        ffmpeg_cmd = f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy -y {output_path}"
        
        cmd_path = self.dirs['final'] / 'final_merge_cmd.sh'
        with open(cmd_path, 'w') as f:
            f.write(ffmpeg_cmd)
        
        # Try to execute
        try:
            import subprocess
            subprocess.run(ffmpeg_cmd, shell=True, check=True)
            print(f"✅ Final video created: {output_path}")
        except Exception as e:
            print(f"⚠️  Merge command saved to: {cmd_path}")
            print(f"   Run manually: bash {cmd_path}")
        
        return str(output_path)
    
    def process_complete_story(self, child_image_path: str, user_story: str, num_clips: int = 8):
        """Main pipeline: Process complete story from child photo to final video"""
        print("=" * 80)
        print("🚀 STARTING AI STORY VIDEO PIPELINE")
        print("=" * 80)
        
        # Step 1: Analyze child image
        child_analysis = self.analyze_child_image(child_image_path)
        
        # Step 2: Enhance story into clips
        clips = self.enhance_story_plot(user_story, child_analysis, num_clips)
        
        merged_clips = []
        
        # Step 3-7: Process each clip
        for i, clip in enumerate(clips, 1):
            print(f"\n{'=' * 80}")
            print(f"PROCESSING CLIP {i}/{num_clips}")
            print(f"{'=' * 80}")
            
            # Generate image with Imagen 3
            image_path = self.generate_image_with_imagen(
                prompt=clip['image_prompt'],
                reference_image_path=child_image_path,
                clip_num=i
            )
            
            # Generate video with Veo 2
            video_path = None
            if image_path:
                video_path = self.generate_video_with_veo(
                    image_path=image_path,
                    video_prompt=clip['video_prompt'],
                    clip_num=i
                )
            
            # Generate narration
            narration_path = self.generate_narration_with_tts(
                narration_text=clip['narration_text'],
                clip_num=i
            )
            
            # Generate sound effects description
            sfx_path = self.generate_sound_effects(
                sfx_description=clip['soundfx_description'],
                clip_num=i
            )
            
            # Merge clip media (if video exists)
            if video_path:
                merged_path = self.merge_clip_media(i, video_path, narration_path, sfx_path)
                if merged_path:
                    merged_clips.append(merged_path)
            
            # Rate limiting
            time.sleep(2)
        
        # Step 8: Merge all clips
        final_video = None
        if merged_clips:
            final_video = self.merge_all_clips(merged_clips)
        
        print("\n" + "=" * 80)
        print("🎉 PIPELINE COMPLETE!")
        print("=" * 80)
        print(f"📁 All outputs saved in: {self.output_dir}")
        if final_video:
            print(f"🎬 Final video: {final_video}")
        print(f"📝 Story structure: {self.output_dir / 'story_structure.json'}")
        
        return final_video


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize pipeline
    pipeline = StoryVideoPipeline(output_dir="hackathon_output")
    
    # Example inputs
    child_photo = "path/to/child_photo.jpg"  # Update this path
    user_story = "A brave child discovers a magical forest and makes friends with talking animals who teach them about kindness."
    
    # Run complete pipeline
    print("Starting pipeline...")
    print(f"Child photo: {child_photo}")
    print(f"Story: {user_story}")
    print("\n")
    
    final_video = pipeline.process_complete_story(
        child_image_path=child_photo,
        user_story=user_story,
        num_clips=8
    )
    
    if final_video:
        print(f"\n✨ Your story video is ready: {final_video}")
    else:
        print(f"\n⚠️  Pipeline completed with some pending generations")
        print(f"   Check the output directory for prompts and partial results")