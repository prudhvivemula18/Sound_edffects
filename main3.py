import os
import json
from pathlib import Path
from typing import List, Dict
import google.generativeai as genai
import time

# Configure Google AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class InteractiveStoryTTSPipeline:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.dirs = {
            'prompts': self.output_dir / 'prompts',
            'narration': self.output_dir / 'narration',
            'story_data': self.output_dir / 'story_data'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Initialize models
        self.text_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.tts_model = genai.GenerativeModel('gemini-2.5-flash-preview-tts')
        
        # 8 seconds per clip
        self.clip_duration = 8
    
    def get_user_input(self):
        """Get story idea and duration from user"""
        print("=" * 80)
        print("🎬 WELCOME TO INTERACTIVE STORY VIDEO CREATOR")
        print("=" * 80)
        print()
        
        # Get story idea
        print("📖 Tell me your story idea:")
        print("   (Can be a brief concept, a detailed plot, or anything in between)")
        print()
        story_idea = input("Your story: ").strip()
        
        while not story_idea:
            print("❌ Please provide a story idea!")
            story_idea = input("Your story: ").strip()
        
        print()
        
        # Get desired duration in minutes
        print("⏱️  How long should your story video be?")
        print("   (Enter duration in minutes, e.g., 1, 2, 3.5, etc.)")
        print()
        
        while True:
            try:
                duration_input = input("Duration (in minutes): ").strip()
                duration_minutes = float(duration_input)
                
                if duration_minutes <= 0:
                    print("❌ Duration must be greater than 0!")
                    continue
                
                if duration_minutes > 30:
                    print("⚠️  That's quite long! Recommended: 1-5 minutes")
                    confirm = input("   Continue anyway? (yes/no): ").strip().lower()
                    if confirm not in ['yes', 'y']:
                        continue
                
                break
            except ValueError:
                print("❌ Please enter a valid number!")
        
        # Calculate number of clips
        total_seconds = duration_minutes * 60
        num_clips = int(total_seconds / self.clip_duration)
        
        print()
        print("=" * 80)
        print("📊 STORY BREAKDOWN")
        print("=" * 80)
        print(f"Duration: {duration_minutes} minutes ({int(total_seconds)} seconds)")
        print(f"Number of clips: {num_clips} clips × {self.clip_duration} seconds each")
        print(f"Story idea: {story_idea[:80]}...")
        print("=" * 80)
        print()
        
        confirm = input("Proceed with this configuration? (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("\n❌ Pipeline cancelled by user")
            return None, None
        
        return story_idea, num_clips
    
    def expand_story_to_scenes(self, story_idea: str, num_clips: int) -> List[Dict]:
        """Expand user's story idea into detailed scene descriptions"""
        print(f"\n📝 Expanding your story into {num_clips} scenes...")
        print("   This may take a moment...\n")
        
        prompt = f"""You are a professional storyteller and screenplay writer. 

User's Story Idea:
{story_idea}

Task: Expand this story into EXACTLY {num_clips} scenes. Each scene will be 8 seconds long.

Requirements:
1. Create a complete narrative arc with beginning, middle, and end
2. Each scene should have:
   - A clear title (2-5 words)
   - A detailed description (2-3 sentences) that paints a vivid picture
3. Maintain consistency and flow between scenes
4. Include emotional beats and character development
5. Make each scene visually interesting and cinematic
6. Ensure the story feels complete within the {num_clips} scenes

Return ONLY a JSON array with {num_clips} objects, each containing:
- "title": Scene title
- "description": Detailed scene description

Example format:
[
  {{
    "title": "Morning Awakening",
    "description": "Golden sunlight streams through the bedroom window. A young protagonist slowly opens their eyes, stretching as a new day full of possibilities begins."
  }},
  ...
]

Generate all {num_clips} scenes now."""

        try:
            response = self.text_model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            scenes = json.loads(text)
            
            # Validate we got the right number of scenes
            if len(scenes) != num_clips:
                print(f"⚠️  Expected {num_clips} scenes, got {len(scenes)}. Adjusting...")
                if len(scenes) > num_clips:
                    scenes = scenes[:num_clips]
                else:
                    # Need more scenes - this shouldn't happen but handle it
                    print(f"❌ Not enough scenes generated. Please try again.")
                    return None
            
            # Save expanded story
            story_path = self.dirs['story_data'] / 'expanded_story.json'
            with open(story_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'original_idea': story_idea,
                    'num_clips': num_clips,
                    'total_duration_seconds': num_clips * self.clip_duration,
                    'scenes': scenes
                }, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Story expanded successfully!")
            print(f"   Saved to: {story_path}\n")
            
            # Show preview
            print("📋 STORY OUTLINE:")
            print("=" * 80)
            for i, scene in enumerate(scenes, 1):
                print(f"{i:2d}. {scene['title']}")
                print(f"    {scene['description'][:70]}...")
                if i % 5 == 0 and i < len(scenes):
                    print()
            print("=" * 80)
            print()
            
            return scenes
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing story structure: {e}")
            print(f"   Raw response: {text[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Error expanding story: {e}")
            return None
    
    def create_scene_prompts(self, scene: Dict, scene_num: int, total_scenes: int) -> Dict:
        """Create ultra-detailed prompts for a single scene"""
        print(f"🎬 Processing Scene {scene_num}/{total_scenes}: {scene['title']}")
        
        prompt = f"""Create ultra-detailed production prompts for this 8-second story scene:

Scene {scene_num} of {total_scenes}
Title: {scene['title']}
Description: {scene['description']}

Generate the following with MAXIMUM detail:

1. IMAGE_PROMPT: Ultra-detailed visual prompt (300+ words) including:
   - Exact lighting conditions (time of day, light quality, color temperature, shadows, highlights)
   - Precise camera angle, framing, composition (rule of thirds, golden ratio, etc.)
   - Detailed environment description (every visible element, textures, materials)
   - Color palette and mood (specific color codes, saturation, contrast)
   - Character positioning, posture, expression, clothing details (if applicable)
   - Background elements, props, and set dressing
   - Artistic style (cinematic realism, stylized, atmospheric, etc.)
   - Depth of field, focus points, bokeh quality
   - Weather, atmosphere, air quality (fog, haze, clarity)

2. VIDEO_PROMPT: Detailed animation/motion prompt (200+ words) including:
   - Specific camera movements (smooth pan, tilt, dolly, crane, tracking shots)
   - Speed and acceleration of camera movements
   - Character movements, gestures, actions with precise timing
   - Environmental animations (wind, particles, light changes, shadows)
   - Transition effects (if applicable)
   - Pacing and rhythm within the 8 seconds
   - Key moments at 0s, 2s, 4s, 6s, 8s timestamps
   - Cinematic techniques (slow motion, speed ramps, parallax)
   - Movement flow and continuity

3. NARRATION_TEXT: Engaging 8-second narration (20-25 words, 2-3 sentences)
   - Warm, engaging storytelling voice
   - Emotional resonance matching scene mood
   - Connects to visual action
   - Proper pacing for 8-second delivery
   - Natural, conversational tone

4. NARRATION_VOICE_DIRECTION: Detailed TTS voice direction including:
   - Specific tone and emotion (e.g., "warm and hopeful", "tense and urgent")
   - Pacing instructions (speed: slow/medium/fast, where to pause)
   - Voice character (age, energy level, personality traits)
   - Specific words or phrases to emphasize
   - Volume dynamics (soft, building, powerful)
   - Overall emotional arc within the 8 seconds

5. SOUND_FX: Comprehensive sound design (150+ words) including:
   - Detailed ambient sounds (environment, room tone, nature)
   - Action-specific sound effects with timing
   - Foley details (footsteps, clothing, objects)
   - Music style, instruments, tempo, mood
   - Audio transitions and fades
   - Spatial audio considerations (stereo positioning)
   - Emotional impact through sound
   - Volume levels and mixing notes

Return ONLY a JSON object with these 5 fields, no additional text."""

        try:
            response = self.text_model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            scene_data = json.loads(text)
            scene_data['scene_number'] = scene_num
            scene_data['scene_title'] = scene['title']
            scene_data['original_description'] = scene['description']
            
            print(f"✅ Scene {scene_num} prompts generated")
            return scene_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON for scene {scene_num}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error generating prompts for scene {scene_num}: {e}")
            return None
    
    def generate_narration_audio(self, scene_data: Dict) -> str:
        """Generate narration audio using Gemini 2.5 Flash TTS"""
        scene_num = scene_data['scene_number']
        narration_text = scene_data['NARRATION_TEXT']
        voice_direction = scene_data.get('NARRATION_VOICE_DIRECTION', '')
        
        print(f"🎙️  Generating TTS for Scene {scene_num}...")
        print(f"   Text: {narration_text}")
        
        try:
            # Prepare TTS prompt with voice direction
            tts_prompt = f"""Voice Direction: {voice_direction}

Narration: {narration_text}

Deliver this narration with the specified voice direction, paced for 8 seconds."""
            
            # Generate audio with TTS model
            response = self.tts_model.generate_content(
                tts_prompt,
                generation_config={
                    'temperature': 0.7,
                }
            )
            
            # Save audio file
            output_path = self.dirs['narration'] / f'narration_{scene_num:02d}.mp3'
            
            # Check if response contains audio
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Save the audio data
                        audio_data = part.inline_data.data
                        with open(output_path, 'wb') as f:
                            f.write(audio_data)
                        
                        print(f"✅ TTS audio generated: {output_path}")
                        return str(output_path)
            
            # If no audio in response, save text for reference
            text_path = self.dirs['narration'] / f'narration_{scene_num:02d}.txt'
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"SCENE {scene_num}: {scene_data['scene_title']}\n\n")
                f.write(f"NARRATION TEXT:\n{narration_text}\n\n")
                f.write(f"VOICE DIRECTION:\n{voice_direction}\n\n")
                f.write(f"TTS PROMPT:\n{tts_prompt}\n")
            
            print(f"⚠️  TTS audio not found in response")
            print(f"   Text and prompt saved to: {text_path}")
            return str(text_path)
            
        except Exception as e:
            print(f"❌ Error generating TTS: {e}")
            
            # Save text as fallback
            text_path = self.dirs['narration'] / f'narration_{scene_num:02d}.txt'
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"SCENE {scene_num}: {scene_data['scene_title']}\n\n")
                f.write(f"NARRATION TEXT:\n{narration_text}\n\n")
                f.write(f"VOICE DIRECTION:\n{voice_direction}\n\n")
                f.write(f"ERROR: {str(e)}\n")
            
            print(f"   Narration text saved to: {text_path}")
            return str(text_path)
    
    def save_individual_prompts(self, scene_data: Dict):
        """Save individual prompt files for each scene"""
        scene_num = scene_data['scene_number']
        
        # Save image prompt
        image_prompt_path = self.dirs['prompts'] / f'scene_{scene_num:02d}_IMAGE.txt'
        with open(image_prompt_path, 'w', encoding='utf-8') as f:
            f.write(f"SCENE {scene_num}: {scene_data['scene_title']}\n")
            f.write("=" * 80 + "\n\n")
            f.write("IMAGE GENERATION PROMPT\n\n")
            f.write(scene_data['IMAGE_PROMPT'])
        
        # Save video prompt
        video_prompt_path = self.dirs['prompts'] / f'scene_{scene_num:02d}_VIDEO.txt'
        with open(video_prompt_path, 'w', encoding='utf-8') as f:
            f.write(f"SCENE {scene_num}: {scene_data['scene_title']}\n")
            f.write("=" * 80 + "\n\n")
            f.write("VIDEO GENERATION PROMPT\n\n")
            f.write(scene_data['VIDEO_PROMPT'])
        
        # Save sound FX prompt
        sfx_prompt_path = self.dirs['prompts'] / f'scene_{scene_num:02d}_SOUNDFX.txt'
        with open(sfx_prompt_path, 'w', encoding='utf-8') as f:
            f.write(f"SCENE {scene_num}: {scene_data['scene_title']}\n")
            f.write("=" * 80 + "\n\n")
            f.write("SOUND EFFECTS PROMPT\n\n")
            f.write(scene_data['SOUND_FX'])
        
        print(f"✅ Individual prompts saved for Scene {scene_num}")
    
    def run_pipeline(self):
        """Main interactive pipeline"""
        print("\n")
        
        # Step 1: Get user input
        story_idea, num_clips = self.get_user_input()
        
        if not story_idea or not num_clips:
            return
        
        # Step 2: Expand story into scenes
        scenes = self.expand_story_to_scenes(story_idea, num_clips)
        
        if not scenes:
            print("\n❌ Failed to expand story. Please try again.")
            return
        
        # Confirm before proceeding
        print("\n🚀 Ready to generate detailed prompts and TTS narration!")
        proceed = input("   Continue? (yes/no): ").strip().lower()
        
        if proceed not in ['yes', 'y']:
            print("\n❌ Pipeline cancelled by user")
            return
        
        print("\n" + "=" * 80)
        print("🎬 GENERATING PRODUCTION ASSETS")
        print("=" * 80)
        
        # Step 3: Process each scene
        all_scene_data = []
        generated_audio = []
        
        for i, scene in enumerate(scenes, 1):
            print(f"\n{'=' * 80}")
            print(f"SCENE {i}/{num_clips}")
            print(f"{'=' * 80}")
            
            # Generate detailed prompts
            scene_data = self.create_scene_prompts(scene, i, num_clips)
            
            if scene_data:
                all_scene_data.append(scene_data)
                
                # Save individual prompt files
                self.save_individual_prompts(scene_data)
                
                # Generate TTS narration
                audio_path = self.generate_narration_audio(scene_data)
                if audio_path:
                    generated_audio.append(audio_path)
            
            # Rate limiting
            time.sleep(2)
        
        # Save all scene data
        all_prompts_path = self.dirs['story_data'] / 'all_scene_prompts.json'
        with open(all_prompts_path, 'w', encoding='utf-8') as f:
            json.dump(all_scene_data, f, indent=2, ensure_ascii=False)
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎉 PIPELINE COMPLETE!")
        print("=" * 80)
        print(f"📁 All outputs saved in: {self.output_dir}")
        print(f"📝 Story structure: {self.dirs['story_data']}/")
        print(f"🎙️  Narration files: {self.dirs['narration']}/")
        print(f"📄 Individual prompts: {self.dirs['prompts']}/")
        print(f"\n✅ Generated {len(generated_audio)} TTS narration files")
        print(f"✅ Created {len(all_scene_data)} complete scene packages")
        print("\n" + "=" * 80)


# Main execution
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize and run interactive pipeline
    pipeline = InteractiveStoryTTSPipeline(output_dir="my_story_output")
    pipeline.run_pipeline()