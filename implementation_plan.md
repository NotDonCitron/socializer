# Implementation Plan: Proxy & Session Management System

## Overview
Transform the current single-account socializer into a Dolphin Anty-style multi-account platform with persistent fingerprinting. Each account maintains consistent browser fingerprints, hardware IDs, and session data while supporting proxy rotation. Inspired by Jarvee's architecture but with anti-detect browser capabilities - "full stealth on 1 click" with persistent account identities.

## Types

### Core Data Models
```python
@dataclass
class ProxyConfig:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks5
    country: Optional[str] = None
    provider: Optional[str] = None
    last_used: datetime = field(default_factory=datetime.now)
    success_rate: float = 1.0
    is_active: bool = True

@dataclass
class BrowserFingerprint:
    user_agent: str
    viewport: Dict[str, int]  # width, height
    timezone: str
    language: str
    platform: str
    hardware_concurrency: int
    device_memory: float
    screen_resolution: Dict[str, int]
    color_depth: int
    pixel_ratio: float
    webgl_vendor: str
    webgl_renderer: str
    canvas_fingerprint: str
    audio_fingerprint: str
    fonts: List[str]
    plugins: List[str]
    webdriver: bool = False

@dataclass
class AccountProfile:
    id: str
    platform: EngagementPlatform
    username: str
    password: str  # encrypted
    email: Optional[str] = None
    proxy_id: Optional[str] = None
    fingerprint: BrowserFingerprint  # Persistent fingerprint for this account
    session_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    status: AccountStatus = AccountStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SessionContext:
    account_id: str
    proxy_config: Optional[ProxyConfig]
    browser_context: Any  # Playwright context
    cookies: List[Dict] = field(default_factory=list)
    local_storage: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    is_healthy: bool = True

enum AccountStatus:
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    REQUIRES_VERIFICATION = "requires_verification"

enum ProxyHealth:
    HEALTHY = "healthy"
    SLOW = "slow"
    BLOCKED = "blocked"
    DOWN = "down"
```

## Files

### New Files to Create
- `radar/proxy_manager.py` - Core proxy management and rotation logic
- `radar/account_pool.py` - Multi-account management and session handling
- `radar/session_orchestrator.py` - Coordinates sessions across accounts and proxies
- `radar/fingerprint_generator.py` - Generates and manages persistent browser fingerprints
- `radar/proxy_health_monitor.py` - Proxy validation and health checking
- `radar/session_persistence.py` - Advanced cookie/storage persistence
- `radar/scaling_config.py` - Configuration for multi-account operations
- `radar/proxy_providers/` - Directory for different proxy provider integrations
- `radar/proxy_providers/base.py` - Base proxy provider interface
- `radar/proxy_providers/brightdata.py` - BrightData/Oxylabs integration
- `radar/proxy_providers/smartproxy.py` - SmartProxy integration
- `radar/proxy_providers/custom.py` - Custom proxy list management

### Existing Files to Modify
- `radar/browser.py` - Add proxy support to BrowserManager
- `radar/tiktok.py` - Integrate with session orchestrator
- `radar/instagram.py` - Integrate with session orchestrator
- `radar/cli.py` - Add proxy and account management commands
- `radar/config.py` - Extend configuration for proxy/account settings
- `radar/engagement.py` - Update for multi-account batch operations

### Web UI Integration Files
- `Socializer-Admin/client/src/lib/api.ts` - Add proxy/account management API calls
- `Socializer-Admin/client/src/components/AccountManager.tsx` - Account CRUD with fingerprint viewer
- `Socializer-Admin/client/src/components/ProxyPool.tsx` - Proxy management and health dashboard  
- `Socializer-Admin/client/src/components/SessionMonitor.tsx` - Real-time session status
- `Socializer-Admin/client/src/components/FingerprintPreview.tsx` - Visual fingerprint display
- `Socializer-Admin/server/routes.ts` - Add proxy/account API routes
- `Socializer-Admin/shared/schema.ts` - Add proxies, fingerprints, sessions tables

### Database Schema Additions (schema.ts)
```typescript
// New tables to add to Socializer-Admin/shared/schema.ts

export const proxies = pgTable("proxies", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  host: text("host").notNull(),
  port: integer("port").notNull(),
  username: text("username"),
  password: text("password"),
  protocol: text("protocol", { enum: ["http", "https", "socks5"] }).default("http"),
  country: text("country"),
  provider: text("provider"),
  lastUsed: timestamp("last_used"),
  successRate: real("success_rate").default(1.0),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow(),
});

export const fingerprints = pgTable("fingerprints", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  accountId: varchar("account_id").references(() => accounts.id),
  userAgent: text("user_agent").notNull(),
  viewport: jsonb("viewport").$type<{ width: number; height: number }>(),
  timezone: text("timezone").notNull(),
  language: text("language").notNull(),
  platform: text("platform").notNull(),
  hardwareConcurrency: integer("hardware_concurrency"),
  deviceMemory: real("device_memory"),
  screenResolution: jsonb("screen_resolution").$type<{ width: number; height: number }>(),
  colorDepth: integer("color_depth"),
  pixelRatio: real("pixel_ratio"),
  webglVendor: text("webgl_vendor"),
  webglRenderer: text("webgl_renderer"),
  canvasHash: text("canvas_hash"),
  audioHash: text("audio_hash"),
  fonts: jsonb("fonts").$type<string[]>(),
  plugins: jsonb("plugins").$type<string[]>(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const sessions = pgTable("sessions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  accountId: varchar("account_id").references(() => accounts.id),
  proxyId: varchar("proxy_id").references(() => proxies.id),
  fingerprintId: varchar("fingerprint_id").references(() => fingerprints.id),
  cookies: jsonb("cookies").$type<any[]>(),
  localStorage: jsonb("local_storage").$type<Record<string, string>>(),
  isHealthy: boolean("is_healthy").default(true),
  lastHeartbeat: timestamp("last_heartbeat"),
  createdAt: timestamp("created_at").defaultNow(),
});
```

