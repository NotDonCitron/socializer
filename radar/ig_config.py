"""
Instagram Configuration Module.

Centralizes all Instagram-related configuration with environment variable support
for production deployment.
"""
import os
from pathlib import Path
from typing import Optional


# =============================================================================
# Credential Configuration
# =============================================================================

def get_ig_username() -> Optional[str]:
    """Get Instagram username from environment."""
    return os.getenv("IG_USERNAME")


def get_ig_password() -> Optional[str]:
    """Get Instagram password from environment."""
    return os.getenv("IG_PASSWORD")


# =============================================================================
# Session Configuration
# =============================================================================

# Directory for storing browser session data (cookies, local storage)
IG_SESSION_DIR: str = os.getenv("IG_SESSION_DIR", "ig_session")

# Path to cookies file within session directory
IG_COOKIES_PATH: str = os.path.join(IG_SESSION_DIR, "cookies.json")


# =============================================================================
# Retry Configuration
# =============================================================================

# Maximum number of retry attempts for failed operations
IG_MAX_RETRIES: int = int(os.getenv("IG_MAX_RETRIES", "3"))

# Base delay between retries in seconds (exponential backoff applied)
IG_RETRY_DELAY: float = float(os.getenv("IG_RETRY_DELAY", "5.0"))

# Maximum delay between retries in seconds
IG_MAX_RETRY_DELAY: float = float(os.getenv("IG_MAX_RETRY_DELAY", "60.0"))


# =============================================================================
# Timeout Configuration
# =============================================================================

# Default timeout for page navigation in milliseconds
IG_NAV_TIMEOUT: int = int(os.getenv("IG_NAV_TIMEOUT", "30000"))

# Timeout for upload operations in milliseconds (videos can take long)
IG_UPLOAD_TIMEOUT: int = int(os.getenv("IG_UPLOAD_TIMEOUT", "300000"))

# Timeout for login operations in milliseconds
IG_LOGIN_TIMEOUT: int = int(os.getenv("IG_LOGIN_TIMEOUT", "45000"))


# =============================================================================
# Logging Configuration
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
IG_LOG_LEVEL: str = os.getenv("IG_LOG_LEVEL", "INFO")

# Enable debug screenshots
IG_DEBUG_SCREENSHOTS: bool = os.getenv("DEBUG", "0") == "1"

# Directory for debug screenshots
IG_DEBUG_DIR: str = os.getenv("IG_DEBUG_DIR", "debug_shots")


# =============================================================================
# Human Behavior Simulation
# =============================================================================

# Minimum delay between actions in milliseconds
IG_MIN_ACTION_DELAY: int = int(os.getenv("IG_MIN_ACTION_DELAY", "500"))

# Maximum delay between actions in milliseconds
IG_MAX_ACTION_DELAY: int = int(os.getenv("IG_MAX_ACTION_DELAY", "2000"))

# Enable random scrolling behavior
IG_RANDOM_SCROLL: bool = os.getenv("IG_RANDOM_SCROLL", "1") == "1"


# =============================================================================
# Validation
# =============================================================================

def validate_config() -> dict:
    """
    Validate configuration and return status.
    
    Returns:
        dict with 'valid' boolean and 'errors' list
    """
    errors = []
    
    # Check if session directory is writable
    session_path = Path(IG_SESSION_DIR)
    if session_path.exists() and not os.access(session_path, os.W_OK):
        errors.append(f"Session directory not writable: {IG_SESSION_DIR}")
    
    # Validate timeout values
    if IG_NAV_TIMEOUT < 1000:
        errors.append("IG_NAV_TIMEOUT too low (minimum 1000ms)")
    
    if IG_UPLOAD_TIMEOUT < 30000:
        errors.append("IG_UPLOAD_TIMEOUT too low (minimum 30000ms)")
    
    # Validate retry config
    if IG_MAX_RETRIES < 0:
        errors.append("IG_MAX_RETRIES cannot be negative")
    
    if IG_RETRY_DELAY < 0:
        errors.append("IG_RETRY_DELAY cannot be negative")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def has_credentials() -> bool:
    """Check if Instagram credentials are configured."""
    return bool(get_ig_username() and get_ig_password())


def print_config_status():
    """Print current configuration status."""
    print("=" * 50)
    print("Instagram Configuration Status")
    print("=" * 50)
    print(f"Credentials configured: {'yes' if has_credentials() else 'no'}")
    print(f"Session directory: {IG_SESSION_DIR}")
    print(f"Max retries: {IG_MAX_RETRIES}")
    print(f"Retry delay: {IG_RETRY_DELAY}s")
    print(f"Log level: {IG_LOG_LEVEL}")
    print(f"Debug screenshots: {'yes' if IG_DEBUG_SCREENSHOTS else 'no'}")
    
    validation = validate_config()
    if validation["valid"]:
        print("Configuration: OK")
    else:
        print("Configuration: OK")
        for error in validation["errors"]:
            print(f"  - {error}")
    print("=" * 50)


if __name__ == "__main__":
    print_config_status()
