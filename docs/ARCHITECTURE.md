# Nyx-OSINT Architecture Overview

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Module Structure](#module-structure)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Extension Points](#extension-points)

---

## System Overview

Nyx-OSINT is built as a modular, asynchronous Python application designed for high-performance OSINT gathering. The architecture emphasizes:

- **Modularity**: Clear separation of concerns across modules
- **Asynchronicity**: Concurrent operations for performance
- **Extensibility**: Plugin system for custom platform checkers
- **Reliability**: Robust error handling and resource management
- **Scalability**: Efficient caching and rate limiting

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                    │
│  ┌──────────────┐              ┌──────────────┐            │
│  │     GUI      │              │     CLI      │            │
│  │ (CustomTk)   │              │   (Click)    │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Intelligence Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Email   │  │  Phone   │  │  Person   │  │  Smart   │ │
│  │  Intel   │  │  Intel   │  │  Intel   │  │  Search  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Deep Investigation Service                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      OSINT Layer                             │
│  ┌──────────────┐              ┌──────────────┐            │
│  │   Search     │              │   Profile    │            │
│  │   Service    │              │   Builder    │            │
│  └──────────────┘              └──────────────┘            │
│                                                              │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  Platform    │              │   Plugin     │            │
│  │  Checkers    │              │   Registry   │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Infrastructure                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   HTTP   │  │  Cache   │  │ Database │  │  Events  │ │
│  │  Client  │  │  System  │  │ Manager  │  │   Bus    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. HTTP Client (`core/http_client.py`)

**Purpose**: Centralized HTTP request handling with rate limiting and retries.

**Key Features**:
- Rate limiting via `RateLimiter`
- Exponential backoff retry logic
- Connection pooling via `httpx.AsyncClient`
- 429 (Too Many Requests) handling with `Retry-After` support
- Configurable timeouts and user agents

**Usage Pattern**:
```python
async with HTTPClient(rate_limit=10.0) as client:
    response = await client.get(url)
```

### 2. Cache System (`core/cache.py`)

**Purpose**: Multi-level caching for performance optimization.

**Architecture**:
- **L1 Cache**: In-memory (`MemoryCacheBackend`) - Fast, limited size
- **L2 Cache**: Disk-based (`DiskCacheBackend`) - Slower, persistent
- **MultiLevelCache**: Combines both with TTL support

**Cache Keys**: Platform-specific hashes based on username/email/phone

### 3. Database Manager (`core/database.py`)

**Purpose**: SQLAlchemy-based persistence layer.

**Models**:
- `Target`: Investigation subjects
- `TargetProfile`: Platform-specific profiles
- `SearchHistory`: Search execution records

**Features**:
- Connection pooling
- Health checks
- Session management

### 4. Event Bus (`core/events.py`)

**Purpose**: Pub/Sub system for inter-module communication.

**Event Types**:
- `platform_found`: Profile discovered
- `search_complete`: Search finished
- `error_occurred`: Error handling

**Usage**:
```python
event_bus = get_event_bus()
event_bus.subscribe("platform_found", handler)
event_bus.publish(Event("platform_found", data={...}))
```

---

## Module Structure

### Intelligence Modules (`intelligence/`)

#### Email Intelligence (`email.py`)
- Email validation
- Breach database checking
- Provider identification
- Profile discovery

#### Phone Intelligence (`phone.py`)
- Number parsing (via `phonenumbers`)
- Carrier lookup
- Location intelligence
- Line type detection

#### Person Intelligence (`person.py`)
- Name-based searches
- Public records (placeholder)
- Social media discovery
- Professional network search

#### Smart Search (`smart.py`)
- Free-form input processing
- Identifier extraction (usernames, emails, phones, names)
- Multi-module orchestration
- Confidence scoring
- Database persistence

#### Deep Investigation (`deep.py`)
- Centralized investigation orchestration
- Query type detection
- Multi-module coordination
- Result aggregation

### OSINT Modules (`osint/`)

#### Search Service (`search.py`)
- Platform filtering
- Concurrent search execution
- Caching integration
- Event publishing

#### Platform Checkers (`checker.py`)
- `BasePlatformChecker`: Abstract base class
- `StatusCodeChecker`: HTTP status-based detection
- `RegexChecker`: Pattern-based detection
- False positive detection

#### Profile Builder (`profile_builder.py`)
- Profile construction from search results
- Profile correlation
- Report generation

#### Plugin System (`plugin.py`)
- `PlatformCheckerPlugin`: Plugin interface
- `PluginRegistry`: Discovery and management

### Analysis Modules (`analysis/`)

#### Correlation Analyzer (`correlation.py`)
- Profile similarity calculation
- Shared attribute detection
- Pattern recognition

#### Relationship Graphs (`graphs.py`)
- Graph construction from profiles
- Cluster detection
- Centrality calculation
- Export (JSON, Graphviz)

#### Timeline Analysis (`timeline.py`)
- Temporal event tracking
- Pattern detection
- Export capabilities

### Export Modules (`export/`)

#### HTML Exporter (`html.py`)
- Template-based HTML generation
- Field redaction
- Custom templates

#### PDF Exporter (`pdf.py`)
- ReportLab-based PDF generation
- Styling and formatting
- Multi-page support

#### JSON Exporter (`json_export.py`)
- Structured data export
- Compression support
- Metadata inclusion

#### CSV Exporter (`csv_export.py`)
- Tabular data export
- Profile-specific export

### Filter Modules (`filters/`)

#### Advanced Filter (`advanced.py`)
- Complex filter rules
- Query parsing
- Filter chaining

#### Saved Searches (`saved_searches.py`)
- Search persistence
- Tag-based organization
- Query management

#### Batch Processor (`batch.py`)
- Concurrent batch processing
- Progress tracking
- Job management

---

## Data Flow

### Username Search Flow

```
1. User Input (CLI/GUI)
   │
   ▼
2. SearchService.search_username()
   │
   ├─► Filter platforms (category, NSFW, etc.)
   │
   ├─► Check cache
   │   └─► Cache hit: Return cached results
   │
   ├─► Create concurrent tasks for each platform
   │   │
   │   ├─► StatusCodeChecker.check()
   │   │   │
   │   │   ├─► HTTPClient.get(url)
   │   │   │   │
   │   │   │   ├─► RateLimiter.wait()
   │   │   │   │
   │   │   │   └─► httpx.AsyncClient.request()
   │   │   │
   │   │   └─► Validate response
   │   │
   │   └─► Publish "platform_found" event
   │
   ├─► Build profiles (ProfileBuilder)
   │
   ├─► Store in cache
   │
   └─► Return results
```

### Smart Search Flow

```
1. User Input (free-form text)
   │
   ▼
2. SmartSearchService.smart_search()
   │
   ├─► Extract identifiers
   │   ├─► Usernames (@username, username)
   │   ├─► Emails (email@domain.com)
   │   ├─► Phones (+1234567890)
   │   └─► Names (John Doe)
   │
   ├─► Parallel execution:
   │   │
   │   ├─► Username profiles (SearchService)
   │   ├─► Email intelligence (EmailIntelligence)
   │   ├─► Phone intelligence (PhoneIntelligence)
   │   ├─► Person intelligence (PersonIntelligence)
   │   └─► Web searches (MetaSearchEngine)
   │
   ├─► Build candidates
   │   ├─► Aggregate data
   │   ├─► Calculate confidence scores
   │   └─► Rank by confidence
   │
   ├─► Persist to database (optional)
   │
   └─► Return SmartSearchResult
```

---

## Design Patterns

### 1. Service Pattern

Services encapsulate business logic and coordinate between modules:

```python
class SearchService:
    def __init__(self, http_client: Optional[HTTPClient] = None):
        self.http_client = http_client or HTTPClient()
    
    async def search_username(self, username: str) -> Dict[str, Profile]:
        # Orchestrate search across platforms
        pass
```

### 2. Plugin Pattern

Extensible architecture for custom platform checkers:

```python
class PlatformCheckerPlugin(ABC):
    @abstractmethod
    async def check(self, username: str) -> Optional[Profile]:
        pass
```

### 3. Factory Pattern

Used for creating platform checkers:

```python
def create_checker(platform: Platform) -> BasePlatformChecker:
    if platform.check_type == "status_code":
        return StatusCodeChecker(platform)
    elif platform.check_type == "regex":
        return RegexChecker(platform)
```

### 4. Observer Pattern

Event bus for decoupled communication:

```python
event_bus.subscribe("platform_found", on_platform_found)
event_bus.publish(Event("platform_found", data=profile))
```

### 5. Strategy Pattern

Different checking strategies (status code vs regex):

```python
class BasePlatformChecker(ABC):
    @abstractmethod
    async def check(self, username: str) -> Optional[Profile]:
        pass
```

---

## Extension Points

### 1. Custom Platform Checkers

Create a plugin:

```python
from nyx.osint.plugin import PlatformCheckerPlugin

class MyCustomChecker(PlatformCheckerPlugin):
    async def check(self, username: str) -> Optional[Profile]:
        # Custom checking logic
        pass
    
    def get_platform_name(self) -> str:
        return "myplatform"
```

Register:

```python
from nyx.osint.plugin import PluginRegistry

registry = PluginRegistry()
registry.register(MyCustomChecker())
```

### 2. Custom Export Formats

Extend base exporter:

```python
from nyx.export.base import BaseExporter

class XMLExporter(BaseExporter):
    def export(self, data, output_path):
        # XML export logic
        pass
```

### 3. Custom Intelligence Modules

Create new intelligence service:

```python
class CustomIntelligence:
    async def investigate(self, query: str):
        # Custom investigation logic
        pass
```

---

## Configuration

Configuration is managed via YAML files (`config/settings.yaml`):

```yaml
http:
  max_concurrent_requests: 100
  timeout: 10
  retries: 3
  rate_limit: 10.0

cache:
  enabled: true
  ttl: 3600
  max_size: 1000
  backend: memory

database:
  url: sqlite:///nyx.db
  pool_size: 10
```

---

## Error Handling

### Exception Hierarchy

```
NyxException
├── ConfigurationError
├── SearchError
│   ├── PlatformError
│   └── ValidationError
├── DatabaseError
└── ExportError
```

### Error Handling Strategy

1. **Graceful Degradation**: Continue operation when optional features fail
2. **Retry Logic**: Automatic retries with exponential backoff
3. **Logging**: Comprehensive error logging with context
4. **User Feedback**: Clear error messages in CLI/GUI

---

## Performance Considerations

### Concurrency

- Uses `asyncio` for concurrent platform checks
- Configurable concurrency limits
- Rate limiting to prevent overwhelming targets

### Caching

- Multi-level caching reduces redundant requests
- TTL-based expiration
- Cache invalidation on updates

### Resource Management

- Explicit resource cleanup (`aclose()` methods)
- Context managers for HTTP clients
- Connection pooling

---

## Security Considerations

### Input Validation

- Sanitization of user inputs
- Type checking at boundaries
- Path traversal prevention

### Privacy

- Field redaction in exports
- Configurable data retention
- Encryption support for sensitive data

### Rate Limiting

- Prevents abuse of target platforms
- Respects `Retry-After` headers
- Configurable limits

---

**Version:** 0.1.0  
**Last Updated:** 2025-01-23

