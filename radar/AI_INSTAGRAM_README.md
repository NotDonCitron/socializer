# Instagram AI Autonomous System - Phase 3

This directory contains the AI-powered autonomous Instagram posting system implemented for Phase 3 of the Instagram automation roadmap.

## 🎯 Overview

Phase 3 introduces true autonomy to the Instagram posting system by:

- **Vision Analysis**: Understanding image content using AI
- **Intelligent Caption Generation**: Creating engaging captions and hashtags
- **Autonomous Decision Making**: Deciding when and what to post based on strategy
- **Continuous Operation**: Monitoring content directories and posting autonomously

## 🏗️ Architecture

### Core Components

#### 1. Vision Analysis (`llm/vision.py`)
- **Purpose**: Analyze images to understand content, mood, objects, and context
- **Providers**: OpenAI GPT-4V or Google Gemini Vision
- **Output**: Structured analysis including objects, mood, colors, scene, people count, activities

#### 2. Caption Generation (`llm/base.py`, `llm/gemini.py`)
- **Purpose**: Generate Instagram-optimized captions and hashtags
- **Input**: Vision analysis results
- **Features**: Audience-specific tone, theme alignment, engagement optimization

#### 3. Decision Making (`ai_decision_maker.py`)
- **Purpose**: Determine posting strategy and timing
- **Factors**: Content quality, relevance, timing, frequency limits
- **Decisions**: Post now, post later, queue, or skip

#### 4. AI Automator (`instagram_ai_automator.py`)
- **Purpose**: Orchestrate the entire AI pipeline
- **Features**: Content monitoring, processing pipeline, autonomous operation

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -e .
pip install openai google-generativeai  # AI dependencies
```

### 2. Set Environment Variables

```bash
# Required: Choose one vision provider
export OPENAI_API_KEY="your-openai-key"
# OR
export GEMINI_API_KEY="your-gemini-key"

# Optional: For actual posting
export INSTAGRAM_USERNAME="your-username"
export INSTAGRAM_PASSWORD="your-password"
```

### 3. Run the Demo

```bash
python examples/instagram_ai_autonomous.py
```

## 📁 File Structure

```
radar/
├── llm/
│   ├── vision.py           # Vision analysis with GPT-4V/Gemini
│   ├── base.py            # Extended LLM interface
│   └── gemini.py          # Caption generation implementation
├── ai_decision_maker.py   # Autonomous decision logic
├── instagram_ai_automator.py  # Main AI orchestrator
└── AI_INSTAGRAM_README.md    # This documentation

examples/
└── instagram_ai_autonomous.py  # Complete demo script

content_to_post/           # Directory for content to be processed
```

## 🎨 Configuration

### Account Strategy

Customize your posting strategy in the demo script:

```python
strategy = AccountStrategy(
    target_audience="lifestyle",  # general, lifestyle, business, creative
    posting_frequency="moderate", # low, moderate, high
    preferred_times=["08:00", "12:00", "18:00", "20:00"],
    content_themes=["nature", "urban", "people"],
    avoid_hashtags=["spam", "bot"]
)
```

### Vision Provider

Choose your preferred vision API:

```bash
export VISION_PROVIDER="openai"  # or "gemini"
```

## 🔄 AI Pipeline Flow

1. **Content Discovery**: Scan `content_to_post/` directory for new images
2. **Vision Analysis**: Extract objects, mood, scene, colors from image
3. **Content Evaluation**: Score quality and relevance to account strategy
4. **Caption Generation**: Create engaging caption and hashtags using LLM
5. **Decision Making**: Determine if/when to post based on strategy
6. **Posting**: Upload to Instagram with AI-generated content
7. **Learning**: Record posting success for future decisions

## 📊 Decision Making Logic

### Quality Score (0-1)
- **+0.2**: Clear, identifiable objects
- **+0.15**: Positive mood (happy, peaceful, beautiful)
- **+0.1**: People present or interesting scenes
- **-0.1**: Too much text overlay

### Relevance Score (0-1)
- **+0.3**: Matches account themes perfectly
- **+0.2**: Aligns with target audience
- **Base 0.5**: General content

### Posting Decisions
- **POST_NOW**: High quality + relevance + optimal timing
- **POST_LATER**: Good content, schedule for preferred time
- **QUEUE**: Good content, save for tomorrow
- **SKIP**: Low quality or irrelevant content

## ⚠️ Important Notes

### Rate Limits & Ethics
- **Instagram Limits**: Respect posting frequency to avoid bans
- **API Costs**: Vision analysis has costs per image
- **Human Oversight**: Monitor autonomous operation initially
- **Test Accounts**: Never use production accounts for testing

### Error Handling
- Automatic fallback to basic captions if AI fails
- Logging of all decisions and actions
- Graceful degradation when APIs are unavailable

### Performance Considerations
- Vision analysis: ~3-10 seconds per image
- Caption generation: ~2-5 seconds
- Batch processing recommended for multiple images

## 🔧 Customization

### Custom Vision Prompts

Modify prompts in `vision.py` for different analysis focuses:

```python
prompt = """
Analyze this image for [your specific criteria]...
"""
```

### Account-Specific Instructions

Add custom instructions in `ai_decision_maker.py`:

```python
def _get_custom_instructions(self):
    return "Focus on [your brand voice] and emphasize [key themes]"
```

## 📈 Monitoring & Analytics

Track performance through logs and status:

```python
status = automator.get_status()
print(f"Daily posts: {status['daily_post_count']}")
print(f"Content processed: {status['processed_files_count']}")
```

## 🚀 Production Deployment

For production use:

1. **Monitoring**: Set up log aggregation
2. **Backups**: Regular session and configuration backups
3. **Scaling**: Consider multiple accounts with separate automators
4. **A/B Testing**: Test different strategies and prompts
5. **Cost Management**: Monitor API usage and optimize

## 🤝 Contributing

When extending Phase 3:

1. Maintain separation of concerns (vision, decisions, posting)
2. Add comprehensive error handling
3. Include logging for all major operations
4. Test with various image types and scenarios
5. Document API changes and new features

## 📚 Next Steps (Phase 4)

Phase 3 enables autonomous operation. Phase 4 focuses on:
- Scaling to multiple accounts
- Advanced engagement features
- Real-time performance monitoring
- Migration to async architectures

---

**Remember**: This system is for educational purposes. Always respect platform terms of service and community guidelines. Use test accounts and implement human oversight for production scenarios.