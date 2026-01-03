# Socializer Roadmap

## 🏗️ Phase 1: Foundation (Current Status)
- [x] **TikTok Upload Automation**: Basic web upload works.
- [x] **Session Management**: Persistent browser contexts to avoid logins.
- [x] **Content Management**: Centralized `radar/content.py` for Hashtag Presets.
- [x] **Interactive Mode**: `tiktok_interactive.py` updated.
- [ ] **Fully Automated Script**: `tiktok_auto.py` created but needs robust error testing.

## 🧠 Phase 2: AI Intelligence (The Vision)
- [ ] **Smart Caption Stub**: Implement the interface for `generate_smart_caption`.
- [ ] **Visual Analysis**: Integrate Gemini/CopilotKit to "see" the video frame.
- [ ] **Context Awareness**: Generate hashtags based on video content (e.g., detect "coding", "gaming").
- [ ] **Tone Selection**: Allow user to pick "Funny", "Professional", "Hype" vibe.

## 🚀 Phase 3: Workflow & Scale
- [ ] **Queue System**: Plan posts for the future.
- [ ] **Approval Interface**: Simple UI to check AI suggestions before posting.
- [ ] **Multi-Platform**: Re-activate/Fix Instagram and add YouTube Shorts.

## 🔧 Technical Debt & Cleanup
- [ ] Refactor `TikTokAutomator` to be more resilient to UI changes.
- [ ] Add unit tests for `ContentManager`.
