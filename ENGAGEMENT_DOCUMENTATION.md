# Socializer Engagement Features Documentation

## Overview

The Socializer engagement system provides comprehensive social media engagement automation for Instagram and TikTok platforms. This documentation covers all aspects of the engagement features, from basic usage to advanced batch operations.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Engagement Actions](#engagement-actions)
4. [CLI Usage](#cli-usage)
5. [API Endpoints](#api-endpoints)
6. [Batch Operations](#batch-operations)
7. [Rate Limiting & Safety](#rate-limiting--safety)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)
10. [Examples](#examples)
11. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.8+
- Playwright installed (`playwright install chromium`)
- Valid social media accounts with credentials
- Session directories (`ig_session/` and `tiktok_session/`)

### Installation

The engagement features are part of the main Socializer package:

```bash
pip install -e .
```

### Basic Usage

```python
from radar.browser import BrowserManager
from radar.engagement import EngagementManager

with BrowserManager() as manager:
    engagement_manager = EngagementManager()
    engagement_manager.initialize_instagram(manager, "ig_session")

    # Login
    engagement_manager.instagram_automator.login("username", "password")

    # Like a post
    result = engagement_manager.instagram_automator.like_post("https://www.instagram.com/p/EXAMPLE/")
    print(f"Success: {result.success}, Message: {result.message}")
```

## Core Concepts

### Engagement Actions

Engagement actions represent individual social media interactions:

- **Like/Unlike**: Like or unlike posts/videos
- **Follow/Unfollow**: Follow or unfollow users/creators
- **Comment/Reply**: Post comments or replies
- **Save/Unsave**: Save or unsave content
- **Share**: Share content via DM or other methods
- **Story View**: View Instagram stories

### Engagement Platforms

Supported platforms:
- **Instagram**: Posts, reels, stories, profiles
- **TikTok**: Videos, creators, comments

### Engagement Results

All actions return `EngagementResult` objects containing:
- `success`: Boolean indicating success/failure
- `message`: Human-readable result message
- `action`: Original engagement action
- `timestamp`: When the action was executed
- `platform_data`: Platform-specific response data

## Engagement Actions

### Like Content

```python
# Instagram
result = engagement_manager.instagram_automator.like_post("https://www.instagram.com/p/EXAMPLE/")

# TikTok
result = engagement_manager.tiktok_automator.like_video("https://www.tiktok.com/@user/video/123")
```

### Follow Users

```python
# Instagram
result = engagement_manager.instagram_automator.follow_user("username")

# TikTok
result = engagement_manager.tiktok_automator.follow_creator("creator_username")
```

### Comment on Content

```python
# Instagram
result = engagement_manager.instagram_automator.comment_on_post(
    "https://www.instagram.com/p/EXAMPLE/",
    "Great content! 👍"
)

# TikTok
result = engagement_manager.tiktok_automator.comment_on_video(
    "https://www.tiktok.com/@user/video/123",
    "Awesome video! 🔥"
)
```

### Save Content

```python
# Instagram
result = engagement_manager.instagram_automator.save_post("https://www.instagram.com/p/EXAMPLE/")

# TikTok
result = engagement_manager.tiktok_automator.save_video("https://www.tiktok.com/@user/video/123")
```

### Share Content

```python
# Instagram (DM share)
result = engagement_manager.instagram_automator.share_post(
    "https://www.instagram.com/p/EXAMPLE/",
    method="dm"
)

# TikTok (DM share)
result = engagement_manager.tiktok_automator.share_video(
    "https://www.tiktok.com/@user/video/123",
    method="dm"
)
```

## CLI Usage

The CLI provides convenient commands for engagement actions:

### Instagram Commands

```bash
# Like a post
radar engage instagram-like "https://www.instagram.com/p/EXAMPLE/"

# Follow a user
radar engage instagram-follow "username"

# Comment on a post
radar engage instagram-comment "https://www.instagram.com/p/EXAMPLE/" "Great post!"
```

### TikTok Commands

```bash
# Like a video
radar engage tiktok-like "https://www.tiktok.com/@user/video/123"

# Follow a creator
radar engage tiktok-follow "creator_username"

# Comment on a video
radar engage tiktok-comment "https://www.tiktok.com/@user/video/123" "Awesome content!"
```

### Batch Commands

```bash
# Execute batch from JSON config
radar engage batch engagement_config.json
```

## API Endpoints

The engagement API provides REST endpoints for programmatic control:

### Base URL

```
http://localhost:8000
```

### Authentication

API endpoints require valid session cookies. Ensure you're logged in before making requests.

### Endpoints

#### Like Content

```bash
POST /engage/like
{
    "platform": "instagram",
    "target_identifier": "https://www.instagram.com/p/EXAMPLE/"
}
```

#### Follow User

```bash
POST /engage/follow
{
    "platform": "tiktok",
    "target_identifier": "creator_username"
}
```

#### Comment on Content

```bash
POST /engage/comment
{
    "platform": "instagram",
    "target_identifier": "https://www.instagram.com/p/EXAMPLE/",
    "metadata": {
        "comment_text": "Great content!"
    }
}
```

#### Batch Engagement

```bash
POST /engage/batch
{
    "platform": "instagram",
    "actions": [
        {
            "type": "like",
            "target": "https://www.instagram.com/p/EXAMPLE1/"
        },
        {
            "type": "follow",
            "target": "username"
        }
    ],
    "settings": {
        "delay_between_actions": 30,
        "max_retries": 2
    }
}
```

#### Get Statistics

```bash
GET /engage/stats
```

## Batch Operations

Batch operations allow executing multiple engagement actions sequentially with rate limiting.

### Creating a Batch

```python
from radar.models import EngagementAction, EngagementActionType, EngagementPlatform, EngagementBatch

actions = [
    EngagementAction(
        action_type=EngagementActionType.LIKE,
        platform=EngagementPlatform.INSTAGRAM,
        target_identifier="https://www.instagram.com/p/EXAMPLE1/"
    ),
    EngagementAction(
        action_type=EngagementActionType.FOLLOW,
        platform=EngagementPlatform.INSTAGRAM,
        target_identifier="username"
    ),
    EngagementAction(
        action_type=EngagementActionType.COMMENT,
        platform=EngagementPlatform.INSTAGRAM,
        target_identifier="https://www.instagram.com/p/EXAMPLE2/",
        metadata={"comment_text": "Great content!"}
    )
]

batch = EngagementBatch(
    actions=actions,
    platform=EngagementPlatform.INSTAGRAM,
    settings={
        "delay_between_actions": 30,  # seconds
        "max_retries": 2,
        "randomize_order": True,
        "stop_on_failure": False
    }
)
```

### Executing a Batch

```python
results = engagement_manager.execute_batch(batch)

# Process results
for result in results:
    print(f"Action: {result.action.action_type.value}")
    print(f"Target: {result.action.target_identifier}")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print("---")
```

### Batch Configuration File

Create a JSON configuration file for batch operations:

```json
{
    "platform": "instagram",
    "settings": {
        "delay_between_actions": 30,
        "max_retries": 2,
        "randomize_order": true,
        "stop_on_failure": false
    },
    "actions": [
        {
            "type": "like",
            "target": "https://www.instagram.com/p/EXAMPLE1/",
            "metadata": {}
        },
        {
            "type": "follow",
            "target": "username",
            "metadata": {}
        },
        {
            "type": "comment",
            "target": "https://www.instagram.com/p/EXAMPLE2/",
            "metadata": {
                "comment_text": "Great content! 👍"
            }
        }
    ]
}
```

## Rate Limiting & Safety

The engagement system includes built-in rate limiting to prevent detection:

### Rate Limit Settings

```python
rate_limits = {
    EngagementPlatform.INSTAGRAM: {
        'min_delay': 30,  # seconds
        'max_delay': 60,
        'max_actions_per_hour': 120
    },
    EngagementPlatform.TIKTOK: {
        'min_delay': 20,  # seconds
        'max_delay': 45,
        'max_actions_per_hour': 180
    }
}
```

### Anti-Detection Features

- **Human-like delays**: Random delays between actions
- **Randomized order**: Actions can be randomized to avoid patterns
- **Exponential backoff**: Retry failed actions with increasing delays
- **Session monitoring**: Track session health and performance

### Best Practices for Avoiding Detection

1. **Use realistic delays**: Don't perform actions too quickly
2. **Mix action types**: Combine likes, follows, and comments
3. **Randomize targets**: Don't engage with the same users repeatedly
4. **Limit batch sizes**: Keep batches under 50 actions
5. **Use headless mode cautiously**: Some platforms detect headless browsers
6. **Monitor success rates**: High failure rates may indicate detection

## Error Handling

The engagement system provides comprehensive error handling:

### Common Error Types

- **Navigation errors**: Failed to navigate to target URL
- **Element not found**: Engagement buttons not detected
- **Action verification failed**: Could not confirm action success
- **Rate limiting**: Platform rate limits exceeded
- **Session expired**: Login session no longer valid

### Error Recovery

```python
result = engagement_manager.instagram_automator.like_post("https://www.instagram.com/p/EXAMPLE/")

if not result.success:
    print(f"Error: {result.message}")

    # Retry with exponential backoff
    for retry in range(3):
        print(f"Retry {retry + 1}/3...")
        result = engagement_manager.instagram_automator.like_post("https://www.instagram.com/p/EXAMPLE/")
        if result.success:
            break
        time.sleep(2 ** retry)  # Exponential backoff
```

### Batch Error Handling

```python
batch = EngagementBatch(
    actions=actions,
    platform=EngagementPlatform.INSTAGRAM,
    settings={
        "max_retries": 3,  # Automatic retries
        "stop_on_failure": False  # Continue on errors
    }
)

results = engagement_manager.execute_batch(batch)

# Analyze failures
failed_actions = [r for r in results if not r.success]
for failure in failed_actions:
    print(f"Failed: {failure.action.action_type.value} on {failure.action.target_identifier}")
    print(f"Reason: {failure.message}")
```

## Best Practices

### Account Management

1. **Use dedicated accounts**: Don't use personal accounts for automation
2. **Warm up accounts**: Use accounts normally before automating
3. **Limit daily actions**: Stay within platform limits
4. **Use proxies**: Rotate IPs to avoid detection
5. **Monitor account health**: Check for shadowbans or restrictions

### Content Strategy

1. **Engage with relevant content**: Focus on your niche
2. **Use varied comments**: Avoid repetitive or spammy comments
3. **Mix engagement types**: Combine likes, follows, and comments
4. **Follow back**: Engage with users who engage with you
5. **Avoid controversial content**: Stick to safe, positive interactions

### Technical Best Practices

1. **Use session persistence**: Maintain logged-in sessions
2. **Monitor success rates**: Track engagement performance
3. **Implement circuit breakers**: Stop if failure rate is too high
4. **Log all actions**: Maintain detailed engagement logs
5. **Update selectors regularly**: Platform UIs change frequently

## Examples

### Instagram Engagement Demo

See `examples/instagram_engagement_demo.py` for a complete Instagram engagement workflow.

### TikTok Engagement Demo

See `examples/tiktok_engagement_demo.py` for a complete TikTok engagement workflow.

### Batch Engagement Example

See `examples/batch_engagement_example.py` for batch operation examples.

## Troubleshooting

### Common Issues

#### "Element not found" errors

- **Cause**: Platform UI has changed or selectors are outdated
- **Solution**: Update selectors in `radar/selectors.py`
- **Prevention**: Use multiple selector strategies with fallbacks

#### "Login failed" errors

- **Cause**: Invalid credentials or session expired
- **Solution**: Verify credentials and delete session directory
- **Prevention**: Use persistent sessions and monitor login status

#### "Rate limited" errors

- **Cause**: Too many actions in short time
- **Solution**: Increase delays between actions
- **Prevention**: Use built-in rate limiting and monitor success rates

#### "Action verification failed"

- **Cause**: Platform didn't register the action
- **Solution**: Add verification retries with delays
- **Prevention**: Use human-like interaction patterns

### Debugging Tips

1. **Enable debug mode**: Set `DEBUG=1` environment variable
2. **Check screenshots**: Debug screenshots are saved automatically
3. **Monitor console logs**: Use `enable_monitoring()` method
4. **Test selectors**: Use browser dev tools to verify selectors
5. **Start small**: Test with single actions before batches

## Advanced Features

### Custom Engagement Workflows

Create custom engagement strategies:

```python
def smart_engagement_strategy(engagement_manager, target_urls):
    """Custom engagement strategy with varied actions."""
    actions = []

    for url in target_urls:
        # 30% chance to like
        if random.random() < 0.3:
            actions.append(EngagementAction(
                action_type=EngagementActionType.LIKE,
                platform=EngagementPlatform.INSTAGRAM,
                target_identifier=url
            ))

        # 10% chance to comment
        if random.random() < 0.1:
            actions.append(EngagementAction(
                action_type=EngagementActionType.COMMENT,
                platform=EngagementPlatform.INSTAGRAM,
                target_identifier=url,
                metadata={"comment_text": random.choice(["Great!", "Nice!", "Cool!"])}
            ))

    return actions
```

### Engagement Analytics

Track and analyze engagement performance:

```python
def analyze_engagement_results(results):
    """Analyze engagement batch results."""
    by_type = {}
    success_rates = {}

    for result in results:
        action_type = result.action.action_type.value
        if action_type not in by_type:
            by_type[action_type] = {"success": 0, "total": 0}

        by_type[action_type]["total"] += 1
        if result.success:
            by_type[action_type]["success"] += 1

    # Calculate success rates
    for action_type, stats in by_type.items():
        success_rates[action_type] = (stats["success"] / stats["total"]) * 100

    return success_rates
```

### Integration with Content Pipeline

Combine engagement with content creation:

```python
# After posting content, engage with related posts
def post_and_engage(engagement_manager, post_url, related_urls):
    """Post content and engage with related posts."""
    # Post your content (using existing upload methods)
    # ...

    # Then engage with related content
    actions = []
    for url in related_urls:
        actions.append(EngagementAction(
            action_type=EngagementActionType.LIKE,
            platform=EngagementPlatform.INSTAGRAM,
            target_identifier=url
        ))

    batch = EngagementBatch(actions=actions, platform=EngagementPlatform.INSTAGRAM)
    engagement_manager.execute_batch(batch)
```

## Conclusion

The Socializer engagement system provides a powerful, flexible framework for social media engagement automation. By following the best practices and examples in this documentation, you can create sophisticated engagement workflows while minimizing detection risks.

For more information, see the individual example files and the main Socializer documentation.