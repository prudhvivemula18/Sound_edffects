# Interactive Story TTS Pipeline

An automated pipeline that transforms story ideas into complete production-ready assets using Google's Gemini AI models. Creates detailed scene breakdowns, visual prompts, narration scripts, and TTS audio files.

## 🎯 Features

- **Interactive Story Expansion**: Converts brief story ideas into detailed scene-by-scene breakdowns
- **Automated Asset Generation**: Creates comprehensive prompts for images, videos, sound effects, and narration
- **AI-Powered Text-to-Speech**: Generates natural-sounding narration audio using Gemini 2.5 Flash TTS
- **Flexible Duration**: Supports any video length with 8-second scene clips
- **Organized Output**: Structured file system with separate directories for different asset types

## 📋 Requirements

### Python Dependencies
```bash
pip install google-generativeai python-dotenv
```

### API Requirements
- **Google AI API Key** with access to:
  - `gemini-2.0-flash-exp` (text generation)
  - `gemini-2.5-flash-preview-tts` (text-to-speech)

## 🔧 Setup

### 1. Clone or Download the Project
```bash
git clone <your-repo-url>
cd story-tts-pipeline
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Create a `requirements.txt` file with:
```
google-generativeai>=0.3.0
python-dotenv>=1.0.0
```

### 3. Configure API Key

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_ai_api_key_here
```

**To get your Google AI API key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it into your `.env` file

### 4. Verify API Access

Test your API key:
```python
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Test text model
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Hello!")
print(response.text)
```

## 🚀 Usage

### Basic Usage
```bash
python interactive_story_pipeline.py
```

### Interactive Prompts
The pipeline will ask you for:

1. **Story Idea**: Your concept, plot, or narrative
   - Example: "A robot discovering emotions for the first time"
   - Can be brief or detailed

2. **Duration**: How long your video should be (in minutes)
   - Example: 2 (for a 2-minute video)
   - Creates scenes of 8 seconds each

### Example Session
```
🎬 WELCOME TO INTERACTIVE STORY VIDEO CREATOR
================================================================================

📖 Tell me your story idea:
Your story: A lonely astronaut finds a mysterious signal on Mars

⏱️  How long should your story video be?
Duration (in minutes): 2

📊 STORY BREAKDOWN
================================================================================
Duration: 2.0 minutes (120 seconds)
Number of clips: 15 clips × 8 seconds each
Story idea: A lonely astronaut finds a mysterious signal on Mars...
================================================================================

Proceed with this configuration? (yes/no): yes
```

## 📁 Output Structure

```
my_story_output/
├── story_data/
│   ├── expanded_story.json       # Complete story structure
│   └── all_scene_prompts.json    # All scene data in one file
├── prompts/
│   ├── scene_01_IMAGE.txt        # Image generation prompt
│   ├── scene_01_VIDEO.txt        # Video generation prompt
│   ├── scene_01_SOUNDFX.txt      # Sound effects prompt
│   ├── scene_02_IMAGE.txt
│   └── ...
└── narration/
    ├── narration_01.mp3          # TTS audio file
    ├── narration_02.mp3
    └── ...
```

## 📄 Output Files Explained

### Story Data Files
- **expanded_story.json**: Original idea + scene breakdown with titles and descriptions
- **all_scene_prompts.json**: Complete production data for all scenes

### Individual Scene Prompts
Each scene gets three prompt files:
- **IMAGE**: Ultra-detailed visual description (300+ words) for image generation
- **VIDEO**: Animation and camera movement instructions (200+ words)
- **SOUNDFX**: Comprehensive sound design specifications (150+ words)

### Narration Files
- **narration_XX.mp3**: Generated TTS audio files (8 seconds each)
- **narration_XX.txt**: Fallback text files if TTS generation fails

## 🎨 Using the Generated Assets

### Image Generation (Midjourney, DALL-E, Stable Diffusion)
```bash
# Copy the IMAGE prompt from:
my_story_output/prompts/scene_01_IMAGE.txt

# Paste into your image generation tool
```

### Video Generation (Runway, Pika, Luma)
```bash
# Use the VIDEO prompt from:
my_story_output/prompts/scene_01_VIDEO.txt

# Combined with the generated image as a starting frame
```

### Sound Design (ElevenLabs, Soundly, Epidemic Sound)
```bash
# Follow the SOUNDFX specifications from:
my_story_output/prompts/scene_01_SOUNDFX.txt
```

### Narration Audio
```bash
# The TTS audio is ready to use:
my_story_output/narration/narration_01.mp3
```

## ⚙️ Configuration

### Change Output Directory
```python
pipeline = InteractiveStoryTTSPipeline(output_dir="custom_output_folder")
```

### Adjust Scene Duration
Modify the `clip_duration` in the class initialization:
```python
self.clip_duration = 10  # Change from 8 to 10 seconds
```

### Customize Models
Update model names in `__init__`:
```python
self.text_model = genai.GenerativeModel('gemini-1.5-pro')  # Different model
self.tts_model = genai.GenerativeModel('gemini-2.5-flash-preview-tts')
```

## 🔍 Troubleshooting

### API Key Issues
```
Error: API key not found
Solution: Verify .env file exists and contains GOOGLE_API_KEY
```

### TTS Generation Fails
```
⚠️  TTS audio not found in response
Solution: Check API access to gemini-2.5-flash-preview-tts model
          Text files are saved as fallback
```

### Rate Limiting
```
Error: 429 Too Many Requests
Solution: The pipeline includes 2-second delays between scenes
          Increase sleep time in run_pipeline() if needed
```

### JSON Parsing Errors
```
❌ Error parsing story structure
Solution: The pipeline will retry. If persistent, check API response format
```

## 📊 Performance

- **Scene Generation**: ~3-5 seconds per scene
- **TTS Generation**: ~5-10 seconds per audio file
- **Total Time**: For a 2-minute video (15 scenes): ~5-10 minutes

## 🛡️ API Rate Limits

Google AI free tier limits (as of 2024):
- **Requests per minute**: 60 RPM
- **Tokens per minute**: Varies by model
- Pipeline includes automatic rate limiting (2s delays)

## 🔄 Future Enhancements

- [ ] Direct integration with video generation APIs
- [ ] Multi-language support
- [ ] Voice cloning options
- [ ] Batch processing multiple stories
- [ ] Progress saving/resume functionality
- [ ] Video assembly and rendering

## 📝 License

MIT License - feel free to use and modify for your projects

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 💬 Support

For issues or questions:
- Check the troubleshooting section
- Review Google AI documentation: https://ai.google.dev/
- Open an issue on GitHub

## 🎬 Example Use Cases

- **YouTube Shorts**: Quick story videos
- **Educational Content**: Animated lessons
- **Marketing Videos**: Product stories
- **Creative Projects**: Film pre-visualization
- **Audiobook Production**: Chapter narration

---
