import os
import json
from pathlib import Path
from typing import List, Dict
import google.generativeai as genai
from PIL import Image
import time

# Configure Google AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class StoryTTSPipeline:
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
    
    def create_scene_prompts(self, scene_descriptions: List[Dict]) -> List[Dict]:
        """Create ultra-detailed prompts for each scene (8-second clips)"""
        print(f"\n📝 Creating ultra-detailed prompts for {len(scene_descriptions)} scenes...")
        
        enhanced_scenes = []
        
        for i, scene in enumerate(scene_descriptions, 1):
            print(f"\n🎬 Processing Scene {i}: {scene['title']}")
            
            prompt = f"""Create ultra-detailed production prompts for this 8-second story scene:

Scene Title: {scene['title']}
Scene Description: {scene['description']}

Generate the following with MAXIMUM detail:

1. IMAGE_PROMPT: Ultra-detailed visual prompt (300+ words) including:
   - Exact lighting conditions (time of day, light quality, color temperature, shadows)
   - Precise camera angle, framing, and composition
   - Detailed environment description (every visible element)
   - Color palette and mood
   - Texture details (materials, surfaces, fabrics)
   - Character positioning and expression (if applicable)
   - Artistic style and cinematography references
   - Depth of field and focus points

2. VIDEO_PROMPT: Detailed animation/motion prompt (200+ words) including:
   - Specific camera movements (pans, tilts, zooms, tracking)
   - Character movements and actions (timing, speed, gestures)
   - Environmental animations (wind, light changes, particles)
   - Transition effects
   - Pacing and rhythm of the 8-second clip
   - Key moments and beats within the 8 seconds
   - Cinematic techniques to use

3. NARRATION_TEXT: Engaging 8-second narration (2-3 sentences, ~20-25 words)
   - Warm, storytelling voice
   - Emotional resonance
   - Connects to the visual action
   - Appropriate pacing for 8 seconds

4. NARRATION_VOICE_DIRECTION: Detailed TTS direction including:
   - Tone and emotion (specific feeling)
   - Pacing (speed, pauses, emphasis)
   - Voice character (warm/cool, young/mature, energetic/calm)
   - Key words to emphasize
   - Overall mood to convey

5. SOUND_FX: Comprehensive sound design (100+ words) including:
   - Ambient sounds (detailed environment audio)
   - Action-specific sound effects
   - Music style and instruments
   - Audio transitions
   - Mood and emotional impact through sound

Return ONLY a JSON object with these 5 fields."""

            response = self.text_model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            try:
                scene_data = json.loads(text)
                scene_data['scene_number'] = i
                scene_data['scene_title'] = scene['title']
                scene_data['original_description'] = scene['description']
                enhanced_scenes.append(scene_data)
                print(f"✅ Scene {i} prompts generated")
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing JSON for scene {i}: {e}")
                print(f"Raw response: {text[:200]}...")
            
            # Rate limiting
            time.sleep(2)
        
        # Save all prompts
        prompts_path = self.dirs['story_data'] / 'enhanced_scene_prompts.json'
        with open(prompts_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_scenes, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ All scene prompts saved to: {prompts_path}")
        return enhanced_scenes
    
    def generate_narration_audio(self, scene_data: Dict) -> str:
        """Generate narration audio using Gemini 2.5 Flash TTS"""
        scene_num = scene_data['scene_number']
        narration_text = scene_data['NARRATION_TEXT']
        voice_direction = scene_data.get('NARRATION_VOICE_DIRECTION', '')
        
        print(f"\n🎙️ Generating TTS for Scene {scene_num}...")
        print(f"   Text: {narration_text}")
        
        try:
            # Prepare TTS prompt with voice direction
            tts_prompt = f"""Voice Direction: {voice_direction}

Narration Text: {narration_text}

Please read this narration with the specified voice direction, ensuring it fits within 8 seconds."""
            
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
    
    def process_story(self, scene_descriptions: List[Dict]):
        """Main pipeline: Generate ultra-detailed prompts and TTS narration"""
        print("=" * 80)
        print("🚀 STARTING STORY TTS PIPELINE")
        print("=" * 80)
        
        # Step 1: Create ultra-detailed prompts for all scenes
        enhanced_scenes = self.create_scene_prompts(scene_descriptions)
        
        if not enhanced_scenes:
            print("\n❌ No scenes were successfully processed")
            return
        
        # Step 2: Generate TTS and save individual prompts for each scene
        generated_audio = []
        
        for scene_data in enhanced_scenes:
            print(f"\n{'=' * 80}")
            print(f"PROCESSING SCENE {scene_data['scene_number']}/{len(enhanced_scenes)}")
            print(f"{'=' * 80}")
            
            # Save individual prompt files
            self.save_individual_prompts(scene_data)
            
            # Generate TTS narration
            audio_path = self.generate_narration_audio(scene_data)
            if audio_path:
                generated_audio.append(audio_path)
            
            # Rate limiting
            time.sleep(2)
        
        print("\n" + "=" * 80)
        print("🎉 PIPELINE COMPLETE!")
        print("=" * 80)
        print(f"📁 All outputs saved in: {self.output_dir}")
        print(f"📝 Enhanced prompts: {self.dirs['story_data'] / 'enhanced_scene_prompts.json'}")
        print(f"🎙️ Narration files: {self.dirs['narration']}/")
        print(f"📄 Individual prompts: {self.dirs['prompts']}/")
        print(f"\n✅ Generated {len(generated_audio)} TTS narration files")


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize pipeline
    pipeline = StoryTTSPipeline(output_dir="college_story_output")
    
    # Your college story scenes
    college_scenes = [
        {
            "title": "Wake-Up Call",
            "description": "The day begins as sunlight filters through the blinds. A quiet dorm room stirs to life, and a student slowly wakes, ready to greet the morning."
        },
        {
            "title": "The Old Sneakers",
            "description": "Familiar sneakers sit worn but steady. Fingers trace the laces, grounding the start of another day on campus."
        },
        {
            "title": "Campus Walk",
            "description": "The campus awakens in golden light. Each step along the tree-lined path carries a calm, steady rhythm forward."
        },
        {
            "title": "Classroom Reflection",
            "description": "In the quiet lecture hall, focus settles on a notebook. Thoughts flow as the world moves gently around, unnoticed."
        },
        {
            "title": "Midnight Study",
            "description": "Late-night effort glows under the desk lamp. Fingers move across the keyboard, ideas taking shape in the stillness of night."
        },
        {
            "title": "Library Collaboration",
            "description": "Sunlight filters through the library windows as collaboration unfolds. Ideas shared, hands gesturing, learning in motion."
        },
        {
            "title": "Run Again",
            "description": "Morning light catches sweat and determination. Every stride on the pavement pushes forward, fueled by energy and resolve."
        },
        {
            "title": "College Life Montage",
            "description": "Life moves in vibrant snapshots—coffee warms the hands, laughter echoes, and creativity sparks everywhere around."
        },
        {
            "title": "Rejection (Phone Scene)",
            "description": "A quiet moment at night. Rain taps against the window as a message shifts thoughts, and reflection settles in."
        },
        {
            "title": "New Idea",
            "description": "Morning light inspires a fresh start. Pencil glides across the page, and new ideas begin to take shape."
        },
        {
            "title": "Presentation Day",
            "description": "Confidence shines as the student presents. Words flow, gestures emphasize, and the room leans in, attentive and engaged."
        },
        {
            "title": "Approval",
            "description": "A simple nod, a warm smile. Approval shines quietly, a moment of recognition that lifts the spirit."
        },
        {
            "title": "Rain Walk",
            "description": "Raindrops fall softly as footsteps echo on wet pavement. Reflection and calm accompany a solitary walk home."
        },
        {
            "title": "Belief Quote",
            "description": "Every step forward starts with belief. Light rises through the haze, and hope feels tangible in the morning air."
        }
    ]
    
    # Run pipeline
    print("Starting Story TTS Pipeline...")
    print(f"Processing {len(college_scenes)} scenes\n")
    
    pipeline.process_story(college_scenes)