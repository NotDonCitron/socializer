"""
Human-like interaction utilities for browser automation.

Provides natural timing, mouse movements, and typing patterns to reduce
bot detection on platforms like TikTok and Instagram.
"""
import random
import math
import asyncio
from typing import Optional, Tuple
from playwright.sync_api import Page, Locator


def human_delay(min_ms: int = 200, max_ms: int = 2000) -> float:
    """
    Returns a delay following lognormal distribution (more natural than uniform).
    
    Lognormal produces mostly shorter delays with occasional longer pauses,
    mimicking real human behavior patterns.
    
    Args:
        min_ms: Minimum delay in milliseconds
        max_ms: Maximum delay in milliseconds
        
    Returns:
        Delay in milliseconds
    """
    # Lognormal with mean ~500ms, moderate variance
    delay = random.lognormvariate(0, 0.5) * 500 + min_ms
    return min(max_ms, max(min_ms, delay))


def typing_delay(base_ms: int = 80, variance: int = 30) -> float:
    """
    Returns keystroke timing with Gaussian variance.
    
    Real typing has variable inter-key intervals based on
    finger positions, familiarity with words, etc.
    
    Args:
        base_ms: Average typing speed in milliseconds
        variance: Standard deviation
        
    Returns:
        Delay between keystrokes in milliseconds
    """
    delay = random.gauss(base_ms, variance)
    return max(30, min(200, delay))  # Clamp between 30-200ms


def thinking_pause_chance() -> bool:
    """
    Returns True ~10% of the time to simulate "thinking" pauses.
    """
    return random.random() < 0.1


def random_offset(box: dict, bias_center: float = 0.4) -> Tuple[float, float]:
    """
    Calculate a random click position within an element's bounding box.
    
    Biased toward center to avoid edge clicks that look robotic.
    
    Args:
        box: Bounding box dict with 'x', 'y', 'width', 'height'
        bias_center: Range around center (0.4 = middle 40%)
        
    Returns:
        Tuple of (x, y) coordinates
    """
    offset_range = (1 - bias_center) / 2
    x = box['x'] + box['width'] * (offset_range + random.random() * bias_center)
    y = box['y'] + box['height'] * (offset_range + random.random() * bias_center)
    return x, y


def bezier_steps(start: Tuple[float, float], end: Tuple[float, float], num_steps: int = 20) -> list:
    """
    Generate points along a quadratic Bezier curve for natural mouse movement.
    
    Uses a random control point to create curved, human-like paths.
    
    Args:
        start: Starting (x, y) coordinates
        end: Ending (x, y) coordinates
        num_steps: Number of points to generate
        
    Returns:
        List of (x, y) tuples along the curve
    """
    # Random control point for curve variation
    mid_x = (start[0] + end[0]) / 2 + random.uniform(-100, 100)
    mid_y = (start[1] + end[1]) / 2 + random.uniform(-50, 50)
    
    points = []
    for i in range(num_steps + 1):
        t = i / num_steps
        # Quadratic Bezier formula: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
        x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * mid_x + t ** 2 * end[0]
        y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * mid_y + t ** 2 * end[1]
        points.append((x, y))
    
    return points


def human_type(page: Page, selector: str, text: str, clear_first: bool = True) -> None:
    """
    Type text with human-like timing variations.
    
    Includes variable keystroke delays and occasional longer pauses
    to simulate natural typing patterns.
    
    Args:
        page: Playwright Page object
        selector: CSS selector for the input element
        text: Text to type
        clear_first: Whether to clear existing content first
    """
    element = page.query_selector(selector)
    if not element:
        raise ValueError(f"Element not found: {selector}")
    
    element.click()
    page.wait_for_timeout(random.randint(100, 300))
    
    if clear_first:
        page.keyboard.press("Control+A")
        page.wait_for_timeout(50)
        page.keyboard.press("Backspace")
        page.wait_for_timeout(random.randint(100, 200))
    
    for char in text:
        page.keyboard.type(char)
        page.wait_for_timeout(typing_delay())
        
        # Occasional thinking pause
        if thinking_pause_chance():
            page.wait_for_timeout(random.randint(300, 800))


def human_click(page: Page, selector: str, use_bezier: bool = True) -> None:
    """
    Click an element with human-like mouse movement.
    
    Moves the mouse in a curved path to a random point within
    the element before clicking.
    
    Args:
        page: Playwright Page object
        selector: CSS selector for the element to click
        use_bezier: Whether to use curved mouse movement
    """
    element = page.query_selector(selector)
    if not element:
        raise ValueError(f"Element not found: {selector}")
    
    box = element.bounding_box()
    if not box:
        # Element may not be visible, try regular click
        element.click()
        return
    
    target_x, target_y = random_offset(box)
    
    if use_bezier:
        # Get current mouse position (approximate from viewport center if unknown)
        current = page.evaluate("() => ({ x: window.innerWidth / 2, y: window.innerHeight / 2 })")
        start = (current['x'], current['y'])
        end = (target_x, target_y)
        
        steps = bezier_steps(start, end, random.randint(10, 25))
        for x, y in steps:
            page.mouse.move(x, y)
            page.wait_for_timeout(random.randint(5, 15))
    else:
        page.mouse.move(target_x, target_y, steps=random.randint(10, 25))
    
    page.wait_for_timeout(random.randint(50, 150))
    page.mouse.click(target_x, target_y)


def wait_human(page: Page, action: str = "general") -> None:
    """
    Wait with human-like timing based on action type.
    
    Args:
        page: Playwright Page object
        action: Type of action ('click', 'type', 'navigate', 'general')
    """
    delays = {
        'click': (100, 500),
        'type': (50, 200),
        'navigate': (1000, 3000),
        'general': (200, 1000),
    }
    
    min_ms, max_ms = delays.get(action, (200, 1000))
    page.wait_for_timeout(human_delay(min_ms, max_ms))


def scroll_naturally(page: Page, direction: str = "down", amount: int = 300) -> None:
    """
    Scroll the page with natural, variable speed.
    
    Args:
        page: Playwright Page object
        direction: 'up' or 'down'
        amount: Approximate pixels to scroll
    """
    multiplier = -1 if direction == "up" else 1
    actual_amount = amount + random.randint(-50, 50)
    
    # Scroll in small increments for natural effect
    steps = random.randint(3, 7)
    per_step = actual_amount // steps
    
    for _ in range(steps):
        page.mouse.wheel(0, per_step * multiplier)
        page.wait_for_timeout(random.randint(50, 150))