### Files for Configuration Updates
- `stack.yaml` - Add proxy and account configuration sections
- `pyproject.toml` - Add proxy-related dependencies
- `.env.example` - Add proxy provider API keys

## Functions

### New Functions
- `ProxyManager.__init__(config_path: str)` - Initialize proxy management
- `ProxyManager.get_proxy_for_account(account_id: str) -> ProxyConfig` - Get optimal proxy
- `ProxyManager.rotate_proxy(account_id: str) -> ProxyConfig` - Force proxy rotation
- `ProxyManager.validate_proxy(proxy: ProxyConfig) -> ProxyHealth` - Test proxy connectivity
- `AccountPool.load_accounts(platform: EngagementPlatform) -> List[AccountProfile]` - Load account profiles
- `AccountPool.get_available_account() -> AccountProfile` - Get next available account
- `SessionOrchestrator.create_session(account: AccountProfile) -> SessionContext` - Create browser session
- `SessionOrchestrator.restore_session(account_id: str) -> SessionContext` - Restore saved session
- `SessionPersistence.save_session(session: SessionContext)` - Persist session data
- `SessionPersistence.load_session(account_id: str) -> Dict` - Load session data

### Modified Functions
- `BrowserManager.launch_persistent_context()` - Add proxy parameter
- `TikTokAutomator.login()` - Accept proxy configuration
- `InstagramAutomator.login()` - Accept proxy configuration
- `EngagementManager.execute_batch()` - Support account-specific operations

## Classes

### New Classes
- `ProxyManager` - Core proxy management with health monitoring and rotation
- `AccountPool` - Multi-account management with load balancing
- `SessionOrchestrator` - Session lifecycle management across accounts
- `FingerprintGenerator` - Generates and applies persistent browser fingerprints
- `ProxyHealthMonitor` - Background proxy validation service
- `SessionPersistence` - Advanced session storage and recovery
- `BaseProxyProvider` - Abstract base for proxy provider integrations
- `BrightDataProvider` - BrightData proxy provider implementation
- `SmartProxyProvider` - SmartProxy provider implementation

### Modified Classes
- `BrowserManager` - Add proxy support and session isolation
- `TikTokAutomator` - Integrate session orchestrator
- `InstagramAutomator` - Integrate session orchestrator
- `EngagementManager` - Add account pool integration

## Dependencies

### New Packages
- `requests` - For proxy validation and provider APIs
- `cryptography` - For password encryption
- `apscheduler` - For background proxy health monitoring
- `redis` - Optional for distributed session storage
- `pymongo` - Optional for MongoDB session storage

### Version Updates
- `playwright>=1.43.0` - Already present, ensure latest
- `playwright-stealth>=2.0.0` - Already present

## Testing

### Test Structure
- `tests/test_proxy_manager.py` - Proxy rotation and health monitoring
- `tests/test_account_pool.py` - Multi-account management
- `tests/test_session_orchestrator.py` - Session lifecycle
- `tests/test_integration_proxy_session.py` - End-to-end proxy + session testing

### Test Coverage
- Proxy failover scenarios
- Session recovery from disk
- Account switching during batch operations
- Proxy health monitoring edge cases
- Cross-platform session compatibility

## Implementation Order

1. **Foundation Setup**
   - Create proxy data models and configuration
   - Implement FingerprintGenerator for persistent browser identities
   - Implement basic ProxyManager with local proxy lists
   - Add proxy support to BrowserManager

2. **Session Management Core**
   - Implement SessionPersistence for cookie/storage handling
   - Create SessionOrchestrator for session lifecycle with fingerprint application
   - Update existing automators to use session orchestrator

3. **Account Pool System**
   - Build AccountPool for multi-account management with persistent fingerprints
   - Implement account status tracking and rotation
   - Add account-specific configuration support

4. **Proxy Provider Integrations**
   - Create base proxy provider interface
   - Implement BrightData and SmartProxy providers
   - Add proxy health monitoring and rotation logic

5. **CLI and Configuration**
   - Extend CLI with proxy and account management commands
   - Update configuration system for proxy/account settings
   - Add environment variable support for provider APIs

6. **Integration and Testing**
   - Update engagement system for multi-account operations
   - Implement comprehensive testing suite
   - Add monitoring and logging for production use

7. **Web UI Integration (Socializer-Admin)**
   - Create account management dashboard component
   - Build proxy management interface with health status
   - Add session viewer showing active fingerprints per account
   - Implement account creation/import wizard with fingerprint preview
   - Create proxy pool configuration UI
   - Add real-time session health monitoring dashboard

8. **Advanced Features**
   - Implement proxy warming and session pre-loading
   - Add intelligent account-proxy matching
   - Add fingerprint analytics and uniqueness scoring