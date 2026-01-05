"""
Engagement API Endpoints

FastAPI application for programmatic engagement control.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from radar.models import EngagementAction, EngagementResult, EngagementActionType, EngagementPlatform
from radar.engagement import EngagementManager
from radar.browser import BrowserManager
import os

app = FastAPI(
    title="Socializer Engagement API",
    description="API for social media engagement automation",
    version="0.1.0"
)

# Global engagement manager
engagement_manager = EngagementManager()

class EngagementRequest(BaseModel):
    """Request model for engagement actions."""
    platform: str
    action_type: str
    target_identifier: str
    metadata: Optional[dict] = None

class BatchRequest(BaseModel):
    """Request model for batch engagement."""
    platform: str
    actions: List[dict]
    settings: Optional[dict] = None

@app.on_event("startup")
async def startup_event():
    """Initialize automators on startup."""
    # Initialize browser manager
    engagement_manager.browser_manager = BrowserManager()

    # Initialize both platforms (lazy initialization)
    print("Engagement API started. Automators will initialize on first use.")

@app.post("/engage/like", response_model=dict)
async def like_content(request: EngagementRequest):
    """Like a post or video."""
    try:
        # Initialize appropriate automator
        if not _initialize_automator(request.platform):
            raise HTTPException(status_code=500, detail="Failed to initialize automator")

        # Execute like action
        action = EngagementAction(
            action_type=EngagementActionType.LIKE,
            platform=EngagementPlatform[request.platform.upper()],
            target_identifier=request.target_identifier
        )

        result = _execute_action(action)

        return {
            "success": result.success,
            "message": result.message,
            "action_type": "like",
            "platform": request.platform,
            "target": request.target_identifier
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/engage/follow", response_model=dict)
async def follow_user(request: EngagementRequest):
    """Follow a user or creator."""
    try:
        # Initialize appropriate automator
        if not _initialize_automator(request.platform):
            raise HTTPException(status_code=500, detail="Failed to initialize automator")

        # Execute follow action
        action = EngagementAction(
            action_type=EngagementActionType.FOLLOW,
            platform=EngagementPlatform[request.platform.upper()],
            target_identifier=request.target_identifier
        )

        result = _execute_action(action)

        return {
            "success": result.success,
            "message": result.message,
            "action_type": "follow",
            "platform": request.platform,
            "target": request.target_identifier
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/engage/comment", response_model=dict)
async def comment_content(request: EngagementRequest):
    """Comment on a post or video."""
    try:
        # Validate metadata contains comment text
        if not request.metadata or "comment_text" not in request.metadata:
            raise HTTPException(status_code=400, detail="comment_text required in metadata")

        # Initialize appropriate automator
        if not _initialize_automator(request.platform):
            raise HTTPException(status_code=500, detail="Failed to initialize automator")

        # Execute comment action
        action = EngagementAction(
            action_type=EngagementActionType.COMMENT,
            platform=EngagementPlatform[request.platform.upper()],
            target_identifier=request.target_identifier,
            metadata=request.metadata
        )

        result = _execute_action(action)

        return {
            "success": result.success,
            "message": result.message,
            "action_type": "comment",
            "platform": request.platform,
            "target": request.target_identifier,
            "comment_text": request.metadata["comment_text"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/engage/save", response_model=dict)
async def save_content(request: EngagementRequest):
    """Save a post or video."""
    try:
        # Initialize appropriate automator
        if not _initialize_automator(request.platform):
            raise HTTPException(status_code=500, detail="Failed to initialize automator")

        # Execute save action
        action = EngagementAction(
            action_type=EngagementActionType.SAVE,
            platform=EngagementPlatform[request.platform.upper()],
            target_identifier=request.target_identifier
        )

        result = _execute_action(action)

        return {
            "success": result.success,
            "message": result.message,
            "action_type": "save",
            "platform": request.platform,
            "target": request.target_identifier
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/engage/batch", response_model=dict)
async def batch_engagement(request: BatchRequest):
    """Execute a batch of engagement actions."""
    try:
        # Initialize appropriate automator
        if not _initialize_automator(request.platform):
            raise HTTPException(status_code=500, detail="Failed to initialize automator")

        # Create actions from request
        actions = []
        for action_data in request.actions:
            action_type = EngagementActionType[action_data["type"].upper()]
            platform = EngagementPlatform[request.platform.upper()]

            action = EngagementAction(
                action_type=action_type,
                platform=platform,
                target_identifier=action_data["target"],
                metadata=action_data.get("metadata", {})
            )
            actions.append(action)

        # Create and execute batch
        from radar.models import EngagementBatch
        batch = EngagementBatch(
            actions=actions,
            platform=platform,
            settings=request.settings or {}
        )

        results = engagement_manager.execute_batch(batch)

        # Summarize results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return {
            "success": successful > 0,
            "total_actions": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(results)) * 100 if results else 0,
            "platform": request.platform,
            "results": [
                {
                    "action_type": r.action.action_type.value,
                    "target": r.action.target_identifier,
                    "success": r.success,
                    "message": r.message
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/engage/stats", response_model=dict)
async def get_stats():
    """Get engagement statistics."""
    try:
        stats = engagement_manager.get_engagement_stats()
        return {
            "action_counts": stats["action_counts"],
            "last_action_times": stats["last_action_times"],
            "rate_limits": stats["rate_limits"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/engage/reset", response_model=dict)
async def reset_counters():
    """Reset engagement counters."""
    try:
        engagement_manager.reset_counters()
        return {"success": True, "message": "Counters reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _initialize_automator(platform: str) -> bool:
    """Initialize the appropriate automator based on platform."""
    try:
        if platform.lower() == "instagram":
            if not engagement_manager.instagram_automator:
                # Initialize Instagram automator
                if not engagement_manager.initialize_instagram(
                    engagement_manager.browser_manager,
                    "ig_session"
                ):
                    return False

                # Login if not already logged in
                if not hasattr(engagement_manager.instagram_automator, 'page') or not engagement_manager.instagram_automator.page:
                    # Get credentials from environment or use defaults
                    username = os.getenv("IG_USERNAME", "your_username")
                    password = os.getenv("IG_PASSWORD", "your_password")

                    if not engagement_manager.instagram_automator.login(username, password, headless=True):
                        return False

        elif platform.lower() == "tiktok":
            if not engagement_manager.tiktok_automator:
                # Initialize TikTok automator
                if not engagement_manager.initialize_tiktok(
                    engagement_manager.browser_manager,
                    "tiktok_session"
                ):
                    return False

                # Login if not already logged in
                if not hasattr(engagement_manager.tiktok_automator, 'page') or not engagement_manager.tiktok_automator.page:
                    if not engagement_manager.tiktok_automator.login(headless=True):
                        return False

        else:
            raise ValueError(f"Unsupported platform: {platform}")

        return True

    except Exception as e:
        print(f"Error initializing automator: {e}")
        return False

def _execute_action(action: EngagementAction) -> EngagementResult:
    """Execute a single engagement action."""
    try:
        return engagement_manager._execute_single_action(action)
    except Exception as e:
        return EngagementResult(
            action=action,
            success=False,
            message=f"Action execution failed: {e}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)