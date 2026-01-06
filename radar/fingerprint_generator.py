"""
Browser fingerprint generator for anti-detect browser functionality.

Generates and manages persistent browser fingerprints that remain consistent
across browser sessions, similar to Dolphin Anty's approach.

Features:
- Canvas fingerprinting for WebGL and 2D rendering
- Audio context fingerprinting
- WebGL vendor/renderer spoofing
- Font enumeration and spoofing
- Plugin enumeration
- Hardware concurrency and device memory simulation
- Persistent fingerprint storage and retrieval
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import json
import sqlite3
import os
import random
import string
from datetime import datetime
from pathlib import Path
import base64
import zlib


@dataclass
class BrowserFingerprint:
    """Complete browser fingerprint for anti-detection."""
    # Basic browser properties
    user_agent: str
    viewport: Dict[str, int]  # width, height
    timezone: str
    language: str
    platform: str

    # Hardware properties
    hardware_concurrency: int
    device_memory: float
    screen_resolution: Dict[str, int]  # width, height
    color_depth: int
    pixel_ratio: float

    # WebGL properties
    webgl_vendor: str
    webgl_renderer: str
    webgl_version: str
    webgl_shading_language_version: str

    # Canvas properties
    canvas_fingerprint: str
    canvas_webgl_fingerprint: str

    # Audio properties
    audio_fingerprint: str

    # Enumeration properties
    fonts: List[str]
    plugins: List[str]

    # Anti-detection properties
    webdriver: bool = False
    chrome_runtime: bool = True
    permissions: Dict[str, str] = field(default_factory=dict)

    # Metadata
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0

    def to_playwright_context_options(self) -> Dict[str, Any]:
        """Convert fingerprint to Playwright context options."""
        return {
            "user_agent": self.user_agent,
            "viewport": self.viewport,
            "device_scale_factor": self.pixel_ratio,
            "is_mobile": self.platform.lower().find("mobile") != -1,
            "has_touch": self.platform.lower().find("mobile") != -1,
            "color_scheme": "light",
            "locale": self.language,
            "timezone_id": self.timezone,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize fingerprint to dictionary."""
        return {
            "id": self.id,
            "user_agent": self.user_agent,
            "viewport": self.viewport,
            "timezone": self.timezone,
            "language": self.language,
            "platform": self.platform,
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory,
            "screen_resolution": self.screen_resolution,
            "color_depth": self.color_depth,
            "pixel_ratio": self.pixel_ratio,
            "webgl_vendor": self.webgl_vendor,
            "webgl_renderer": self.webgl_renderer,
            "webgl_version": self.webgl_version,
            "webgl_shading_language_version": self.webgl_shading_language_version,
            "canvas_fingerprint": self.canvas_fingerprint,
            "canvas_webgl_fingerprint": self.canvas_webgl_fingerprint,
            "audio_fingerprint": self.audio_fingerprint,
            "fonts": self.fonts,
            "plugins": self.plugins,
            "webdriver": self.webdriver,
            "chrome_runtime": self.chrome_runtime,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "usage_count": self.usage_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrowserFingerprint":
        """Deserialize fingerprint from dictionary."""
        return cls(
            id=data.get("id"),
            user_agent=data["user_agent"],
            viewport=data["viewport"],
            timezone=data["timezone"],
            language=data["language"],
            platform=data["platform"],
            hardware_concurrency=data["hardware_concurrency"],
            device_memory=data["device_memory"],
            screen_resolution=data["screen_resolution"],
            color_depth=data["color_depth"],
            pixel_ratio=data["pixel_ratio"],
            webgl_vendor=data["webgl_vendor"],
            webgl_renderer=data["webgl_renderer"],
            webgl_version=data["webgl_version"],
            webgl_shading_language_version=data["webgl_shading_language_version"],
            canvas_fingerprint=data["canvas_fingerprint"],
            canvas_webgl_fingerprint=data["canvas_webgl_fingerprint"],
            audio_fingerprint=data["audio_fingerprint"],
            fonts=data["fonts"],
            plugins=data["plugins"],
            webdriver=data.get("webdriver", False),
            chrome_runtime=data.get("chrome_runtime", True),
            permissions=data.get("permissions", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used=datetime.fromisoformat(data["last_used"]),
            usage_count=data.get("usage_count", 0)
        )


class FingerprintGenerator:
    """
    Generates and manages persistent browser fingerprints.

    Features:
    - Generate realistic browser fingerprints
    - Store and retrieve fingerprints from database
    - Apply fingerprints to Playwright contexts
    - Canvas and WebGL fingerprinting
    - Audio context fingerprinting
    """

    def __init__(self, db_path: str = "data/radar.sqlite"):
        """
        Initialize fingerprint generator.

        Args:
            db_path: Path to SQLite database for fingerprint storage
        """
        self.db_path = db_path
        self._fingerprints: Dict[str, BrowserFingerprint] = {}
        self._init_database()

    def _init_database(self):
        """Initialize SQLite tables for fingerprint storage."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fingerprints (
                    id TEXT PRIMARY KEY,
                    user_agent TEXT NOT NULL,
                    viewport TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    language TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    hardware_concurrency INTEGER NOT NULL,
                    device_memory REAL NOT NULL,
                    screen_resolution TEXT NOT NULL,
                    color_depth INTEGER NOT NULL,
                    pixel_ratio REAL NOT NULL,
                    webgl_vendor TEXT NOT NULL,
                    webgl_renderer TEXT NOT NULL,
                    webgl_version TEXT NOT NULL,
                    webgl_shading_language_version TEXT NOT NULL,
                    canvas_fingerprint TEXT NOT NULL,
                    canvas_webgl_fingerprint TEXT NOT NULL,
                    audio_fingerprint TEXT NOT NULL,
                    fonts TEXT NOT NULL,
                    plugins TEXT NOT NULL,
                    webdriver INTEGER DEFAULT 0,
                    chrome_runtime INTEGER DEFAULT 1,
                    permissions TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def _generate_id(self) -> str:
        """Generate a unique fingerprint ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def generate_fingerprint(self, platform: str = "desktop") -> BrowserFingerprint:
        """
        Generate a new browser fingerprint.

        Args:
            platform: "desktop" or "mobile"

        Returns:
            Generated BrowserFingerprint
        """
        if platform == "mobile":
            return self._generate_mobile_fingerprint()
        else:
            return self._generate_desktop_fingerprint()

    def _generate_desktop_fingerprint(self) -> BrowserFingerprint:
        """Generate a desktop browser fingerprint."""
        # Common desktop configurations
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 1600, "height": 900},
        ]

        timezones = [
            "America/New_York", "America/Chicago", "America/Denver",
            "America/Los_Angeles", "Europe/London", "Europe/Berlin",
            "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
        ]

        languages = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "ja-JP"]

        # Hardware properties
        hardware_concurrency = random.choice([4, 6, 8, 12, 16])
        device_memory = random.choice([4, 8, 16, 32])

        # Screen resolution (usually matches viewport for desktop)
        screen_res = random.choice(viewports)

        # User agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

        # WebGL properties
        webgl_vendors = ["Google Inc.", "Intel Inc.", "NVIDIA Corporation", "AMD"]
        webgl_renderers = [
            "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "ANGLE (AMD, Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "Intel(R) UHD Graphics 620",
            "NVIDIA GeForce GTX 1060/PCIe/SSE2",
            "AMD Radeon RX 580"
        ]

        # Generate fingerprints
        canvas_fingerprint = self._generate_canvas_fingerprint()
        canvas_webgl_fingerprint = self._generate_webgl_fingerprint()
        audio_fingerprint = self._generate_audio_fingerprint()

        # Font lists (subset of common fonts)
        font_lists = [
            ["Arial", "Calibri", "Cambria", "Candara", "Consolas", "Constantia", "Corbel", "Courier New"],
            ["Arial", "Helvetica", "Times New Roman", "Courier", "Courier New", "Verdana", "Georgia"],
            ["Arial", "Calibri", "Cambria", "Candara", "Consolas", "Constantia", "Corbel", "Courier New", "Franklin Gothic"],
        ]

        # Plugin lists (Chrome extensions)
        plugin_lists = [
            ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"],
            ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client", "WebKit built-in PDF"],
            ["Chrome PDF Plugin", "Chrome PDF Viewer"],
        ]

        fingerprint = BrowserFingerprint(
            user_agent=random.choice(user_agents),
            viewport=random.choice(viewports),
            timezone=random.choice(timezones),
            language=random.choice(languages),
            platform="Win32",  # Windows desktop
            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory,
            screen_resolution=screen_res,
            color_depth=24,
            pixel_ratio=1.0,
            webgl_vendor=random.choice(webgl_vendors),
            webgl_renderer=random.choice(webgl_renderers),
            webgl_version="WebGL 1.0 (OpenGL ES 2.0 Chromium)",
            webgl_shading_language_version="WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
            canvas_fingerprint=canvas_fingerprint,
            canvas_webgl_fingerprint=canvas_webgl_fingerprint,
            audio_fingerprint=audio_fingerprint,
            fonts=random.choice(font_lists),
            plugins=random.choice(plugin_lists),
        )

        return fingerprint

    def _generate_mobile_fingerprint(self) -> BrowserFingerprint:
        """Generate a mobile browser fingerprint."""
        # Mobile viewports and properties
        mobile_viewports = [
            {"width": 412, "height": 915},  # Pixel 3
            {"width": 390, "height": 844},  # iPhone 12
            {"width": 428, "height": 926},  # iPhone 12 Pro Max
            {"width": 360, "height": 740},  # Samsung Galaxy S20
        ]

        mobile_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ]

        mobile_platforms = ["iPhone", "Linux armv8l", "iPhone"]

        # Generate fingerprints
        canvas_fingerprint = self._generate_canvas_fingerprint()
        canvas_webgl_fingerprint = self._generate_webgl_fingerprint()
        audio_fingerprint = self._generate_audio_fingerprint()

        fingerprint = BrowserFingerprint(
            user_agent=random.choice(mobile_user_agents),
            viewport=random.choice(mobile_viewports),
            timezone="America/New_York",  # Common default
            language="en-US",
            platform=random.choice(mobile_platforms),
            hardware_concurrency=random.choice([2, 4, 8]),
            device_memory=random.choice([2, 4, 6, 8]),
            screen_resolution={"width": 1080, "height": 2340},  # Common mobile resolution
            color_depth=24,
            pixel_ratio=random.choice([2.0, 2.5, 3.0]),
            webgl_vendor="Apple Inc.",  # iOS default
            webgl_renderer="Apple GPU",
            webgl_version="WebGL 1.0 (OpenGL ES 2.0 Chromium)",
            webgl_shading_language_version="WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
            canvas_fingerprint=canvas_fingerprint,
            canvas_webgl_fingerprint=canvas_webgl_fingerprint,
            audio_fingerprint=audio_fingerprint,
            fonts=["Arial", "Helvetica", "Times New Roman"],
            plugins=["Chrome PDF Plugin"],  # Minimal on mobile
        )

        return fingerprint

    def _generate_canvas_fingerprint(self) -> str:
        """Generate a canvas 2D fingerprint."""
        # Simulate canvas rendering characteristics
        canvas_data = {
            "text_rendering": random.choice(["subpixel-antialiased", "antialiased", "grayscale"]),
            "font_smoothing": random.choice(["antialiased", "subpixel-antialiased"]),
            "line_width": random.uniform(0.5, 1.5),
            "text_baseline_offset": random.uniform(-0.1, 0.1),
        }

        # Create a hash of the canvas characteristics
        canvas_str = json.dumps(canvas_data, sort_keys=True)
        return hashlib.sha256(canvas_str.encode()).hexdigest()[:16]

    def _generate_webgl_fingerprint(self) -> str:
        """Generate a WebGL fingerprint."""
        webgl_data = {
            "max_texture_size": random.choice([4096, 8192, 16384]),
            "max_renderbuffer_size": random.choice([4096, 8192]),
            "max_viewport_dims": [random.choice([4096, 8192]), random.choice([4096, 8192])],
            "renderer_unmasked": random.choice([
                "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0)",
                "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0)",
                "Apple GPU"
            ]),
            "vendor_unmasked": random.choice(["Intel Inc.", "NVIDIA Corporation", "Apple Inc."]),
        }

        webgl_str = json.dumps(webgl_data, sort_keys=True)
        return hashlib.sha256(webgl_str.encode()).hexdigest()[:16]

    def _generate_audio_fingerprint(self) -> str:
        """Generate an audio context fingerprint."""
        audio_data = {
            "sample_rate": random.choice([44100, 48000, 96000]),
            "channel_count": random.choice([2, 1]),
            "max_channel_count": random.choice([2, 6, 8]),
            "state": "running",
            "current_time": random.uniform(0.001, 0.01),
        }

        audio_str = json.dumps(audio_data, sort_keys=True)
        return hashlib.sha256(audio_str.encode()).hexdigest()[:16]

    def save_fingerprint(self, fingerprint: BrowserFingerprint) -> str:
        """
        Save fingerprint to database.

        Args:
            fingerprint: Fingerprint to save

        Returns:
            Fingerprint ID
        """
        if not fingerprint.id:
            fingerprint.id = self._generate_id()

        self._fingerprints[fingerprint.id] = fingerprint

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO fingerprints
                (id, user_agent, viewport, timezone, language, platform,
                 hardware_concurrency, device_memory, screen_resolution, color_depth, pixel_ratio,
                 webgl_vendor, webgl_renderer, webgl_version, webgl_shading_language_version,
                 canvas_fingerprint, canvas_webgl_fingerprint, audio_fingerprint,
                 fonts, plugins, webdriver, chrome_runtime, permissions,
                 created_at, last_used, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fingerprint.id,
                fingerprint.user_agent,
                json.dumps(fingerprint.viewport),
                fingerprint.timezone,
                fingerprint.language,
                fingerprint.platform,
                fingerprint.hardware_concurrency,
                fingerprint.device_memory,
                json.dumps(fingerprint.screen_resolution),
                fingerprint.color_depth,
                fingerprint.pixel_ratio,
                fingerprint.webgl_vendor,
                fingerprint.webgl_renderer,
                fingerprint.webgl_version,
                fingerprint.webgl_shading_language_version,
                fingerprint.canvas_fingerprint,
                fingerprint.canvas_webgl_fingerprint,
                fingerprint.audio_fingerprint,
                json.dumps(fingerprint.fonts),
                json.dumps(fingerprint.plugins),
                1 if fingerprint.webdriver else 0,
                1 if fingerprint.chrome_runtime else 0,
                json.dumps(fingerprint.permissions),
                fingerprint.created_at.isoformat(),
                fingerprint.last_used.isoformat(),
                fingerprint.usage_count
            ))
            conn.commit()

        return fingerprint.id

    def load_fingerprint(self, fingerprint_id: str) -> Optional[BrowserFingerprint]:
        """
        Load fingerprint from database.

        Args:
            fingerprint_id: Fingerprint ID to load

        Returns:
            BrowserFingerprint or None if not found
        """
        if fingerprint_id in self._fingerprints:
            return self._fingerprints[fingerprint_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM fingerprints WHERE id = ?", (fingerprint_id,)).fetchone()

            if row:
                fingerprint = BrowserFingerprint(
                    id=row["id"],
                    user_agent=row["user_agent"],
                    viewport=json.loads(row["viewport"]),
                    timezone=row["timezone"],
                    language=row["language"],
                    platform=row["platform"],
                    hardware_concurrency=row["hardware_concurrency"],
                    device_memory=row["device_memory"],
                    screen_resolution=json.loads(row["screen_resolution"]),
                    color_depth=row["color_depth"],
                    pixel_ratio=row["pixel_ratio"],
                    webgl_vendor=row["webgl_vendor"],
                    webgl_renderer=row["webgl_renderer"],
                    webgl_version=row["webgl_version"],
                    webgl_shading_language_version=row["webgl_shading_language_version"],
                    canvas_fingerprint=row["canvas_fingerprint"],
                    canvas_webgl_fingerprint=row["canvas_webgl_fingerprint"],
                    audio_fingerprint=row["audio_fingerprint"],
                    fonts=json.loads(row["fonts"]),
                    plugins=json.loads(row["plugins"]),
                    webdriver=bool(row["webdriver"]),
                    chrome_runtime=bool(row["chrome_runtime"]),
                    permissions=json.loads(row["permissions"]) if row["permissions"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_used=datetime.fromisoformat(row["last_used"]),
                    usage_count=row["usage_count"]
                )

                self._fingerprints[fingerprint_id] = fingerprint
                return fingerprint

        return None

    def get_all_fingerprints(self) -> List[BrowserFingerprint]:
        """Get all fingerprints from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM fingerprints ORDER BY last_used DESC").fetchall()

            fingerprints = []
            for row in rows:
                fingerprint = BrowserFingerprint(
                    id=row["id"],
                    user_agent=row["user_agent"],
                    viewport=json.loads(row["viewport"]),
                    timezone=row["timezone"],
                    language=row["language"],
                    platform=row["platform"],
                    hardware_concurrency=row["hardware_concurrency"],
                    device_memory=row["device_memory"],
                    screen_resolution=json.loads(row["screen_resolution"]),
                    color_depth=row["color_depth"],
                    pixel_ratio=row["pixel_ratio"],
                    webgl_vendor=row["webgl_vendor"],
                    webgl_renderer=row["webgl_renderer"],
                    webgl_version=row["webgl_version"],
                    webgl_shading_language_version=row["webgl_shading_language_version"],
                    canvas_fingerprint=row["canvas_fingerprint"],
                    canvas_webgl_fingerprint=row["canvas_webgl_fingerprint"],
                    audio_fingerprint=row["audio_fingerprint"],
                    fonts=json.loads(row["fonts"]),
                    plugins=json.loads(row["plugins"]),
                    webdriver=bool(row["webdriver"]),
                    chrome_runtime=bool(row["chrome_runtime"]),
                    permissions=json.loads(row["permissions"]) if row["permissions"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_used=datetime.fromisoformat(row["last_used"]),
                    usage_count=row["usage_count"]
                )

                self._fingerprints[fingerprint.id] = fingerprint
                fingerprints.append(fingerprint)

            return fingerprints

    def update_usage(self, fingerprint_id: str):
        """Update fingerprint usage statistics."""
        fingerprint = self._fingerprints.get(fingerprint_id)
        if fingerprint:
            fingerprint.last_used = datetime.now()
            fingerprint.usage_count += 1

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE fingerprints
                    SET last_used = ?, usage_count = ?
                    WHERE id = ?
                """, (fingerprint.last_used.isoformat(), fingerprint.usage_count, fingerprint_id))
                conn.commit()

    def delete_fingerprint(self, fingerprint_id: str):
        """Delete fingerprint from database."""
        self._fingerprints.pop(fingerprint_id, None)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM fingerprints WHERE id = ?", (fingerprint_id,))
            conn.commit()

    def apply_fingerprint_to_page(self, page, fingerprint: BrowserFingerprint):
        """
        Apply fingerprint properties to a Playwright page.

        This injects JavaScript to spoof navigator properties and canvas fingerprints.
        """
        # Spoof navigator properties
        navigator_script = f"""
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fingerprint.hardware_concurrency}
        }});

        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {fingerprint.device_memory}
        }});

        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fingerprint.platform}'
        }});

        Object.defineProperty(navigator, 'language', {{
            get: () => '{fingerprint.language}'
        }});

        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{fingerprint.language}']
        }});

        // Spoof screen properties
        Object.defineProperty(screen, 'width', {{
            get: () => {fingerprint.screen_resolution['width']}
        }});

        Object.defineProperty(screen, 'height', {{
            get: () => {fingerprint.screen_resolution['height']}
        }});

        Object.defineProperty(screen, 'colorDepth', {{
            get: () => {fingerprint.color_depth}
        }});

        // Spoof webdriver
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => {str(fingerprint.webdriver).lower()}
        }});

        // Fonts enumeration spoofing
        const originalFonts = document.fonts;
        const spoofedFonts = {json.dumps(fingerprint.fonts)};

        document.fonts.values = function*() {{
            for (const font of spoofedFonts) {{
                yield {{ family: font, style: 'normal', weight: '400' }};
            }}
        }};

        // Plugins spoofing
        const spoofedPlugins = {json.dumps(fingerprint.plugins)};
        const pluginArray = [];

        for (let i = 0; i < spoofedPlugins.length; i++) {{
            pluginArray.push({{
                name: spoofedPlugins[i],
                description: spoofedPlugins[i] + ' Plugin',
                filename: 'plugin' + i + '.dll'
            }});
        }}

        Object.defineProperty(navigator, 'plugins', {{
            get: () => pluginArray
        }});

        // Chrome runtime spoofing
        if ({str(fingerprint.chrome_runtime).lower()}) {{
            window.chrome = {{ runtime: {{}} }};
        }}
        """

        page.add_init_script(navigator_script)

        # Canvas fingerprinting spoofing
        canvas_script = f"""
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(x, y, width, height) {{
            const imageData = originalGetImageData.call(this, x, y, width, height);
            // Add slight noise to make fingerprint consistent but not identical
            const noise = '{fingerprint.canvas_fingerprint}';
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] = (imageData.data[i] + noise.charCodeAt(i % noise.length)) % 256;
            }}
            return imageData;
        }};

        // WebGL fingerprinting spoofing
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                return '{fingerprint.webgl_vendor}';
            }}
            if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                return '{fingerprint.webgl_renderer}';
            }}
            return originalGetParameter.call(this, parameter);
        }};

        // Audio context fingerprinting spoofing
        const originalCreateOscillator = AudioContext.prototype.createOscillator;
        AudioContext.prototype.createOscillator = function() {{
            const oscillator = originalCreateOscillator.call(this);
            // Add consistent noise to frequency
            const noise = '{fingerprint.audio_fingerprint}';
            const baseFreq = oscillator.frequency.value;
            oscillator.frequency.value = baseFreq + (noise.charCodeAt(0) * 0.001);
            return oscillator;
        }};
        """

        page.add_init_script(canvas_script)

    def export_fingerprints(self, file_path: str):
        """Export all fingerprints to JSON file."""
        fingerprints = self.get_all_fingerprints()

        data = {
            "fingerprints": [fp.to_dict() for fp in fingerprints],
            "exported_at": datetime.now().isoformat()
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_fingerprints(self, file_path: str) -> int:
        """Import fingerprints from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        count = 0
        for fp_data in data.get("fingerprints", []):
            fingerprint = BrowserFingerprint.from_dict(fp_data)
            self.save_fingerprint(fingerprint)
            count += 1

        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get fingerprint statistics."""
        fingerprints = self.get_all_fingerprints()

        total = len(fingerprints)
        desktop = sum(1 for fp in fingerprints if fp.platform == "Win32")
        mobile = sum(1 for fp in fingerprints if fp.platform in ["iPhone", "Linux armv8l"])
        avg_usage = sum(fp.usage_count for fp in fingerprints) / max(total, 1)

        return {
            "total_fingerprints": total,
            "desktop_fingerprints": desktop,
            "mobile_fingerprints": mobile,
            "average_usage_count": avg_usage
        }